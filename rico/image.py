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
    boundary_width = config_json["boundary_width"]

    # image num, x, y, channels (TEXT/IMAGE)
    image_array = np.zeros((len(view_tree_paths), downscale_dim[0], downscale_dim[1], 2), dtype=float)

    for i, view_tree_path in enumerate(view_tree_paths):
        with open(view_tree_path, "r") as view_tree_file:
            view_tree = json.load(view_tree_file)

        if view_tree is None:
            continue

        view_root_bounds = view_tree["activity"]["root"]["bounds"]
        # skip horizon ones
        if view_root_bounds[2] > view_root_bounds[3]:
            continue

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
                image_array[i, x_min:x_max, y_min:y_max, draw_dim] = 1.0
                # draw four boundaries
                image_array[i, x_min:x_min+boundary_width, y_min:y_max, draw_dim] = 0.0
                image_array[i, x_max-boundary_width:x_max, y_min:y_max, draw_dim] = 0.0
                image_array[i, x_min:x_max, y_min:y_min+boundary_width, draw_dim] = 0.0
                image_array[i, x_min:x_max, y_max-boundary_width:y_max, draw_dim] = 0.0

        traverse_view_tree(view_tree["activity"]["root"], view_call_back)
        # if "/262.json" in view_tree_path:
        if True:
            print(view_tree_path)
            visualize_view_tree(image_array[i], config_json)

    return image_array

def visualize_view_tree(image_array, config_json):
    downscale_dim = config_json["downscale_dim"]
    image_full = np.zeros([downscale_dim[1], downscale_dim[0], 3], dtype=float)
    print(image_full.shape)
    for i in range(image_array.shape[2]):
        image_full[:, :, i] = image_array[:, :, i].T
    plt.imshow(image_full, interpolation='nearest' )
    plt.show()
