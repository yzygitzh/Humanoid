import os
import subprocess
import sys

result_dir = sys.argv[1]
coverage_dict = {}
for package_name in next(os.walk(result_dir))[1]:
    coverage_path = os.path.join(result_dir, package_name, "activity_coverage")
    with open(coverage_path, "r") as f:
        activities = set([x.split()[5] for x in f.readlines() if "Hist" in x])

    with open(os.path.join("activities", "%s.txt" % (package_name)), "r") as f:
        total_activities = set([x.strip() for x in f.readlines()])

    hit_activities = 0
    for activity in activities:
        if activity in total_activities or \
           activity.replace("/", "") in total_activities or \
           activity.split("/")[1] in total_activities:
            hit_activities += 1
    coverage_dict[package_name] = hit_activities / len(total_activities)

for package_name in sorted(coverage_dict):
    if coverage_dict[package_name] > .0:
        print("%s\t%g" % (package_name, coverage_dict[package_name]))
    else:
        print(package_name)

