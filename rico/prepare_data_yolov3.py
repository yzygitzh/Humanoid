#coding=utf-8

import argparse
import json
import os

import numpy as np
from PIL import Image

from .image import convert_semantic_view_tree_file
from .utils import visualize_data, is_valid_data

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    filtered_traces_dir = config_json["filtered_traces_path"]
    semantic_annotations_path = config_json["semantic_annotations_path"]

    output_dir = config_json["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    downscale_dim = config_json["downscale_dim"]

    ui_details_path = config_json["ui_details_path"]
    ui_details = []
    with open(ui_details_path, "r") as f:
        ui_details = [x[:-len(os.linesep)] for x in f.readlines()][1:]

    for ui_detail in ui_details:
        global_id, pkg_name, trace_id, screen_id = ui_detail.split(",")

        # if pkg_name != "com.dev.newbie.comicstand":
        # if pkg_name != "com.whatsapp":
        #     continue

        screenshot_path = os.path.join(filtered_traces_dir, pkg_name, "trace_%s" % trace_id,
                                      "screenshots", "%s.jpg" % screen_id)
        annotation_path = os.path.join(semantic_annotations_path, "%s.json" % global_id)
        if not os.path.exists(screenshot_path) or not os.path.exists(annotation_path):
            continue

        print(screenshot_path)
        print(annotation_path)
        img = Image.open(screenshot_path)
        resized_img = img.resize((downscale_dim[0], downscale_dim[1]), resample=Image.BILINEAR).transpose(Image.TRANSPOSE)
        # visualize_data(np.array(resized_img))
        boxes = convert_semantic_view_tree_file(annotation_path, config_json)
        # print(boxes)

        # draw boxes for debug
        """
        image_data = np.zeros((downscale_dim[0], downscale_dim[1], 3), dtype=np.float32)
        for box in boxes:
            x_min = int((box[1] - box[3] / 2) * downscale_dim[0])
            y_min = int((box[2] - box[4] / 2) * downscale_dim[1])
            x_max = int((box[1] + box[3] / 2) * downscale_dim[0])
            y_max = int((box[2] + box[4] / 2) * downscale_dim[1])
            image_data[x_min-1:x_min, y_min:y_max, 0] = 1.0
            image_data[x_max:x_max+1, y_min:y_max, 0] = 1.0
            image_data[x_min:x_max, y_min-1:y_min, 0] = 1.0
            image_data[x_min:x_max, y_max:y_max+1, 0] = 1.0
        visualize_data(image_data)
        """

        # save data
        if boxes is not None:
            resized_img.save(os.path.join(output_dir, "%s.jpg" % global_id))
            with open(os.path.join(output_dir, "%s.txt" % global_id), "w") as f:
                f.writelines(["%s %s %s %s %s" % (x[0], x[2], x[1], x[4], x[3]) + \
                              os.linesep for x in boxes])

def parse_args():
    parser = argparse.ArgumentParser(description="Prepare RICO dataset for view parsing, using YOLO")
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
