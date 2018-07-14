#coding=utf-8

import argparse
import gc
import json
import logging
logging.basicConfig(format="%(asctime)-15s %(message)s")
import os
import shutil

import numpy as np
import tensorflow as tf

import loader
from model import SingleScreenModel, MultipleScreenModel
from utils import visualize_data

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    config_json["training_data_dir"] = config_json["validation_data_dir"]
    log_data_dir = config_json["log_data_dir"]
    models = sorted([x.split(".meta")[0]
                     for x in next(os.walk(log_data_dir))[2]
                     if x.endswith(".ckpt.meta")],
                    key=lambda x: int(x.split(".")[0].split("_")[1]))
    model_paths = [os.path.join(log_data_dir, x) for x in models]

    # 2500 ~ 1% of the whole data size
    log_step = 2500 // config_json["batch_size"]

    model = MultipleScreenModel(config_json)

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger("valid")
    logger.setLevel(logging.INFO)

    saver = tf.train.Saver(max_to_keep=None)
    data_loader = loader.MultipleScreenLoader(config_json)

    with tf.Session(config=tf_config) as sess:
        for model_path in model_paths:
            saver.restore(sess, model_path)
            loss_sum = 0
            for i in range(log_step):
                feed_dict = model.get_feed_dict(*data_loader.next_batch())
                loss_sum += sess.run(model.total_loss, feed_dict=feed_dict)
            logger.info("model %s loss: %g" % (model_path, loss_sum / log_step))
    data_loader.stop()

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
