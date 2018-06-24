#coding=utf-8

import argparse
import json
import logging
import os

import numpy as np
import tensorflow as tf

from loader import DebugLoader
from model import SingleScreenModel
from utils import visualize_data

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    loader = DebugLoader(config_json)
    model = SingleScreenModel(config_json)

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger()
    logging.basicConfig(format="%(asctime)-15s %(message)s")
    logger = logging.getLogger("train")
    logger.setLevel(logging.INFO)

    with tf.Session(config=tf_config) as sess:
        optimizer = tf.train.GradientDescentOptimizer(5e-2)
        trainer = optimizer.minimize(model.total_loss)
        feed_dict = model.get_feed_dict(*loader.next_batch())

        sess.run(tf.global_variables_initializer())
        for i in range(10000):
            sess.run(trainer, feed_dict=feed_dict)

            if i % 100 == 0:
                logger.info("heatmap loss: %g" % sess.run(model.heatmap_loss, feed_dict=feed_dict))
                logger.info("interact loss: %g" % sess.run(model.interact_loss, feed_dict=feed_dict))
                logger.info("total loss: %g" % sess.run(model.total_loss, feed_dict=feed_dict))

                predict_heatmaps = sess.run(model.predict_heatmaps, feed_dict=feed_dict)
                predict_interacts = sess.run(model.predict_interacts, feed_dict=feed_dict)
                print("Interacts:", predict_interacts)
                for i in range(predict_heatmaps.shape[0]):
                    curr_heatmap = predict_heatmaps[i]
                    visualize_image = np.zeros([curr_heatmap.shape[0], curr_heatmap.shape[1], 3])
                    visualize_image[:, :, 0] = curr_heatmap[:, :, 0]
                    visualize_data(visualize_image)

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
