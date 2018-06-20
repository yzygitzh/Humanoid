#coding=utf-8

import argparse
import json
import os

import matplotlib.pyplot as plt
import numpy as np

import image
import touch_input

from utils import visualize_data

def collect_gesture_periods(trace_path, config_json):
    gestures_path = os.path.join(trace_path, "gestures.json")
    with open(gestures_path, "r") as gestures_file:
        gestures = json.load(gestures_file)
    return [len(gestures[x]) for x in gestures]

def collect_gesture_sizes(trace_path, config_json):
    gestures_path = os.path.join(trace_path, "gestures.json")
    downscale_dim = config_json["downscale_dim"]

    with open(gestures_path, "r") as gestures_file:
        gestures = json.load(gestures_file)
    size_list = []
    for gesture in gestures.values():
        if len(gesture) == 1:
            size_list.append(0)
        elif len(gesture) >= 2:
            size_list.append(int(np.sqrt(((gesture[0][0] - gesture[-1][0]) * downscale_dim[0]) ** 2 + \
                                         ((gesture[0][1] - gesture[-1][1]) * downscale_dim[1]) ** 2)))
    return size_list

def plot_xy(xy_array, xlabel, xlim_up):
    x = [x[0] for x in xy_array]
    y = [y[1] for y in xy_array]

    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.xlim(0, xlim_up)
    # plt.ylim(0, 1.0)
    # plt.margins(0.01, 0.01)
    # plt.tight_layout()
    plt.show()

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    filtered_traces_dir = config_json["filtered_traces_path"]
    gesture_period_distribution = {}
    gesture_size_distribution = {}

    apps = next(os.walk(filtered_traces_dir))[1]
    for app in apps:
        print(app)
        app_dir = os.path.join(filtered_traces_dir, app)
        app_trace_dirs = [os.path.join(app_dir, x)
                          for x in next(os.walk(app_dir))[1]]
        for app_trace_dir in app_trace_dirs:
            gesture_periods = collect_gesture_periods(app_trace_dir, config_json)
            for gesture_period in gesture_periods:
                if gesture_period not in gesture_period_distribution:
                    gesture_period_distribution[gesture_period] = 0
                gesture_period_distribution[gesture_period] += 1

            gesture_sizes = collect_gesture_sizes(app_trace_dir, config_json)
            for gesture_size in gesture_sizes:
                if gesture_size not in gesture_size_distribution:
                    gesture_size_distribution[gesture_size] = 0
                gesture_size_distribution[gesture_size] += 1

    gesture_period_distribution.pop(0)
    gesture_period_distribution.pop(1)
    plot_xy(sorted(gesture_period_distribution.items()), "Gesture Length Distribution", 50)
    gesture_size_distribution.pop(0)
    plot_xy(sorted(gesture_size_distribution.items()), "Gesture Size Distribution", 400)

def parse_args():
    parser = argparse.ArgumentParser(description="Profile touch distribution")
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
