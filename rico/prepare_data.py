#coding=utf-8

import argparse
import pickle
import json
import os

import numpy as np

import image
import touch_input
import text_input

from utils import visualize_data, is_valid_data

def process_trace(trace_path, config_json):
    gestures_path = os.path.join(trace_path, "gestures.json")
    view_trees_dir = os.path.join(trace_path, "view_hierarchies")

    with open(gestures_path, "r") as gestures_file:
        gestures = json.load(gestures_file)

    view_tree_tags = sorted([int(x[:-len(".json")])
                             for x in next(os.walk(view_trees_dir))[2]])

    with open(gestures_path, "r") as gestures_file:
        gestures = json.load(gestures_file)
        gestures = [gestures[x] for x in sorted(gestures, key=lambda x: int(x))]
    assert(len(gestures) == len(view_tree_tags))

    # convert view tree to color rects
    view_tree_paths = [os.path.join(view_trees_dir, "%d.json" % x) for x in view_tree_tags]
    image_array = image.convert_view_trees(view_tree_paths, config_json)

    # find tap inputs
    heatmap_array, interact_array = touch_input.convert_gestures(gestures, config_json)

    # find text differences pairs and insert text inputs
    # (heuristically insert them at the end of the pair)
    view_tree_paths, image_array, heatmap_array, interact_array = \
    text_input.add_text_inputs(view_tree_paths, image_array,
                               heatmap_array, interact_array, config_json)
    assert(len(view_tree_paths) == len(image_array) == len(heatmap_array) == len(interact_array))
    # filter empty states
    filtered_data = []
    for i, (image_data, heatmap_data, interact_data) in \
        enumerate(zip(image_array, heatmap_array, interact_array)):
        sum_image_data = image_data + heatmap_data
        if is_valid_data(sum_image_data, interact_data, config_json):
            # print("Interact:", interact_data)
            # print("Path:", view_tree_paths[i])
            # visualize_data(sum_image_data, config_json)
            filtered_data.append([sum_image_data, interact_data])

    return filtered_data

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    filtered_traces_dir = config_json["filtered_traces_path"]
    output_dir = config_json["output_dir"]

    apps = next(os.walk(filtered_traces_dir))[1]
    for app in apps:
        # if app != "org.telegram.messenger":
        # if app != "com.whatsapp":
        # if app != "com.surveysampling.mobile.quickthoughts":
        #     continue
        print(app)
        app_dir = os.path.join(filtered_traces_dir, app)
        app_trace_dirs = [os.path.join(app_dir, x)
                          for x in next(os.walk(app_dir))[1]]
        processed_traces = {}
        for app_trace_dir in app_trace_dirs:
            processed_trace = process_trace(app_trace_dir, config_json)
            trace_num = os.path.basename(app_trace_dir)
            processed_traces[trace_num] = processed_trace

        save_file_name = "%s.pickle" % app
        with open(os.path.join(output_dir, save_file_name), "wb") as f:
            pickle.dump(processed_traces, f)
        # print(sorted(processed_traces))
        # break

def parse_args():
    parser = argparse.ArgumentParser(description="Prepare RICO dataset for Humanoid")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.config_path)
    return

if __name__ == "__main__":
    main()
