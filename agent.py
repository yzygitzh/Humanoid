#coding=utf-8

import argparse
import json
import os
import pickle
import random
import socket
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

import numpy as np
from pyflann import *
import tensorflow as tf
tf_config = tf.ConfigProto()
tf_config.gpu_options.allow_growth = True
from matplotlib import pyplot as plt

from rico.image import convert_view_trees
from rico.touch_input import convert_gestures
from rico.utils import traverse_view_tree
from train.model import MultipleScreenModel
from train.utils import visualize_data

class RPCHandler(SimpleXMLRPCRequestHandler):
    def _dispatch(self, method, params):
        try:
            return self.server.funcs[method](*params)
        except:
            import traceback
            traceback.print_exc()
            raise

class TextGenerator():
    def __init__(self, config_json):
        with open(config_json["embedding_path"], "r") as f:
            self.embedding = json.load(f)

        self.points = np.array(self.embedding["vectors"], dtype=np.float32)
        print("load point matrix", self.points.shape)
        self.texts = self.embedding["texts"]

        self.flann = FLANN()
        self.flann.build_index(self.points, algorithm="kmeans",
                               branching=32, iterations=7, checks=16)
        print("built point index")

    def get_text(self, point):
        result, _ = self.flann.nn_index(point, 2, algorithm="kmeans",
                                        branching=32, iterations=7, checks=16)
        point_indices = result[0]
        random.shuffle(point_indices)
        return self.texts[point_indices[0]]

class DroidBotDataProcessor():
    def __init__(self, agent_config_json):
        rico_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        "rico", "config.json")
        with open(rico_config_path, "r") as rico_config_file:
            self.rico_config_json = json.load(rico_config_file)

        train_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        "train", "config.json")
        with open(train_config_path, "r") as train_config_file:
            self.train_config_json = json.load(train_config_file)

        self.origin_dim = self.rico_config_json["origin_dim"]
        self.downscale_dim = self.rico_config_json["downscale_dim"]
        self.frame_num = self.train_config_json["frame_num"]
        self.predicting_dim = self.train_config_json["predicting_dim"]
        self.total_interacts = self.train_config_json["total_interacts"]
        self.navigation_back_bounds_options = agent_config_json["navigation_back_bounds"]

    def __clean_view_tree(self, view_tree):
        view_tree["visible-to-user"] = view_tree["visible"]
        bounds = view_tree["bounds"]
        view_tree["bounds"] = [bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]]
        view_tree["rel-bounds"] = view_tree["bounds"]
        for child in view_tree["children"]:
            self.__clean_view_tree(child)

    def __event_to_pos(self, event):
        event_type = event["event_type"]
        if "x" in event and "y" in event and event["x"] is not None and event["y"] is not None:
            return [[event["x"] / self.origin_dim[0],
                     event["y"] / self.origin_dim[1]]]
        elif event_type in ["touch", "long_touch", "scroll", "set_text"]:
            # get view center
            x = (event["view"]["bounds"][0][0] + event["view"]["bounds"][1][0]) / 2
            y = (event["view"]["bounds"][0][1] + event["view"]["bounds"][1][1]) / 2
            return [[x / self.origin_dim[0],
                     y / self.origin_dim[1]]]
        elif event_type == "key" and event["name"] == "BACK":
            # get back center
            x = (self.navigation_back_bounds[0] + self.navigation_back_bounds[2]) / 2
            y = (self.navigation_back_bounds[1] + self.navigation_back_bounds[3]) / 2
            return [[x / self.origin_dim[0],
                     y / self.origin_dim[1]]]
        else:
            # event without pos
            return []

    def __events_to_touchs(self, events):
        return [self.__event_to_pos(x) for x in events]

    def __compute_prob(self, x_min, x_max, y_min, y_max, event_type, heatmap, interact):
        if x_min >= x_max or y_min >= y_max:
            return 0.0
        prob_sum = np.sum(heatmap[x_min:x_max, y_min:y_max])
        weighted_sum = prob_sum / ((x_max-x_min)*(y_max-y_min))
        return interact[self.rico_config_json[event_type]] * weighted_sum

    def update_origin_dim(self, screen_res):
        # print(screen_res)
        self.origin_dim = screen_res
        self.rico_config_json["origin_dim"] = screen_res

    def view_tree_to_image(self, view_tree):
        self.__clean_view_tree(view_tree)
        image = convert_view_trees([{
            "activity": {"root": view_tree}
        }], self.rico_config_json)[0]
        # visualize_data(image)
        return image

    def view_tree_texts(self, view_tree):
        text_list = []
        def text_call_back(view_tree):
            if "resource_id" in view_tree and \
               view_tree["resource_id"] is not None and \
               len(view_tree["resource_id"]) and \
               "text" in view_tree and \
               view_tree["text"] is not None and \
               len(view_tree["text"]) and \
               view_tree["visible"]:
                text_list.append(view_tree["resource_id"] + "$" + str(view_tree["enabled"]))
        traverse_view_tree(view_tree, text_call_back)
        text_list.sort()
        # print(text_list)
        return text_list

    def events_to_probs(self, events, heatmap, interact):
        event_probs = []
        for event in events:
            event_type = event["event_type"]
            event_prob = 0.0
            if event_type in ["touch", "long_touch", "scroll", "set_text", "key"]:
                if event_type == "key" and event["name"] != "BACK":
                    event_prob = 0.0

                if event_type == "key":
                    bounds = self.navigation_back_bounds
                else:
                    bounds = event["view"]["bounds"]
                    bounds = [bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]]
                x_min = max(0, int(bounds[0] * self.downscale_ratio))
                y_min = max(0, int(bounds[1] * self.downscale_ratio))
                x_max = min(self.downscale_dim[0], int(bounds[2] * self.downscale_ratio))
                y_max = min(self.downscale_dim[1], int(bounds[3] * self.downscale_ratio))
                if event_type in ["touch", "key"]:
                    event_prob = self.__compute_prob(x_min, x_max, y_min, y_max, "interact_touch", heatmap, interact)
                elif event_type == "long_touch":
                    event_prob = self.__compute_prob(x_min, x_max, y_min, y_max, "interact_long_touch", heatmap, interact)
                elif event_type == "scroll":
                    event_prob = self.__compute_prob(x_min, x_max, y_min, y_max,
                                            "interact_swipe_%s" % (event["direction"].lower()),
                                            heatmap, interact)
                elif event_type == "set_text":
                    event_prob = self.__compute_prob(x_min, x_max, y_min, y_max, "interact_input_text", heatmap, interact)
            event_probs.append(event_prob)
        return event_probs

    def process(self, query_json):
        self.downscale_ratio = self.rico_config_json["downscale_dim"][0] / query_json["screen_res"][0]
        self.navigation_back_bounds = self.navigation_back_bounds_options\
                                           ["%dx%d" % (query_json["screen_res"][1],
                                                       query_json["screen_res"][0])]
        for i in range(4):
            self.navigation_back_bounds[i] *= self.downscale_ratio

        view_trees = [{
            "activity": {"root": x}
        } for x in query_json["history_view_trees"]]

        # clean view trees
        for view_tree in view_trees:
            self.__clean_view_tree(view_tree["activity"]["root"])
        # padding
        view_trees = [None] * (self.frame_num - len(view_trees)) + view_trees
        # assemble images by view tree
        images = convert_view_trees(view_trees, self.rico_config_json)

        # assemble touch heatmaps
        history_events = query_json["history_events"]
        gestures = self.__events_to_touchs(history_events)
        # padding
        gestures = [[]] * (self.frame_num - 1 - len(gestures)) + gestures + [[]]
        # print(gestures)
        heats, _ = convert_gestures(gestures, self.rico_config_json)

        summed_image = [x + y for x, y in zip(images, heats)]

        stacked_image = np.stack(summed_image, axis=0)
        stacked_image[-1, :, :, -self.predicting_dim:] = 0.0
        stacked_image -= 0.5

        dummy_heat = np.zeros_like(stacked_image[:1,:,:,:1])
        dummy_interact = np.zeros((1, self.total_interacts))

        return stacked_image, dummy_heat, dummy_interact

