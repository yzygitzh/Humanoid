#coding=utf-8

import json
import numpy as np

from matplotlib import pyplot as plt
from utils import traverse_view_tree

def convert_view_trees(view_tree_paths, config_json):
    origin_dim = config_json["origin_dim"]
    downscale_dim = config_json["downscale_dim"]
    downscale_ratio = downscale_dim[0] / origin_dim[0]
    text_dim = config_json["text_dim"]
    image_dim = config_json["image_dim"]
    total_dims = config_json["total_dims"]
    boundary_width = config_json["boundary_width"]

    # image num, x, y, channels (TEXT/IMAGE)
    image_array = []

    for view_tree_path in view_tree_paths:
        image_data = np.zeros((downscale_dim[0], downscale_dim[1], total_dims), dtype=float)
        image_array.append(image_data)

        with open(view_tree_path, "r") as view_tree_file:
            view_tree = json.load(view_tree_file)

        if view_tree is None:
            continue

        view_root_bounds = view_tree["activity"]["root"]["bounds"]
        # skip full-screen horizon ones
        if view_root_bounds[2] > view_root_bounds[3] and view_root_bounds[2] > origin_dim[0]:
            continue

        view_offset = [0, 0]
        # heuristically identify non-full-screen window
        if view_root_bounds[2] - view_root_bounds[0] < origin_dim[0] and \
           view_root_bounds[3] - view_root_bounds[1] < origin_dim[1]:
            view_center = [(view_root_bounds[0] + view_root_bounds[2]) / 2,
                        (view_root_bounds[1] + view_root_bounds[3]) / 2]
            view_offset = [int((origin_dim[0] / 2 - view_center[0]) * downscale_ratio),
                           int((origin_dim[1] / 2 - view_center[1]) * downscale_ratio)]

        def view_call_back(view_tree):
            if "children" not in view_tree:
                bounds = view_tree["bounds"]

                x_min = max(0, int(bounds[0] * downscale_ratio)) + view_offset[0]
                y_min = max(0, int(bounds[1] * downscale_ratio)) + view_offset[1]
                x_max = min(downscale_dim[0], int(bounds[2] * downscale_ratio)) + view_offset[0]
                y_max = min(downscale_dim[1], int(bounds[3] * downscale_ratio)) + view_offset[1]

                draw_dim = text_dim if "text" in view_tree else image_dim
                image_data[x_min:x_max, y_min:y_max, draw_dim] = 1.0
                # draw four boundaries
                b_x_min = max(0, x_min - 1)
                b_y_min = max(0, y_min - 1)
                b_x_max = min(downscale_dim[0], x_max + 1)
                b_y_max = min(downscale_dim[1], y_max + 1)
                image_data[b_x_min:b_x_min+boundary_width, b_y_min:b_y_max, draw_dim] = 0.0
                image_data[b_x_max-boundary_width:b_x_max, b_y_min:b_y_max, draw_dim] = 0.0
                image_data[b_x_min:b_x_max, b_y_min:b_y_min+boundary_width, draw_dim] = 0.0
                image_data[b_x_min:b_x_max, b_y_max-boundary_width:b_y_max, draw_dim] = 0.0

        traverse_view_tree(view_tree["activity"]["root"], view_call_back)
        # if "/262.json" in view_tree_path:
        # if True:
        #     print(view_tree_path)
        #     visualize_view_tree(image_data, config_json)

    return image_array

def visualize_view_tree(image_data, config_json):
    downscale_dim = config_json["downscale_dim"]
    text_dim = config_json["text_dim"]
    image_dim = config_json["image_dim"]

    image_full = np.zeros([downscale_dim[1], downscale_dim[0], 3], dtype=float)
    print(image_full.shape)

    image_full[:, :, text_dim] = image_data[:, :, text_dim].T
    image_full[:, :, image_dim] = image_data[:, :, image_dim].T

    plt.imshow(image_full, interpolation='nearest' )
    plt.show()
