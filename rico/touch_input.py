#coding=utf-8

import json
import numpy as np

from matplotlib import pyplot as plt
from scipy.stats import multivariate_normal

GAUSS_MAP = None

def gesture_classify(gesture, config_json):
    downscale_dim = config_json["downscale_dim"]

    assert(len(gesture) > 0)
    if len(gesture) <= config_json["long_touch_threshold"]:
        return config_json["interact_touch"]

    delta_x = (gesture[0][0] - gesture[-1][0]) * downscale_dim[0]
    delta_y = (gesture[0][1] - gesture[-1][1]) * downscale_dim[1]

    dis = int(np.sqrt(delta_x ** 2 + delta_y ** 2))
    if dis <= config_json["swipe_threshold"]:
        return config_json["interact_long_touch"]

    # horizon first
    if abs(delta_x) > abs(delta_y):
        if delta_x < 0:
            return config_json["interact_swipe_right"]
        else:
            return config_json["interact_swipe_left"]
    else:
        if delta_y > 0:
            return config_json["interact_swipe_down"]
        else:
            return config_json["interact_swipe_up"]

def convert_gestures(gestures, config_json):
    downscale_dim = config_json["downscale_dim"]
    interact_dim = config_json["interact_dim"]
    total_dims = config_json["total_dims"]
    gauss_delta = config_json["gauss_delta"]

    # generate GAUSS_MAP cache if not yet
    global GAUSS_MAP
    if GAUSS_MAP is None:
        GAUSS_MAP = np.zeros((downscale_dim[0], downscale_dim[1]), dtype=np.float32)
        var = multivariate_normal(mean=[0, 0], cov=[[gauss_delta,0],[0,gauss_delta]])
        for x in range(downscale_dim[0]):
            for y in range(downscale_dim[1]):
                GAUSS_MAP[x, y] = var.pdf([x, y])

    # image num, x, y, channels (TEXT/IMAGE)
    interact_heatmap_array = []
    gesture_array = []

    for gesture in gestures:
        interact_heatmap = np.zeros((downscale_dim[0], downscale_dim[1], total_dims), dtype=np.float32)
        interact_heatmap_array.append(interact_heatmap)

        if not len(gesture):
            gesture_array.append(None)
            continue

        gesture_kind = gesture_classify(gesture, config_json)
        gesture_array.append({
            "interact_type": gesture_kind,
        })

        gesture_pos = [min(max(int(gesture[0][0] * downscale_dim[0]), 0), downscale_dim[0] - 1),
                       min(max(int(gesture[0][1] * downscale_dim[1]), 0), downscale_dim[1] - 1)]
        for x in range(downscale_dim[0]):
            for y in range(downscale_dim[1]):
                sample_x = abs(x - gesture_pos[0])
                sample_y = abs(y - gesture_pos[1])
                interact_heatmap[x, y, interact_dim] = GAUSS_MAP[sample_x, sample_y]

        # if True:
        #     visualize_gesture(interact_heatmap, config_json)

    return interact_heatmap_array, gesture_array

def visualize_gesture(interact_heatmap, config_json):
    downscale_dim = config_json["downscale_dim"]
    interact_dim = config_json["interact_dim"]

    image_full = np.zeros([downscale_dim[1], downscale_dim[0], 3], dtype=np.float32)

    print(np.sum(interact_heatmap))
    image_full[:, :, interact_dim] = interact_heatmap[:, :, interact_dim].T
    max_val = np.max(image_full[:, :, interact_dim])
    image_full /= max_val

    plt.imshow(image_full, interpolation='nearest' )
    plt.show()
