#coding=utf-8

import argparse
import json
import os

import numpy as np

import image
import touch_input

from utils import visualize_data

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
    heatmap_array, gesture_array = touch_input.convert_gestures(gestures, config_json)

    # find text differences pairs and insert text inputs
    # (heuristically insert them at the end of the pair)

    # visualize for debugging
    for image_data, heatmap_data, gesture_data in \
        zip(image_array, heatmap_array, gesture_array):
        print("Gesture: ", gesture_data)
        visualize_data(image_data + heatmap_data, config_json)


def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    filtered_traces_dir = config_json["filtered_traces_path"]

    apps = next(os.walk(filtered_traces_dir))[1]
    for app in apps:
        if app != "com.hotVideos.BigoLive":
            continue
        app_dir = os.path.join(filtered_traces_dir, app)
        app_trace_dirs = [os.path.join(app_dir, x)
                          for x in next(os.walk(app_dir))[1]]
        for app_trace_dir in app_trace_dirs:
            process_trace(app_trace_dir, config_json)
            break

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
