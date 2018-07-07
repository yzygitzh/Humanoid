#coding=utf-8

import logging
logging.basicConfig(format="%(asctime)-15s %(message)s")
import os
import pickle
import queue
import random
import threading
import time

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
        self.logger = logging.getLogger("loader")
        self.logger.setLevel(logging.INFO)

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

class MultipleScreenLoader(Loader):
    """Normal multiple screen data loader, in contrast to debug data loader
    """
    def __init__(self, config_json):
        super().__init__(config_json)
        self.dataset_threads = config_json["dataset_threads"]
        self.batch_size = config_json["batch_size"]
        self.frame_num = config_json["frame_num"]
        self.data_files = next(os.walk(self.training_data_dir))[2]
        # self.data_files = ["jp.naver.linecard.android.pickle",
        #                    "co.brainly.pickle"]
        self.data_paths = [os.path.join(self.training_data_dir, x) for x in self.data_files]
        self.data_queue = queue.Queue()
        self.path_queue = queue.Queue()
        self.epochs = -1
        self.loading_thread = None
        self.loading_thread_result = None
        self.loading_thread_out = None
        self.produce_threshold = 10000

    def get_current_epoch(self):
        return self.epochs

    def reload_paths(self):
        self.epochs += 1
        self.logger.info("epoch: %d", self.epochs)
        random.shuffle(self.data_paths)
        for data_path in self.data_paths:
            self.path_queue.put(data_path)

    def load_pickles(self, data_paths):
        data_item_list = []
        for data_path in data_paths:
            with open(data_path, "rb") as f:
                input_data = pickle.load(f)
            # assemble frames
            # do zero padding before the first image
            for trace_key in input_data:
                image_num = len(input_data[trace_key])
                if image_num == 0:
                    continue
                stacked_images = np.stack([np.zeros_like(input_data[trace_key][0][0], dtype=np.float32)] * (self.frame_num - 1) + \
                                          [x[0] for x in input_data[trace_key]], axis=0)

                images = [stacked_images[i:i + self.frame_num].copy() for i in range(image_num)]

                # for each image, clear last heatmaps
                for image in images:
                    image[self.frame_num - 1, :, :, -self.predicting_dim:] = 0.0
                    image -= 0.5
                    # for i in range(self.frame_num):
                    #     visualize_data(image[i])

                heatmaps = [x[0][:,:,-self.predicting_dim:].copy() for x in input_data[trace_key]]
                interacts = np.split(np.eye(self.total_interacts)[[x[1]["interact_type"] for x in input_data[trace_key]]],
                                     image_num, axis=0)

                for data_item in zip(images, heatmaps, interacts):
                    data_item_list.append(data_item)
        rand_idx = list(range(len(data_item_list)))
        random.shuffle(rand_idx)
        for i in rand_idx:
            self.data_queue.put(data_item_list[i])

    def next_batch_producer(self):
        # always try to load data when < threshold
        # poll check threshold
        while True:
            if self.data_queue.qsize() < self.produce_threshold:
                paths_to_load = []
                for i in range(min(self.dataset_threads, len(self.data_paths))):
                    if self.path_queue.empty():
                        self.reload_paths()
                    paths_to_load.append(self.path_queue.get())
                    # self.logger.info("loading: %s", paths_to_load[-1])
                self.load_pickles(paths_to_load)
            time.sleep(1)

    def next_batch_consumer(self):
        # always try to get data
        batch_image_list = []
        batch_heatmap_list = []
        batch_interact_list = []
        for i in range(self.batch_size):
            image, heatmap, interact = self.data_queue.get()
            batch_image_list.append(image)
            batch_heatmap_list.append(heatmap)
            batch_interact_list.append(interact)
        return (np.concatenate(batch_image_list, axis=0), \
                np.stack(batch_heatmap_list, axis=0), \
                np.concatenate(batch_interact_list, axis=0))

    def next_batch(self):
        if self.loading_thread is None:
            self.loading_thread = threading.Thread(target=self.next_batch_producer)
            self.loading_thread.start()
        return self.next_batch_consumer()
