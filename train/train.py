#coding=utf-8

import argparse
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
    shutil.rmtree(log_data_dir)
    os.makedirs(log_data_dir)

    learning_rate = config_json["learning_rate"]
    max_iter = config_json["max_iter"]
    log_step = config_json["log_step"]
    snapshot_step = config_json["snapshot_step"]

    # data_loader = loader.DebugSingleScreenLoader(config_json)
    # model = SingleScreenModel(config_json)
    # data_loader = loader.DebugMultipleScreenLoader(config_json)
    data_loader = loader.MultipleScreenLoader(config_json)
    model = MultipleScreenModel(config_json)
    merged_summary = tf.summary.merge_all()

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger("train")
    logger.setLevel(logging.INFO)

    saver = tf.train.Saver(max_to_keep=None)

    with tf.Session(config=tf_config) as sess:
        train_writer = tf.summary.FileWriter(log_data_dir, sess.graph)

        # fast_optimizer = tf.train.GradientDescentOptimizer(learning_rate)
        # fast_optimizer = tf.train.GradientDescentOptimizer(learning_rate * 1000)
        # mid_optimizer = tf.train.MomentumOptimizer(learning_rate, 0.9)
        final_optimizer = tf.train.MomentumOptimizer(learning_rate, 0.9)

        # fast_trainer = fast_optimizer.minimize(model.total_loss)
        # mid_trainer = mid_optimizer.minimize(model.total_loss)
        final_trainer = final_optimizer.minimize(model.total_loss)

        sess.run(tf.global_variables_initializer())
        for i in range(max_iter):
            feed_dict = model.get_feed_dict(*data_loader.next_batch())
            # if data_loader.get_current_epoch() < 40:
            # if i < 3000:
            #     sess.run(fast_trainer, feed_dict=feed_dict)
            # elif data_loader.get_current_epoch() < 100:
            # if i < 10000:
            #     sess.run(mid_trainer, feed_dict=feed_dict)
            # else:
            sess.run(final_trainer, feed_dict=feed_dict)

            if i % snapshot_step == 0:
                saved_path = saver.save(sess, os.path.join(log_data_dir, "model_%d.ckpt" % i))
                logger.info("model saved in path: %s" % saved_path)

            if i % log_step == 0:
                summary = sess.run(merged_summary, feed_dict=feed_dict)
                train_writer.add_summary(summary, i)
                train_writer.flush()

                """
                gr = tf.get_default_graph()
                conv1_kernel_val = gr.get_tensor_by_name("conv1/kernel:0").eval()
                print(conv1_kernel_val[:, :, :, 0])
                conv1_bias_val = gr.get_tensor_by_name("conv1/bias:0").eval()
                print(conv1_bias_val)

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
                """
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
