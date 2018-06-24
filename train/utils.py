#coding=utf-8

import numpy as np

from matplotlib import pyplot as plt

def visualize_data(data, label=""):
    image_full = np.zeros([data.shape[1], data.shape[0], 3], dtype=np.float32)

    for i in range(data.shape[2]):
        image_full[:, :, i] = data[:, :, i].T
        max_val = np.max(image_full[:, :, i])
        if max_val > 0:
            image_full[:, :, i] /= max_val

    plt.imshow(image_full, interpolation="nearest")
    plt.xlabel(label)
    plt.show()
