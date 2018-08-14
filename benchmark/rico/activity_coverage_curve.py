import os
import subprocess
import sys

root_path = "/home/yzy/humanoid/"

def get_cov(activities, total_activities):
    hit_activities = 0
    for activity in activities:
        if activity in total_activities or \
           activity.replace("/", "") in total_activities or \
           activity.split("/")[1] in total_activities:
            hit_activities += 1
    return hit_activities / len(total_activities)

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    out_id = sys.argv[1]
    events_per_sec = float(sys.argv[2])
    result_dir = os.path.join(root_path, out_id)
    out_file = os.path.join("out", "%s.txt" % out_id)
    coverage_dict = {}

    for package_name in next(os.walk(result_dir))[1]:
        print(package_name)
        coverage_path = os.path.join(result_dir, package_name, "activity_coverage")

        with open(os.path.join("activities", "%s.txt" % (package_name)), "r") as f:
            total_activities = set([x.strip() for x in f.readlines()])

        # read activities
        time_id_activities = {0: set()}
        time_id = 0
        with open(coverage_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                stripped_line = line.strip()
                if "Hist" in stripped_line:
                    activity = stripped_line.split()[5]
                    time_id_activities[time_id].add(activity)
                else:
                    old_time_id = time_id
                    time_id = int(stripped_line)
                    for i in range(old_time_id + 1, time_id + 1):
                        time_id_activities[i] = set(time_id_activities[old_time_id])
            activities = set([x.split()[5] for x in f.readlines() if "Hist" in x])

        # calc curve
        cov_list = [0.0]
        last_cov = 0.0
        for event_num in range(10, 2000, 10):
            time_id = int(event_num / events_per_sec)
            if time_id in time_id_activities:
                cov = get_cov(time_id_activities[time_id], total_activities)
            else:
                cov = last_cov
            cov_list.append(cov)
            last_cov = cov
        coverage_dict[package_name] = cov_list

    with open(out_file, "w") as f:
        f.writelines(["\t".join([x] + [str(y) for y in coverage_dict[x]]) + \
                      os.linesep for x in sorted(coverage_dict)])
