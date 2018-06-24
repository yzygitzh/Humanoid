#coding=utf-8

import numpy as np
import tensorflow as tf

from tensorflow.python.ops import array_ops

class BaseModel():
    """Base model
       Build CNN and LSTM units
    """
    def __init__(self, config_json):
        self.x_dim, self.y_dim = config_json["downscale_dim"]
        self.training_dim = config_json["training_dim"]
        self.predicting_dim = config_json["predicting_dim"]
        self.total_interacts = config_json["total_interacts"]
        self.batch_size = config_json["batch_size"]

        self.true_heats = tf.placeholder(dtype=tf.float32,
                                         shape=(None, self.x_dim, self.y_dim, self.predicting_dim))
        self.true_interacts = tf.placeholder(dtype=tf.float32,
                                             shape=(None, self.total_interacts))

        # assign later
        self.input_images = None
        self.heatmap_out = None
        self.interact_out = None

    def get_feed_dict(self, images, heatmaps, interacts):
        return {
            self.input_images: images,
            self.true_heats: heatmaps,
            self.true_interacts: interacts
        }

    def build_cnn(self):
        # First generate low-resolution heatmap
        # 180x320
        self.conv1 = tf.layers.conv2d(inputs=self.input_images,
                                      filters=16,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      name="conv1")
        self.pool1 = tf.layers.max_pooling2d(inputs=self.conv1,
                                             pool_size=2,
                                             strides=2,
                                             name="pool1")
        # 90x160
        self.conv2 = tf.layers.conv2d(inputs=self.pool1,
                                      filters=32,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      name="conv2")
        self.pool2 = tf.layers.max_pooling2d(inputs=self.conv2,
                                             pool_size=2,
                                             strides=2,
                                             name="pool2")
        # 45x80
        self.conv3 = tf.layers.conv2d(inputs=self.pool2,
                                      filters=64,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      name="conv3")
        self.pool3 = tf.layers.max_pooling2d(inputs=self.conv3,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool3")
        # 23x40
        self.conv4 = tf.layers.conv2d(inputs=self.pool3,
                                      filters=64,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      name="conv4")
        self.pool4 = tf.layers.max_pooling2d(inputs=self.conv4,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool4")
        # 12x20
        self.conv5 = tf.layers.conv2d(inputs=self.pool4,
                                      filters=64,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      name="conv5")
        self.pool5 = tf.layers.max_pooling2d(inputs=self.conv5,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool5")

    def build_loss(self):
        # heatmap loss
        print(self.heatmap_out)
        self.heatmap_loss = tf.losses.softmax_cross_entropy(
            tf.reshape(self.true_heats, [-1, 180 * 320]),
            tf.reshape(self.heatmap_out, [-1, 180 * 320]))
        self.predict_heatmaps = tf.reshape(tf.nn.softmax(
            tf.reshape(self.heatmap_out, [-1, 180 * 320])), [-1, 180, 320, 1])
        # interact loss
        self.interact_out_flat = tf.reshape(self.interact_out, [-1, 6 * 10 * 64])
        self.fc = tf.layers.dense(self.interact_out_flat,
                                  self.total_interacts,
                                  activation=tf.nn.relu,
                                  name="fc")
        self.fc_dropout = tf.layers.dropout(self.fc, name="fc_dropout")
        self.interact_loss = tf.losses.softmax_cross_entropy(self.true_interacts,
                                                             self.fc_dropout)
        self.predict_interacts = tf.nn.softmax(self.fc)

        # total loss
        self.total_loss = tf.add(self.heatmap_loss, self.interact_loss, name="total_loss")


class SingleScreenModel(BaseModel):
    """Model for processing single screenshot
       Use conv-pool-de-conv for heatmap
       Use conv-pool-fc for predicting

       input: batch_num, x_dim, y_dim, channels
    """
    def __init__(self, config_json):
        super().__init__(config_json)
        self.input_images = tf.placeholder(dtype=tf.float32,
                                           shape=(None, self.x_dim, self.y_dim, self.training_dim))
        self.build_cnn()
        self.build_model()
        self.build_loss()
        print(self.heatmap_loss)

    def build_model(self):
        # generate heats
        self.pool3_heat = tf.layers.conv2d(inputs=self.pool3,
                                           filters=1,
                                           kernel_size=1,
                                           padding="same",
                                           activation=tf.nn.relu,
                                           name="pool3_heat")
        self.pool4_heat = tf.layers.conv2d(inputs=self.pool4,
                                           filters=1,
                                           kernel_size=1,
                                           padding="same",
                                           activation=tf.nn.relu,
                                           name="pool4_heat")
        self.pool5_heat = tf.layers.conv2d(inputs=self.pool5,
                                           filters=1,
                                           kernel_size=1,
                                           padding="same",
                                           activation=tf.nn.relu,
                                           name="pool5_heat")
        # do upsampling
        # 6x10
        self.pool5_up_filters = tf.get_variable("pool5_up_filters", [4, 4, 1, 1])
        self.pool5_up = tf.nn.relu(tf.nn.conv2d_transpose(value=self.pool5_heat,
                                   filter=self.pool5_up_filters,
                                   output_shape=[self.batch_size, 12, 20, 1],
                                   strides=[1, 2, 2, 1],
                                   name="pool5_up"))
        # 12x20
        self.pool4_heat_sum = tf.add(self.pool5_up, self.pool4_heat, name="pool4_heat_sum")
        self.pool4_up_filters = tf.get_variable("pool4_up_filters", [4, 4, 1, 1])
        self.pool4_up = tf.nn.relu(tf.nn.conv2d_transpose(value=self.pool4_heat_sum,
                                   filter=self.pool4_up_filters,
                                   output_shape=[self.batch_size, 23, 40, 1],
                                   strides=[1, 2, 2, 1],
                                   name="pool4_up"))
        # 23x40
        self.pool3_heat_sum = tf.add(self.pool4_up, self.pool3_heat, name="pool3_heat_sum")
        self.pool3_up_filters = tf.get_variable("pool3_up_filters", [16, 16, 1, 1])
        self.pool3_up = tf.nn.relu(tf.nn.conv2d_transpose(value=self.pool3_heat_sum,
                                   filter=self.pool3_up_filters,
                                   output_shape=[self.batch_size, 180, 320, 1],
                                   strides=[1, 8, 8, 1],
                                   name="pool3_up"))
        self.heatmap_out = self.pool3_up
        self.interact_out = self.pool5
