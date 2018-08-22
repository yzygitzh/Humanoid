#coding=utf-8

import argparse
import json
import os
import pickle

import numpy as np

def safe_dict_get(view_dict, key, default=None):
    return view_dict[key] if (key in view_dict) else default

def get_all_children(view_dict, views):
    children = safe_dict_get(view_dict, 'children')
    if not children:
        return set()
    children = set(children)
    for child in children:
        children_of_child = get_all_children(views[child], views)
        children.union(children_of_child)
    return children

def get_possible_input(views):
    possible_events = []
    enabled_view_ids = []
    touch_exclude_view_ids = set()
    for view_dict in views:
        # exclude navigation bar if exists
        if safe_dict_get(view_dict, 'enabled') and \
           safe_dict_get(view_dict, 'resource_id') != 'android:id/navigationBarBackground':
            enabled_view_ids.append(view_dict['temp_id'])
    enabled_view_ids.reverse()

    for view_id in enabled_view_ids:
        if safe_dict_get(views[view_id], 'clickable'):
            possible_events.append({"event_type": "touch", "view": views[view_id]})
            touch_exclude_view_ids.add(view_id)
            touch_exclude_view_ids.union(get_all_children(views[view_id], views))

    for view_id in enabled_view_ids:
        if safe_dict_get(views[view_id], 'scrollable'):
            possible_events.append({"event_type": "scroll", "view": views[view_id], "direction": "UP"})
            possible_events.append({"event_type": "scroll", "view": views[view_id], "direction": "DOWN"})
            possible_events.append({"event_type": "scroll", "view": views[view_id], "direction": "LEFT"})
            possible_events.append({"event_type": "scroll", "view": views[view_id], "direction": "RIGHT"})

    for view_id in enabled_view_ids:
        if safe_dict_get(views[view_id], 'checkable'):
            possible_events.append({"event_type": "touch", "view": views[view_id]})
            touch_exclude_view_ids.add(view_id)
            touch_exclude_view_ids.union(get_all_children(views[view_id], views))

    for view_id in enabled_view_ids:
        if safe_dict_get(views[view_id], 'long_clickable'):
            possible_events.append({"event_type": "long_touch", "view": views[view_id]})

    for view_id in enabled_view_ids:
        if safe_dict_get(views[view_id], 'editable'):
            possible_events.append({"event_type": "set_text", "view": views[view_id], "text": "HelloWorld"})
            touch_exclude_view_ids.add(view_id)

    for view_id in enabled_view_ids:
        if view_id in touch_exclude_view_ids:
            continue
        children = safe_dict_get(views[view_id], 'children')
        if children and len(children) > 0:
            continue
        possible_events.append({"event_type": "touch", "view": views[view_id]})

    # For old Android navigation bars
    possible_events.append({"event_type": "key", "name": "BACK"})
    possible_events.append({"event_type": "key", "name": "menu"})

    return possible_events

def view_tree_to_list(view_tree, view_list):
    tree_id = len(view_list)
    view_tree['temp_id'] = tree_id

    bounds = [[-1, -1], [-1, -1]]
    bounds[0][0] = view_tree['bounds'][0]
    bounds[0][1] = view_tree['bounds'][1]
    bounds[1][0] = view_tree['bounds'][2]
    bounds[1][1] = view_tree['bounds'][3]
    width = bounds[1][0] - bounds[0][0]
    height = bounds[1][1] - bounds[0][1]
    view_tree['size'] = "%d*%d" % (width, height)
    view_tree['bounds'] = bounds

    view_list.append(view_tree)
    children_ids = []

    if "children" in view_tree:
        for child_tree in view_tree['children']:
            child_tree['parent'] = tree_id
            view_tree_to_list(child_tree, view_list)
            children_ids.append(child_tree['temp_id'])
        view_tree['children'] = children_ids
    else:
        view_tree['children'] = []

def get_view_id_from_pos(views, pos):
    view_id = -1
    for i, view in enumerate(views):
        if view["bounds"][0][0] <= pos[0] <= view["bounds"][1][0] and \
           view["bounds"][0][1] <= pos[1] <= view["bounds"][1][1]:
            view_id = i
    return view_id

