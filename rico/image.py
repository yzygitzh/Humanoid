#coding=utf-8

import json
import numpy as np

from matplotlib import pyplot as plt
from .utils import traverse_view_tree, is_view_hierarchy_valid, compute_view_offset

def convert_view_tree_file(view_tree_path, config_json):
    with open(view_tree_path, "r") as view_tree_file:
        view_tree = json.load(view_tree_file)
    return convert_view_tree(view_tree, config_json)

def convert_semantic_view_tree_file(view_tree_path, config_json):
    with open(view_tree_path, "r") as view_tree_file:
        view_tree = json.load(view_tree_file)
    return convert_semantic_view_tree(view_tree, config_json)

def convert_semantic_view_tree(view_tree, config_json):
    origin_dim = config_json["origin_dim"]
    downscale_dim = config_json["downscale_dim"]

    label_num = len(config_json["semantic_labels"])
    label_to_id = {}
    for i in range(label_num):
        label_to_id[config_json["semantic_labels"][i]] = i

    boxes = []
    if view_tree is None:
        return None
    if not is_view_hierarchy_valid(view_tree, config_json, semantic_ui=True):
        return None

    view_offset = compute_view_offset(view_tree, config_json, semantic_ui=True)
    # print(view_offset)

    def view_call_back(view_tree):
        if "componentLabel" in view_tree:
            bounds = view_tree["bounds"]
            if bounds[0] < 0 or bounds[1] < 0 or \
               bounds[2] > origin_dim[0] or bounds[3] > origin_dim[1] or \
               bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                return
            x_center = (bounds[0] + bounds[2]) / origin_dim[0] / 2 + view_offset[0] / downscale_dim[0]
            y_center = (bounds[1] + bounds[3]) / origin_dim[1] / 2 + view_offset[1] / downscale_dim[1]
            width = (bounds[2] - bounds[0]) / origin_dim[0]
            height = (bounds[3] - bounds[1]) / origin_dim[1]
            boxes.append([label_to_id[view_tree["componentLabel"]],
                          x_center, y_center, width, height])

    traverse_view_tree(view_tree, view_call_back, semantic_ui=True)
    return boxes

def convert_view_tree(view_tree, config_json):
    origin_dim = config_json["origin_dim"]
    downscale_dim = config_json["downscale_dim"]
    downscale_ratio = downscale_dim[0] / origin_dim[0]
    text_dim = config_json["text_dim"]
    image_dim = config_json["image_dim"]
    total_dims = config_json["total_dims"]
    bw = config_json["boundary_width"]

    image_data = np.zeros((downscale_dim[0], downscale_dim[1], total_dims), dtype=np.float32)

    if view_tree is None:
        return image_data
    if not is_view_hierarchy_valid(view_tree, config_json):
        return image_data

    view_offset = compute_view_offset(view_tree, config_json)

    def view_call_back(view_tree):
        if "children" not in view_tree or not len(view_tree["children"]):
            bounds = view_tree["bounds"]
            x_min = int(bounds[0] * downscale_ratio) + view_offset[0]
            y_min = int(bounds[1] * downscale_ratio) + view_offset[1]
            x_max = int(bounds[2] * downscale_ratio) + view_offset[0]
            y_max = int(bounds[3] * downscale_ratio) + view_offset[1]
            if x_min >= x_max or y_min >= y_max:
                return
            draw_dim = text_dim if ("text" in view_tree and view_tree["text"] is not None) \
                                else image_dim
            image_data[x_min:x_max, y_min:y_max, draw_dim] = 1.0
            # draw four boundaries
            image_data[x_min - bw:x_min, y_min - bw:y_max + bw, draw_dim] = 0.0
            image_data[x_max:x_max + bw, y_min - bw:y_max + bw, draw_dim] = 0.0
            image_data[x_min - bw:x_max + bw, y_min - bw:y_min, draw_dim] = 0.0
            image_data[x_min - bw:x_max + bw, y_max:y_max + bw, draw_dim] = 0.0

    traverse_view_tree(view_tree["activity"]["root"], view_call_back)
    # if "/262.json" in view_tree_path:
    # if True:
    #     print(view_tree_path)
    #     visualize_view_tree(image_data, config_json)

    return image_data

def visualize_view_tree(image_data, config_json):
    downscale_dim = config_json["downscale_dim"]
    text_dim = config_json["text_dim"]
    image_dim = config_json["image_dim"]

    image_full = np.zeros([downscale_dim[1], downscale_dim[0], 3], dtype=np.float32)
    print(image_full.shape)

    image_full[:, :, text_dim] = image_data[:, :, text_dim].T
    image_full[:, :, image_dim] = image_data[:, :, image_dim].T

    plt.imshow(image_full, interpolation='nearest' )
    plt.show()
