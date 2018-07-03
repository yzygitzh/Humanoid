#coding=utf-8

import json
import pickle
import socket
from xmlrpc.server import SimpleXMLRPCServer

import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt

import flask

import rico
from train.model import MultipleScreenModel
from train.utils import visualize_data

class HumanoidAgent():
    def __init__(self, domain):
        self.domain = domain
        self.rpc_port = self.get_random_port()
        print("Serving at %s:%d" % (self.domain, self.rpc_port))
        self.server = SimpleXMLRPCServer((self.domain, self.rpc_port))
        self.server.register_function(self.query, "query")

    def get_random_port(self):
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.bind(("", 0))
        port = temp_sock.getsockname()[1]
        temp_sock.close()
        return port

    def query(self, query_json):
        print(json.loads(query_json))
        return query_json

    def run(self):
        self.server.serve_forever()

class HumanoidTest():
    def __init__(self):
        pass

    def test_model(self):
        with open("config.json", "r") as f:
            config_json = json.load(f)
        frame_num = config_json["frame_num"]
        predicting_dim = config_json["predicting_dim"]
        total_interacts = config_json["total_interacts"]
        model = MultipleScreenModel(config_json, training=False)

        data_path = "/mnt/DATA_volume/lab_data/RICO/training_data/jp.naver.linecard.android.pickle"
        with open(data_path, "rb") as f:
            input_data = pickle.load(f)
        image_num = len(input_data["trace_0"])
        stacked_images = np.stack([np.zeros_like(input_data["trace_0"][0][0], dtype=np.float32)] * (frame_num - 1) + \
                                [x[0] for x in input_data["trace_0"]], axis=0)
        images = [stacked_images[i:i + frame_num].copy() for i in range(image_num)]
        # clear last heatmaps
        for image in images:
            image[frame_num - 1, :, :, -predicting_dim:] = 0.0
            image -= 0.5

        heatmaps = np.stack([x[0][:,:,-predicting_dim:]
                            for x in input_data["trace_0"]], axis=0)
        interacts = np.eye(total_interacts)[[x[1]["interact_type"] for x in input_data["trace_0"]]]

        saver = tf.train.Saver()
        with tf.Session() as sess:
            saver.restore(sess, "/mnt/DATA_volume/lab_data/RICO/training_log/model_11500.ckpt")
            for i in range(image_num):
                heatmap = sess.run(model.predict_heatmaps, feed_dict=model.get_feed_dict(images[i], heatmaps[i:i+1], interacts[i:i+1]))
                interact = sess.run(model.predict_interacts, feed_dict=model.get_feed_dict(images[i], heatmaps[i:i+1], interacts[i:i+1]))
                visualize_data(images[i][frame_num - 1] + 0.5)
                visualize_data(heatmap[0])
                print(interact[0])

if __name__ == "__main__":
    # tester = HumanoidTest()
    # tester.test_model()
    agent = HumanoidAgent("localhost")
    agent.run()
