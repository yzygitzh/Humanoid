#coding=utf-8

import numpy as np
import tensorflow as tf

from tensorflow.python.ops import array_ops

class BaseModel():
    """Base model
       Build CNN and LSTM units
    """
    def __init__(self, config_json, training=True):
        self.x_dim, self.y_dim = config_json["downscale_dim"]
        self.training_dim = config_json["training_dim"]
        self.predicting_dim = config_json["predicting_dim"]
        self.total_channels = self.training_dim + self.predicting_dim
        self.total_interacts = config_json["total_interacts"]
        if training:
            self.weight_decay = config_json["weight_decay"]
            self.batch_size = config_json["batch_size"]
            self.keep_prob = 0.5
        else:
            self.weight_decay = 0.0
            self.batch_size = 1
            self.keep_prob = 1.0
        self.regularizer = tf.contrib.layers.l2_regularizer(scale=self.weight_decay)

        self.input_images = None
        self.true_heats = tf.placeholder(dtype=tf.float32,
                                         shape=(None, self.x_dim, self.y_dim, self.predicting_dim))
        self.true_interacts = tf.placeholder(dtype=tf.float32,
                                             shape=(None, self.total_interacts))

        # assign later
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
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
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
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
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
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
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
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
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
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
                                      name="conv5")
        self.pool5 = tf.layers.max_pooling2d(inputs=self.conv5,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool5")
        # 6x10

        # generate heats, i.e. single channel output
        self.pool3_heat = tf.layers.conv2d(inputs=self.pool3,
                                           filters=1,
                                           kernel_size=1,
                                           padding="same",
                                           activation=tf.nn.relu,
                                           kernel_regularizer=self.regularizer,
                                           bias_regularizer=self.regularizer,
                                           name="pool3_heat")
        self.pool4_heat = tf.layers.conv2d(inputs=self.pool4,
                                           filters=1,
                                           kernel_size=1,
                                           padding="same",
                                           activation=tf.nn.relu,
                                           kernel_regularizer=self.regularizer,
                                           bias_regularizer=self.regularizer,
                                           name="pool4_heat")
        self.pool5_heat = tf.layers.conv2d(inputs=self.pool5,
                                           filters=1,
                                           kernel_size=1,
                                           padding="same",
                                           activation=tf.nn.relu,
                                           kernel_regularizer=self.regularizer,
                                           bias_regularizer=self.regularizer,
                                           name="pool5_heat")

    def build_loss(self):
        # heatmap loss
        self.heatmap_loss = tf.losses.softmax_cross_entropy(
            tf.reshape(self.true_heats, [-1, 180 * 320]),
            tf.reshape(self.heatmap_out, [-1, 180 * 320]))
        self.predict_heatmaps = tf.reshape(tf.nn.softmax(
            tf.reshape(self.heatmap_out, [-1, 180 * 320])), [-1, 180, 320, 1])
        # interact loss
        self.interact_out_flat = tf.reshape(self.interact_out, [-1, 6 * 10 * 1])
        self.fc = tf.layers.dense(self.interact_out_flat,
                                  self.total_interacts,
                                  activation=tf.nn.relu,
                                  kernel_regularizer=self.regularizer,
                                  bias_regularizer=self.regularizer,
                                  name="fc")
        # self.fc_dropout = tf.layers.dropout(self.fc, name="fc_dropout")
        self.interact_loss = tf.losses.softmax_cross_entropy(self.true_interacts,
                                                             self.fc)
                                                             # self.fc_dropout)
        self.predict_interacts = tf.nn.softmax(self.fc)

        # total loss
        # self.total_loss = tf.add(self.heatmap_loss, self.interact_loss, name="total_loss")
        # self.total_loss = self.heatmap_loss
        self.total_loss = tf.losses.get_total_loss()

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

    def build_model(self):
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
        self.interact_out = self.pool5_heat


class MultipleScreenModel(BaseModel):
    """Model for processing single screenshot
       Use conv-pool-de-conv for heatmap
       Use conv-pool-fc for predicting

       input: batch_num, x_dim, y_dim, channels
    """
    def __init__(self, config_json, training=True):
        super().__init__(config_json, training)
        self.frame_num = config_json["frame_num"]
        self.input_images = tf.placeholder(dtype=tf.float32,
                                           shape=(None, self.x_dim, self.y_dim,
                                                  self.training_dim + self.predicting_dim))
        self.build_cnn()
        self.build_model()
        self.build_loss()
        if training:
            self.build_summary()

    def build_model(self):
        # generate heats
        # using three LSTMs at different resolutions
        # from pool3, pool4 and pool5

        # pool3_heat_in: item_num (how many series), frame_num, x_dim * y_dim
        self.pool3_heat_in = tf.reshape(self.pool3_heat, [-1, self.frame_num, 23 * 40])
        self.pool4_heat_in = tf.reshape(self.pool4_heat, [-1, self.frame_num, 12 * 20])
        self.pool5_heat_in = tf.reshape(self.pool5_heat, [-1, self.frame_num, 6 * 10])

        # pool3_heat_out: item_num (how many series), x_dim, y_dim
        self.pool3_heat_out = tf.add(
            tf.reshape(
            tf.keras.layers.LSTM(units=23 * 40, dropout=self.keep_prob)(self.pool3_heat_in),
            # tf.keras.layers.LSTM(units=23 * 40)(self.pool3_heat_in),
            [-1, 23, 40, 1]),
            tf.reshape(self.pool3_heat,
            [self.batch_size, self.frame_num, 23, 40, 1])[:, self.frame_num - 1, :,:,:])
        self.pool4_heat_out = tf.add(tf.reshape(
            tf.keras.layers.LSTM(units=12 * 20, dropout=self.keep_prob)(self.pool4_heat_in),
            # tf.keras.layers.LSTM(units=12 * 20)(self.pool4_heat_in),
            [-1, 12, 20, 1]),
            tf.reshape(self.pool4_heat,
            [self.batch_size, self.frame_num, 12, 20, 1])[:, self.frame_num - 1, :,:,:])
        self.pool5_heat_out = tf.add(tf.reshape(
            tf.keras.layers.LSTM(units=6 * 10, dropout=self.keep_prob)(self.pool5_heat_in),
            # tf.keras.layers.LSTM(units=6 * 10)(self.pool5_heat_in),
            [-1, 6, 10, 1]),
            tf.reshape(self.pool5_heat,
            [self.batch_size, self.frame_num, 6, 10, 1])[:, self.frame_num - 1, :,:,:])

        # do upsampling
        # 6x10
        self.pool5_up_filters = tf.get_variable("pool5_up_filters", [4, 4, 1, 1], regularizer=self.regularizer)
        self.pool5_up = tf.nn.relu(tf.nn.conv2d_transpose(value=self.pool5_heat_out,
                                   filter=self.pool5_up_filters,
                                   output_shape=[self.batch_size, 12, 20, 1],
                                   strides=[1, 2, 2, 1],
                                   name="pool5_up"))
        # 12x20
        self.pool4_heat_sum = tf.add(self.pool5_up, self.pool4_heat_out, name="pool4_heat_sum")
        self.pool4_up_filters = tf.get_variable("pool4_up_filters", [4, 4, 1, 1], regularizer=self.regularizer)
        self.pool4_up = tf.nn.relu(tf.nn.conv2d_transpose(value=self.pool4_heat_sum,
                                   filter=self.pool4_up_filters,
                                   output_shape=[self.batch_size, 23, 40, 1],
                                   strides=[1, 2, 2, 1],
                                   name="pool4_up"))
        # 23x40
        self.pool3_heat_sum = tf.add(self.pool4_up, self.pool3_heat_out, name="pool3_heat_sum")
        self.pool3_up_filters = tf.get_variable("pool3_up_filters", [16, 16, 1, 1], regularizer=self.regularizer)
        self.pool3_up = tf.nn.relu(tf.nn.conv2d_transpose(value=self.pool3_heat_sum,
                                   filter=self.pool3_up_filters,
                                   output_shape=[self.batch_size, 180, 320, 1],
                                   strides=[1, 8, 8, 1],
                                   name="pool3_up"))
        self.heatmap_out = self.pool3_up
        self.interact_out = self.pool5_heat_out

    def build_summary(self):
        # summary
        tf.summary.scalar("heatmap_loss", self.heatmap_loss)
        tf.summary.scalar("interact_loss", self.interact_loss)
        tf.summary.scalar("total_loss", self.total_loss)
        tf.summary.image("input_images",
                         self.input_images,
                         max_outputs=self.batch_size*self.frame_num)
        """
        tf.summary.image("sample_heatmaps",
                         self.input_images[:,:,:,-self.predicting_dim:],
                         max_outputs=self.batch_size*self.frame_num)
        """
        tf.summary.image("true_heatmaps",
                         self.true_heats,
                         max_outputs=self.batch_size)
        tf.summary.image("predict_heatmaps",
                         self.predict_heatmaps,
                         max_outputs=self.batch_size)
        tf.summary.histogram("true_interacts", self.true_interacts)
        tf.summary.histogram("predict_interacts", self.predict_interacts)

        tf.summary.histogram("conv1_activation", self.conv1)
        tf.summary.histogram("conv2_activation", self.conv2)
        tf.summary.histogram("conv3_activation", self.conv3)
        tf.summary.histogram("conv4_activation", self.conv4)
        tf.summary.histogram("conv5_activation", self.conv5)
        tf.summary.histogram("conv1_gradient", tf.gradients(self.total_loss, self.conv1))
        tf.summary.histogram("conv2_gradient", tf.gradients(self.total_loss, self.conv2))
        tf.summary.histogram("conv3_gradient", tf.gradients(self.total_loss, self.conv3))
        tf.summary.histogram("conv4_gradient", tf.gradients(self.total_loss, self.conv4))
        tf.summary.histogram("conv5_gradient", tf.gradients(self.total_loss, self.conv5))

        tf.summary.histogram("pool3_heat_out_activation", self.pool3_heat_out)
        tf.summary.histogram("pool4_heat_out_activation", self.pool4_heat_out)
        tf.summary.histogram("pool5_heat_out_activation", self.pool5_heat_out)
        tf.summary.histogram("pool3_heat_out_gradient", tf.gradients(self.total_loss, self.pool3_heat_out))
        tf.summary.histogram("pool4_heat_out_gradient", tf.gradients(self.total_loss, self.pool4_heat_out))
        tf.summary.histogram("pool5_heat_out_gradient", tf.gradients(self.total_loss, self.pool5_heat_out))

        tf.summary.histogram("pool3_up_filters_data", self.pool3_up_filters)
        tf.summary.histogram("pool4_up_filters_data", self.pool4_up_filters)
        tf.summary.histogram("pool5_up_filters_data", self.pool5_up_filters)
        tf.summary.histogram("pool3_up_filters_gradient", tf.gradients(self.total_loss, self.pool3_up_filters))
        tf.summary.histogram("pool4_up_filters_gradient", tf.gradients(self.total_loss, self.pool4_up_filters))
        tf.summary.histogram("pool5_up_filters_gradient", tf.gradients(self.total_loss, self.pool5_up_filters))
