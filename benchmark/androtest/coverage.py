import os
import subprocess
import sys

root_path = "/mnt/FAST_volume/lab_data/AndroTest"
app_path = os.path.join(root_path, "apps")
em_path = os.path.join(root_path, "em")

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    out_id = sys.argv[1]
    out_tool = sys.argv[2]
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
        if not os.path.exists(os.path.join(result_path, app_dir, "coverage.ec")):
            package_cov_map[id_package_map[app_id]] = ""
            continue
        subprocess.Popen(["rm", "-r", "coverage/"])
        emma_cmd = "java -cp emma.jar emma report -r html -in %s/coverage.ec -in %s/bin/coverage.em" % \
                   (os.path.join(result_path, app_dir), os.path.join(em_path, app_id))
        p = subprocess.Popen(emma_cmd.split())
        p.wait()
        if not os.path.exists(os.path.join("coverage", "index.html")):
            package_cov_map[id_package_map[app_id]] = ""
            continue
        with open("coverage/index.html", "rb") as f:
            cov_tuple = f.read().decode("cp1252").split("%")[13].split("<")[0].strip().split("/")
            cov = float(cov_tuple[0][1:]) / float(cov_tuple[1][:-1])
            package_cov_map[id_package_map[app_id]] = cov
            print(app_id, cov)

    with open(out_file, "w") as f:
        f.writelines([str(package_cov_map[x]) + os.linesep for x in package_order])
