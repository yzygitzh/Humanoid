import os
import subprocess
import sys

root_path = "/mnt/FAST_volume/lab_data/AndroTest"
app_path = os.path.join(root_path, "apps")
em_path = os.path.join(root_path, "em")

def get_cov(app_dir, time_id):
    app_id = app_dir.split(os.path.sep)[0]
    ec_path = os.path.join(result_path, app_dir,
                           "coverage.ec%s" % ("" if time_id is None else "." + str(time_id)))
    if not os.path.exists(ec_path):
        return None
    subprocess.Popen(["rm", "-r", "coverage/"])
    emma_cmd = "java -cp emma.jar emma report -r html -in %s -in %s/bin/coverage.em" % \
               (ec_path, os.path.join(em_path, app_id))
    p = subprocess.Popen(emma_cmd.split())
    p.wait()
    if not os.path.exists(os.path.join("coverage", "index.html")):
        return None
    with open("coverage/index.html", "rb") as f:
        try:
           cov_tuple = f.read().decode("cp1252").split("%")[13].split("<")[0].strip().split("/")
           cov = float(cov_tuple[0][1:]) / float(cov_tuple[1][:-1])
           return cov
        except:
           return None

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    out_id = sys.argv[1]
    out_tool = sys.argv[2]
    events_per_min = float(sys.argv[3])
    result_path = os.path.join(root_path, out_id, out_tool)
    out_file = os.path.join("out", "%s.txt" % out_tool)

    with open("app_list.txt", "r") as f:
        app_list = [x[:-len(os.linesep)] for x in f.readlines()]
    with open("package_order.txt", "r") as f:
        package_order = [x[:-len(os.linesep)] for x in f.readlines()]
    with open("stat_map.txt", "r") as f:
        stat_map_tuples = [x[:-len(os.linesep)].split() for x in f.readlines()]
        id_package_map = {x[0]: x[1] for x in stat_map_tuples}
        package_cov_map = {}

    result_ids = next(os.walk(result_path))[1]

    for app_dir in app_list:
        app_id = app_dir.split(os.path.sep)[0]
        cov_list = [0.0]
        last_cov = 0.0
        last_time_id = -1
        for event_num in range(10, 610, 10):
            time_id = int(event_num / events_per_min)
            if time_id > last_time_id:
                cov = get_cov(app_dir, time_id)
            else:
                cov = last_cov
            cov_list.append(cov if cov is not None else last_cov)
            last_cov = cov if cov is not None else last_cov
            last_time_id = time_id

        if sum(cov_list) > 1e-5:
            while cov_list[1] < 1e-5:
                cov_list = cov_list[1:] + [cov_list[-1]]
            package_cov_map[id_package_map[app_id]] = cov_list
        else:
            package_cov_map[id_package_map[app_id]] = []

    with open(out_file, "w") as f:
        f.writelines(["\t".join([x] + [str(y) for y in package_cov_map[x]]) + \
                      os.linesep for x in package_order])
