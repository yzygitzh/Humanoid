#coding=utf-8

import json
import numpy as np

from matplotlib import pyplot as plt
from scipy.stats import multivariate_normal
from utils import traverse_view_tree

def gesture_classify(gesture, config_json):
    return config_json["interact_touch"]

def convert_gestures(gestures, config_json):
    downscale_dim = config_json["downscale_dim"]
    interact_dim = config_json["interact_dim"]
    total_dims = config_json["total_dims"]
    gauss_delta = config_json["gauss_delta"]

    # image num, x, y, channels (TEXT/IMAGE)
    interact_heatmap_array = []
    gesture_array = []

    for gesture in gestures:
        interact_heatmap = np.zeros((downscale_dim[0], downscale_dim[1], total_dims), dtype=float)
        interact_heatmap_array.append(interact_heatmap)

        if not len(gesture):
            gesture_array.append(None)
            continue

        gesture_kind = gesture_classify(gesture, config_json)
        gesture_array.append(gesture_kind)

        gesture_pos = [int(gesture[0][0] * downscale_dim[0]),
                       int(gesture[0][1] * downscale_dim[1])]
        var = multivariate_normal(mean=gesture_pos, cov=[[gauss_delta,0],[0,gauss_delta]])
        for x in range(downscale_dim[0]):
            for y in range(downscale_dim[1]):
                interact_heatmap[x, y, interact_dim] = var.pdf([x, y])

        # if True:
        #     visualize_gesture(interact_heatmap, config_json)

    return interact_heatmap_array, gesture_array

def visualize_gesture(interact_heatmap, config_json):
    downscale_dim = config_json["downscale_dim"]
    interact_dim = config_json["interact_dim"]

    image_full = np.zeros([downscale_dim[1], downscale_dim[0], 3], dtype=float)

    print(np.sum(interact_heatmap))
    image_full[:, :, interact_dim] = interact_heatmap[:, :, interact_dim].T
    max_val = np.max(image_full[:, :, interact_dim])
    image_full /= max_val

    plt.imshow(image_full, interpolation='nearest' )
    plt.show()