action2event_type = {
    0: "touch",
    1: "long_touch",
    2: "scroll_left",
    3: "scroll_right",
    4: "scroll_up",
    5: "scroll_down",
    6: "set_text",
}

def is_events_equal(views, event, action, pos):
    if event["event_type"] == "touch" and action == 0 or \
       event["event_type"] == "long_touch" and action == 1 or \
       event["event_type"] == "scroll" and event["direction"] == "LEFT" and action == 2 or \
       event["event_type"] == "scroll" and event["direction"] == "RIGHT" and action == 3 or \
       event["event_type"] == "scroll" and event["direction"] == "UP" and action == 4 or \
       event["event_type"] == "scroll" and event["direction"] == "DOWN" and action == 5 or \
       event["event_type"] == "set_text" and action == 6:
        if get_view_id_from_pos(views, pos) == event["view"]["temp_id"]:
            return True
    elif event["event_type"] == "key" and event["name"] == "BACK" and \
         action == 0 and 180 <= pos[0] <= 540 and 2392 <= pos[1] <= 2560:
            return True
    return False

def assemble_view_tree(root_view, views):
    root_view["visible"] = root_view["visible-to-user"]
    children = list(enumerate(root_view["children"]))
    if not len(children):
        return
    for i, j in children:
        import copy
        root_view["children"][i] = copy.deepcopy(views[j])
        assemble_view_tree(root_view["children"][i], views)

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    validation_data_dir = config_json["validation_data_dir"]
    app_pickles = next(os.walk(validation_data_dir))[2]
    accuracy_tuples = []
    for app_pickle in app_pickles:
        print(app_pickle)
        history_view_trees = []
        history_events = []
        pickle_path = os.path.join(validation_data_dir, app_pickle)
        with open(pickle_path, "rb") as f:
            input_data = pickle.load(f)
        for trace_key in input_data:
            count = 0
            for view_tree_path, interact, pos in input_data[trace_key]:
                pos = (pos[0] * 1440 / 180, pos[1] * 2560 / 320)
                action = interact["interact_type"]
                with open(view_tree_path, "r") as f:
                    view_tree = json.load(f)["activity"]["root"]
                view_list = []

                import copy
                view_tree_to_list(copy.deepcopy(view_tree), view_list)
                possible_events = get_possible_input(view_list)

                droidbot_view_tree_root = copy.deepcopy(view_list[0])
                assemble_view_tree(droidbot_view_tree_root, view_list)
                # clean_view_tree(view_tree)
                history_view_trees = history_view_trees + [droidbot_view_tree_root]
                if len(history_view_trees) > 4:
                    history_view_trees = history_view_trees[1:]
                # convert action to event
                if action == 0 and 180 <= pos[0] <= 540 and 2392 <= pos[1] <= 2560:
                    event = {"event_type": "key", "name": "BACK"}
                else:
                    event_type = action2event_type[action]
                    event_view = view_list[get_view_id_from_pos(view_list, pos)]
                    event = {"event_type": event_type, "view": event_view}
                    if "scroll" in event_type:
                        event["event_type"] = event_type.split("_")[0]
                        event["direction"] = action2event_type[action].split("_")[1].upper()
                history_events = history_events + [event]
                if len(history_events) > 4:
                    history_events = history_events[1:]

                request_json = {
                    "history_view_trees": history_view_trees,
                    "history_events": history_events[:-1],
                    "possible_events": possible_events,
                    "screen_res": [1440, 2560]
                }

                from xmlrpc.client import ServerProxy
                proxy = ServerProxy("http://localhost:50405/")
                result = json.loads(proxy.predict(json.dumps(request_json)))

                for i, idx in enumerate(result["indices"]):
                    if is_events_equal(view_list, possible_events[idx], action, pos):
                        accuracy_tuples.append((i + 1, len(possible_events)))

                count += 1
                # print(selected_event)
                # print(action, pos)
    with open("validation_result.txt", "w") as f:
        f.writelines(["%d\t%d" % (x[0], x[1]) + os.linesep for x in accuracy_tuples])

def parse_args():
    parser = argparse.ArgumentParser(description="Humanoid training script")
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
