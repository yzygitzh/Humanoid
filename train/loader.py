#coding=utf-8

import os
import pickle

import numpy as np
import tensorflow as tf

from utils import visualize_data

class Loader():
    """Basic data loader
    """
    def __init__(self, config_json):
        self.x_dim, self.y_dim = config_json["downscale_dim"]
        self.training_dim = config_json["training_dim"]
        self.predicting_dim = config_json["predicting_dim"]
        self.total_interacts = config_json["total_interacts"]
        self.training_data_dir = config_json["training_data_dir"]

    def next_batch(self):
        pass

class DebugSingleScreenLoader(Loader):
    def __init__(self, config_json):
        super().__init__(config_json)
        self.data_file = "jp.naver.linecard.android.pickle"
        self.data_path = os.path.join(self.training_data_dir, self.data_file)

    def next_batch(self):
        with open(self.data_path, "rb") as f:
            input_data = pickle.load(f)
        images = np.stack([x[0][:,:,:self.training_dim]
                           for x in input_data["trace_0"]], axis=0)
        heatmaps = np.stack([x[0][:,:,-self.predicting_dim:]
                             for x in input_data["trace_0"]], axis=0)
        interacts = np.eye(self.total_interacts)[[x[1]["interact_type"] for x in input_data["trace_0"]]]
        return images, heatmaps, interacts

class DebugMultipleScreenLoader(Loader):
    def __init__(self, config_json):
        super().__init__(config_json)
        self.data_file = "jp.naver.linecard.android.pickle"
        self.data_path = os.path.join(self.training_data_dir, self.data_file)
        self.frame_num = config_json["frame_num"]

    def next_batch(self):
        with open(self.data_path, "rb") as f:
            input_data = pickle.load(f)
        # assemble frames
        # do zero padding before the first image
        image_num = len(input_data["trace_0"])
        stacked_images = np.stack([np.zeros_like(input_data["trace_0"][0][0], dtype=np.float32)] * (self.frame_num - 1) + \
                                   [x[0] for x in input_data["trace_0"]], axis=0)

        images = np.concatenate([stacked_images[i:i + self.frame_num]
                                 for i in range(image_num)], axis=0)

        # clear last heatmaps
        for i in range(image_num):
            images[(i + 1) * self.frame_num - 1, :, :, -self.predicting_dim:] = 0.0

        heatmaps = np.stack([x[0][:,:,-self.predicting_dim:]
                             for x in input_data["trace_0"]], axis=0)
        interacts = np.eye(self.total_interacts)[[x[1]["interact_type"] for x in input_data["trace_0"]]]
        return images, heatmaps, interacts

class MultiScreenLoader(Loader):
    """Multi screen data loader
    """
    def __init__(self, config_json):
        super().__init__(config_json)
        self.dataset_threads = config_json["dataset_threads"]
        self.data_files = next(os.walk(self.training_data_dir)[2])
        self.data_paths = [os.path.join(self.training_data_dir, x) for x in data_files]

        self.finished_pool = set()
        self.remaining_pool = set(self.data_paths)
        self.current_pool = {}

    def next_batch(self):
        # check whether the pools are empty
        pass
