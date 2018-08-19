import os
import subprocess
import sys

root_path = "/home/yzy/humanoid/"

if __name__ == "__main__":
    out_id = sys.argv[1]
    result_path = os.path.join(root_path, out_id)
    app_dirs = next(os.walk(result_path))[1]

    with open("app_list.txt", "r") as f:
        app_list = [x[:-len(os.linesep)] for x in f.readlines()]

    total_event_time = 0
    total_event_num = 0
    for app_dir in app_list:
        print(app_dir)
        event_time = 0
        event_num = 0

        # calc event time
        act_cov_path = os.path.join(result_path, app_dir, "activity_coverage")
        if not os.path.exists(act_cov_path):
            continue
        with open(act_cov_path, "r") as act_cov_f:
            lines = reversed(act_cov_f.readlines())
            for line in lines:
                if "Hist" not in line:
                    event_time = int(line)
                    break

        # calc event num
        if not ("droidbot" in out_id or "humanoid" in out_id):
            log_dir = os.path.join(result_path, app_dir, "%s.log" % out_id.split("_")[1])
            if not os.path.exists(log_dir):
                continue
            with open(log_dir, "r") as log_f:
                log_lines = log_f.readlines()

        if "droidbot" in out_id or "humanoid" in out_id:
            event_dir = os.path.join(result_path, app_dir, "droidbot_out", "events")
            if not os.path.exists(event_dir):
                continue
            event_num = len(next(os.walk(event_dir))[2])
        elif "stoat" in out_id:
            for line in log_lines:
                if "Iteration: " in line:
                    event_num += 1
        elif "droidmate" in out_id:
            for line in log_lines:
                if "<ExplAct " in line:
                    event_num += 1
        elif "puma" in out_id:
            for line in log_lines:
                if "--- iter" in line or "Restarting app" in line or "Repalying" in line or "force_stop" in  line:
                    event_num += 1
        elif "monkey" in out_id:
            line_set = set()
            for line in log_lines:
                if "Sending event" in line:
                    line_set.add(line)
                elif "Events injected" in line:
                    event_num = 10000
            if event_num < 10000:
                event_num = len(line_set) * 100

        if event_num != 0 and event_time != 0 and (event_time / event_time < 20):
            total_event_num += event_num
            total_event_time += event_time
    print(total_event_num / total_event_time)