class HumanoidAgent():
    def __init__(self, config_json):
        self.domain = config_json["domain"]
        if "port" in config_json:
            self.rpc_port = config_json["port"]
        else:
            self.rpc_port = self.get_random_port()
        print("Serving at %s:%d" % (self.domain, self.rpc_port))
        self.server = SimpleXMLRPCServer((self.domain, self.rpc_port), RPCHandler)
        self.server.register_function(self.predict, "predict")
        self.server.register_function(self.render_view_tree, "render_view_tree")
        self.server.register_function(self.render_content_free_view_tree, "render_content_free_view_tree")

        train_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        "train", "config.json")
        with open(train_config_path, "r") as train_config_file:
            self.train_config_json = json.load(train_config_file)

        self.model = MultipleScreenModel(self.train_config_json, training=False)
        self.saver = tf.train.Saver()
        self.sess = tf.Session()
        self.saver.restore(self.sess, config_json["model_path"])
        self.data_processor = DroidBotDataProcessor(config_json)
        self.text_generator = TextGenerator(config_json)
        print("=== Humanoid XMLRPC service ready at %s:%d ===" % (self.domain, self.rpc_port))

    def get_random_port(self):
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.bind(("", 0))
        port = temp_sock.getsockname()[1]
        temp_sock.close()
        return port

    def predict(self, query_json_str):
        query_json = json.loads(query_json_str)
        try:
            self.data_processor.update_origin_dim(query_json["screen_res"])
            possible_events = query_json["possible_events"]
            image, heat, interact = self.data_processor.process(query_json)
            heatmap, interact, pool5_heat_out= self.sess.run(
                [self.model.predict_heatmaps,
                self.model.predict_interacts,
                self.model.pool5_heat_out],
                feed_dict=self.model.get_feed_dict(image, heat, interact))
            """
            visualize_data(stacked_image[0] + 0.5)
            visualize_data(stacked_image[1] + 0.5)
            visualize_data(stacked_image[2] + 0.5)
            visualize_data(stacked_image[3] + 0.5)
            visualize_data(heatmap[0])
            print(interact[0])
            """
            # print(event_probs)
            # print(prob_idx)
            event_probs = self.data_processor.events_to_probs(possible_events, heatmap[0,:,:,0], interact[0])
            prob_idx = sorted(range(len(event_probs)), key=lambda k: event_probs[k], reverse=True)
            text = self.text_generator.get_text(pool5_heat_out.reshape([1, -1]))
            # print(prob_idx, text)
            return json.dumps({
                "indices": prob_idx,
                "text": text
            })
        except Exception as e:
            print(e)
            event_indices = list(range(len(query_json["possible_events"])))
            random.shuffle(event_indices)
            return json.dumps({
                "indices": event_indices,
                "text": "Humanoid"
            })

    def render_view_tree(self, query_json_str):
        try:
            query_json = json.loads(query_json_str)
            self.data_processor.update_origin_dim(query_json["screen_res"])
            view_tree = query_json["view_tree"]
            image = self.data_processor.view_tree_to_image(view_tree)
            texts = self.data_processor.view_tree_texts(view_tree)
            return json.dumps({
                "image": image.astype(int).flatten().tolist(),
                "texts": texts
            })
        except Exception as e:
            print(e)
            return ""

    def render_content_free_view_tree(self, query_json_str):
        try:
            query_json = json.loads(query_json_str)
            self.data_processor.update_origin_dim(query_json["screen_res"])
            view_tree = query_json["view_tree"]
            image = self.data_processor.view_tree_to_image(view_tree)
            return json.dumps({
                "image": image.astype(int).flatten().tolist()
            })
        except Exception as e:
            print(e)
            return ""

    def run(self):
        self.server.serve_forever()

