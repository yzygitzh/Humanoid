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

    log_data_dir = config_json["log_data_dir"]
    embedding_dir = config_json["embedding_dir"]
    model_name = config_json["embedding_model"]
    model_path = os.path.join(log_data_dir, model_name)
    log_step = 327543 // config_json["batch_size"]

    model = MultipleScreenModel(config_json)

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger("embedding")
    logger.setLevel(logging.INFO)

    saver = tf.train.Saver(max_to_keep=None)
    data_loader = loader.MultipleScreenLoader(config_json, load_text=True)

    text_heatmaps = []
    texts = []

    with tf.Session(config=tf_config) as sess:
        saver.restore(sess, model_path)
        loss_sum = 0
        for i in range(log_step):
            data_batch = data_loader.next_batch()
            input_texts = data_batch[-1]
            feed_dict = model.get_feed_dict(*data_batch[:-1])
            heatmaps = sess.run(model.pool5_heat_out, feed_dict=feed_dict)
            for j, text in enumerate(input_texts):
                if text is not None:
                    text_heatmaps.append(heatmaps[j, :, :, 0].flatten().tolist())
                    texts.append(text)
    data_loader.stop()

    with open(os.path.join(embedding_dir, "%s.embedding" % model_name), "w") as f:
        json.dump({
            "vectors": text_heatmaps,
            "texts": texts
        }, f, ensure_ascii=False)

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
