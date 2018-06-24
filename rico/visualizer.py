#coding=utf-8

import argparse
import json
import pickle
import os

from utils import visualize_data

def run(input_path, config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    with open(input_path, "rb") as f:
        input_data = pickle.load(f)

    for trace_num in input_data:
        trace_data = input_data[trace_num]
        for i, (image_data, interact_data) in enumerate(trace_data):
            visualize_data(image_data, label=json.dumps(interact_data))

def parse_args():
    parser = argparse.ArgumentParser(description="Visualize Humanoid training data")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    parser.add_argument("-i", action="store", dest="input_path",
                        required=True, help="path/to/some_data.pickle")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.input_path, opts.config_path)
    return

if __name__ == "__main__":
    main()