class HumanoidTest():
    def __init__(self):
        with open("config.json", "r") as f:
            self.config_json = json.load(f)

        train_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        "train", "config.json")
        with open(train_config_path, "r") as train_config_file:
            self.train_config_json = json.load(train_config_file)

        self.model = MultipleScreenModel(self.train_config_json, training=False)
        self.saver = tf.train.Saver()
        self.sess = tf.Session()
        self.saver.restore(self.sess, self.config_json["model_path"])
        self.data_processor = DroidBotDataProcessor(self.config_json)

    def __assemble_view_tree(self, root_view, views):
        children = list(enumerate(root_view["children"]))
        if not len(children):
            return
        for i, j in children:
            import copy
            root_view["children"][i] = copy.deepcopy(views[j])
            self.__assemble_view_tree(root_view["children"][i], views)

    def test_model(self):
        with open("/tmp/tele2/state_2018-08-10_160925.json", "r") as f:
            droidbot_state = json.load(f)
            self.__assemble_view_tree(droidbot_state["views"][0],
                                      droidbot_state["views"])
            self.data_processor.update_origin_dim([720, 1280])
            stacked_image, heat, interact = self.data_processor.process({
                "history_view_trees": [droidbot_state["views"][0]],
                "history_events": [],
                "possible_events": [],
                "screen_res": [720, 1280]
            })

            heatmap, interact, pool5_heat_out= self.sess.run(
                [self.model.predict_heatmaps,
                self.model.predict_interacts,
                self.model.pool5_heat_out],
                feed_dict=self.model.get_feed_dict(stacked_image, heat, interact))
            print(interact[0])

            import scipy.misc
            scipy.misc.imsave("/tmp/skeleton.png",
                              np.transpose(stacked_image[3] + 0.5, (1, 0, 2)))

            # gestures = [[[58 / 768, 103 / 1280]]]
            # heats, _ = convert_gestures(gestures, self.data_processor.rico_config_json)
            # print(np.sum(heats[0]))
            # print(heats[0].shape)
            heats_max = np.max(heatmap[0])
            scipy.misc.imsave("/tmp/heat.png", np.transpose(heatmap[0][:,:,0] / heats_max, (1, 0)))

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    # data_processor = DroidBotDataProcessor(config_json)
    # with open("/mnt/EXT_volume/projects_light/Humanoid/query.json", "r") as f:
    #     data_processor.process(json.load(f))
    agent = HumanoidAgent(config_json)
    agent.run()

def parse_args():
    parser = argparse.ArgumentParser(description="Humanoid agent")
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
    # HumanoidTest().test_model()
