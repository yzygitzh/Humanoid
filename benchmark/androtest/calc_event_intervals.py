from datetime import datetime
import os
import subprocess
import sys

root_path = "/mnt/FAST_volume/lab_data/AndroTest"

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    out_id = sys.argv[1]
    result_path = os.path.join(root_path, out_id)

    with open("app_list.txt", "r") as f:
        app_list = [x[:-len(os.linesep)] for x in f.readlines()]

    intervals = []
    for app_dir in app_list:
        event_dir = os.path.join(result_path, app_dir, "droidbot_out", "events")
        if os.path.exists(event_dir):
            event_tags = sorted([datetime.strptime(x[len("event_"):-len(".json")], "%Y-%m-%d_%H%M%S")
                                 for x in next(os.walk(event_dir))[2]], reverse=True)
            for tag2, tag1 in zip(event_tags[:-1], event_tags[1:]):
                intervals.append((tag2 - tag1).total_seconds())
    print(sum(intervals) / len(intervals))

