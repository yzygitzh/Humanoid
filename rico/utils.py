#coding=utf-8

import numpy as np

from matplotlib import pyplot as plt

def traverse_view_tree(view_tree, call_back, semantic_ui=False):
    if view_tree is None or not semantic_ui and not is_view_valid(view_tree):
        return
    call_back(view_tree)
    if "children" in view_tree:
        for child in view_tree["children"]:
            traverse_view_tree(child, call_back, semantic_ui)

def is_view_hierarchy_valid(view_tree, config_json, semantic_ui=False):
    origin_dim = config_json["origin_dim"]
    if semantic_ui:
        view_root_bounds = view_tree["bounds"]
    else:
        view_root_bounds = view_tree["activity"]["root"]["bounds"]
    # skip full-screen horizon ones
    if view_root_bounds[2] > view_root_bounds[3] and view_root_bounds[2] > origin_dim[0]:
        return False
    return True

def compute_view_offset(view_tree, config_json, semantic_ui=False):
    if semantic_ui:
        view_root_bounds = view_tree["bounds"]
    else:
        view_root_bounds = view_tree["activity"]["root"]["bounds"]

    downscale_dim = config_json["downscale_dim"]
    origin_dim = config_json["origin_dim"]
    status_bar_height = config_json["status_bar_height"]
    navigation_bar_height = config_json["navigation_bar_height"]
    downscale_ratio = downscale_dim[0] / origin_dim[0]

    view_offset = [0, 0]
    if semantic_ui:
        root_view = view_tree
    else:
        root_view = view_tree["activity"]["root"]

    # heuristically identify non-full-screen window like permission window
    if not root_view["class"].startswith("com.android.internal.policy.PhoneWindow"):
        return view_offset

    # view_tree from DroidBot may not contain activity_name
    if "activity_name" in view_tree and not view_tree["activity_name"] == "com.android.packageinstaller/com.android.packageinstaller.permission.ui.GrantPermissionsActivity":
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

    if "bounds" not in view or "rel-bounds" not in view:
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
    if "text" not in view:
        return False
    for ancestor in view["ancestors"]:
        if "edittext" in ancestor.lower():
            return True
    return "edittext" in view["class"].lower()

def is_valid_data(image, interact, config_json):
    if interact is None:
        return False

    text_dim = config_json["text_dim"]
    image_dim = config_json["image_dim"]
    interact_dim = config_json["interact_dim"]

    if np.sum(image[:, :, text_dim]) + np.sum(image[:, :, image_dim]) == 0:
        return False
    if np.sum(image[:, :, interact_dim]) == 0:
        return False

    return True

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
