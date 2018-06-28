#coding=utf-8

import json
import numpy as np

from matplotlib import pyplot as plt
from scipy.stats import multivariate_normal

import touch_input
from utils import traverse_view_tree, get_text_view_signature, is_text_view, \
                  is_view_hierarchy_valid, compute_view_offset

def add_text_inputs(view_tree_paths, image_array,
                    heatmap_array, interact_array, config_json):
    total_dims = config_json["total_dims"]
    downscale_dim = config_json["downscale_dim"]
    origin_dim = config_json["origin_dim"]
    downscale_ratio = downscale_dim[0] / origin_dim[0]
    interact_dim = config_json["interact_dim"]
    interact_input_text = config_json["interact_input_text"]

    assert(len(view_tree_paths) == len(image_array) == len(heatmap_array) == len(interact_array))

    text_history = {} # activity + view_id -> [(idx, text_content), ...]

    for i, view_tree_path in enumerate(view_tree_paths):
        with open(view_tree_path, "r") as view_tree_file:
            view_tree = json.load(view_tree_file)

        if view_tree is None:
            continue
        if not is_view_hierarchy_valid(view_tree, config_json):
            continue
        activity_name = view_tree["activity_name"]
        if activity_name is None:
            continue

        view_offset = compute_view_offset(view_tree, config_json)

        def view_call_back(view_tree):
            if is_text_view(view_tree):
                bounds = view_tree["bounds"]

                x_min = max(0, int(bounds[0] * downscale_ratio) + view_offset[0])
                y_min = max(0, int(bounds[1] * downscale_ratio) + view_offset[1])
                x_max = min(downscale_dim[0], int(bounds[2] * downscale_ratio) + view_offset[0])
                y_max = min(downscale_dim[1], int(bounds[3] * downscale_ratio) + view_offset[1])

                if x_min > x_max or y_min > y_max:
                    return

                text_view_id = activity_name + ":" + get_text_view_signature(view_tree)
                if text_view_id not in text_history:
                    text_history[text_view_id] = {
                        "pos": [min(int((x_min + x_max) / 2), downscale_dim[0] - 1),
                                min(int((y_min + y_max) / 2), downscale_dim[1] - 1)],
                        "texts": []
                    }
                text_history[text_view_id]["texts"].append([i, view_tree["text"]])

        traverse_view_tree(view_tree["activity"]["root"], view_call_back)

    # identify text changes
    text_changes = {}
    for text_view_id in text_history:
        pos = text_history[text_view_id]["pos"]
        texts = [[0, ""]] + text_history[text_view_id]["texts"]
        for i in range(len(texts) - 1):
            if texts[i][1] != texts[i + 1][1]:
                if texts[i + 1][0] not in text_changes:
                    text_changes[texts[i + 1][0]] = []
                text_changes[texts[i + 1][0]].append({"pos": pos, "text": texts[i + 1][1]})

    new_view_tree_paths = []
    new_image_array = []
    new_heatmap_array = []
    new_interact_array = []

    text_change_indices = sorted(text_changes)
    last_idx = 0
    for idx in text_change_indices:
        new_view_tree_paths += view_tree_paths[last_idx:idx]
        new_image_array += image_array[last_idx:idx]
        new_heatmap_array += heatmap_array[last_idx:idx]
        new_interact_array += interact_array[last_idx:idx]

        # from left to right, up to down
        sorted_inputs = sorted(text_changes[idx], key=lambda x: x["pos"])
        for text_input in sorted_inputs:
            new_view_tree_paths.append(view_tree_paths[idx])
            new_image_array.append(np.copy(image_array[idx]))
            new_interact_array.append({
                "interact_type": interact_input_text,
                "text": text_input["text"]
            })
            text_heatmap = np.zeros((downscale_dim[0], downscale_dim[1], total_dims), dtype=np.float32)
            new_heatmap_array.append(text_heatmap)
            for x in range(downscale_dim[0]):
                for y in range(downscale_dim[1]):
                    sample_x = abs(x - text_input["pos"][0])
                    sample_y = abs(y - text_input["pos"][1])
                    text_heatmap[x, y, interact_dim] = touch_input.GAUSS_MAP[sample_x, sample_y]
        last_idx = idx

    new_view_tree_paths += view_tree_paths[last_idx:]
    new_image_array += image_array[last_idx:]
    new_heatmap_array += heatmap_array[last_idx:]
    new_interact_array += interact_array[last_idx:]

    return new_view_tree_paths, new_image_array, new_heatmap_array, new_interact_array
