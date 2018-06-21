#coding=utf-8

import numpy as np

from matplotlib import pyplot as plt

def traverse_view_tree(view_tree, call_back):
    if not is_view_valid(view_tree):
        return
    call_back(view_tree)
    if "children" in view_tree:
        for child in view_tree["children"]:
            traverse_view_tree(child, call_back)

def is_view_hierarchy_valid(view_tree, config_json):
    origin_dim = config_json["origin_dim"]
    view_root_bounds = view_tree["activity"]["root"]["bounds"]
    # skip full-screen horizon ones
    if view_root_bounds[2] > view_root_bounds[3] and view_root_bounds[2] > origin_dim[0]:
        return False
    return True

def compute_view_offset(view_tree, config_json):
    view_root_bounds = view_tree["activity"]["root"]["bounds"]
    downscale_dim = config_json["downscale_dim"]
    origin_dim = config_json["origin_dim"]
    status_bar_height = config_json["status_bar_height"]
    navigation_bar_height = config_json["navigation_bar_height"]
    downscale_ratio = downscale_dim[0] / origin_dim[0]

    view_offset = [0, 0]
    # heuristically identify non-full-screen window like permission window
    if not view_tree["activity"]["root"]["class"].startswith("com.android.internal.policy.PhoneWindow"):
        return view_offset
    if not view_tree["activity_name"] == "com.android.packageinstaller/com.android.packageinstaller.permission.ui.GrantPermissionsActivity":
        return view_offset

    if view_root_bounds[2] - view_root_bounds[0] < origin_dim[0] and \
        view_root_bounds[3] - view_root_bounds[1] < origin_dim[1] - status_bar_height - navigation_bar_height:
        view_center = [(view_root_bounds[0] + view_root_bounds[2]) / 2,
                    (view_root_bounds[1] + view_root_bounds[3]) / 2]
        view_offset = [int((origin_dim[0] / 2 - view_center[0]) * downscale_ratio),
                       int(((origin_dim[1] + status_bar_height - navigation_bar_height) / 2 - view_center[1]) * downscale_ratio)]
    return view_offset

def is_view_valid(view):
    visible_to_user = view["visible-to-user"]
    if not visible_to_user:
        return False

    bounds = view["bounds"]
    rel_bounds = view["rel-bounds"]

    if (bounds[0] >= bounds[2] or bounds[1] >= bounds[3] or \
        rel_bounds[0] >= rel_bounds[2] or rel_bounds[1] >= rel_bounds[3]):
        return False

    if ((rel_bounds[2] - rel_bounds[0]) < (bounds[2] - bounds[0]) or \
        (rel_bounds[3] - rel_bounds[1]) < (bounds[3] - bounds[1])):
        return False

    return True

def is_text_view(view):
    for ancestor in view["ancestors"]:
        if "edittext" in ancestor.lower():
            return True
    return "edittext" in view["class"].lower()

def get_text_view_signature(view):
    signature = ""

    # class
    signature += "[class]"
    if "class" in view:
        signature += view["class"]

    # resource_id
    signature += "[resource_id]"
    if "resource_id" in view:
        signature += view["resource_id"]

    # text_hint
    signature += "[text_hint]"
    if "text_hint" in view:
        signature += view["text_hint"]

    # pointer
    signature += "[pointer]"
    if "pointer" in view:
        signature += view["pointer"]

    return signature

def visualize_data(data, config_json):
    image_full = np.zeros([data.shape[1], data.shape[0], 3], dtype=float)
    interact_dim = config_json["interact_dim"]

    for i in range(data.shape[2]):
        image_full[:, :, i] = data[:, :, i].T
        if i == interact_dim:
            max_heat = np.max(image_full[:, :, i])
            image_full[:, :, i] /= max_heat
        else:
            image_full[:, :, i] /= 2.0

    plt.imshow(image_full, interpolation='nearest' )
    plt.show()
