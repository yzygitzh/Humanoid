#coding=utf-8

import argparse
import json
import os

import numpy as np
import tensorflow as tf

from loader import DebugLoader

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    loader = DebugLoader(config_json)

    with tf.Session() as sess:
        images, heatmaps, labels = loader.next_batch()

        print(np.sum(sess.run(images)))
        print(np.sum(sess.run(heatmaps)))
        print(np.sum(sess.run(labels)))


def parse_args():
    parser = argparse.ArgumentParser(description="Humanoid training script")
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
