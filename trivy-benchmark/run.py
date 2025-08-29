import subprocess
import os
import shlex
import time
from collections import defaultdict
import json

def parse_trivy():
    violation_results = defaultdict(lambda: 0)
    all_files = os.listdir("./trivy_out/")
    for res in all_files:
        filepath = os.path.join("./trivy_out/", res)
        with open(filepath) as f:
            data = json.load(f)
        if not "Results" in data:
            continue
        results = data["Results"]
        for entry in results:
            if entry["MisconfSummary"]["Failures"] == 0:
                continue
            for violation in entry["Misconfigurations"]:
                key = violation["Title"]
                violation_results[key] += 1

    return violation_results

def parse_ww():
    violation_results = defaultdict(lambda: 0)
    all_files = os.listdir("./ww_out/")
    for res in all_files:
        filepath = os.path.join("./ww_out/", res)
        with open(filepath) as f:
            lines = f.readlines()
        for line in lines:
            if not "ruleId=" in line:
                continue
            line = line.strip()
            ind = line.find("ruleId=")
            line = line[ind:]
            line = line.lstrip("ruleId=")
            rule_id = line.replace('"', "")
            violation_results[rule_id] += 1
        
    return violation_results

def run_whale_watcher():
    src_dir = "./scraper/testdata"
    out_dir = "./ww_out"

    os.makedirs(out_dir, exist_ok=True)

    start = time.time()

    for subdir in os.listdir(src_dir):
        subdir_path = os.path.join(src_dir, subdir)
        if os.path.isdir(subdir_path):
            # Expect exactly one file inside
            dockerfile = os.path.join(subdir_path, "Dockerfile")
            dockertar = os.path.join(subdir_path, "docker.tar")
            ocitar = os.path.join(subdir_path, "oci.tar")
            if not all([os.path.exists(f) for f in [dockerfile, dockertar, ocitar]]):
                print(f"⚠️ Skipping {subdir_path}, needed files incomplete")
                continue
            outfile = os.path.join(out_dir, f"{subdir}.out")
            cmd = f'WHALE_WATCHER_TARGET_DOCKERFILE="{dockerfile}" WHALE_WATCHER_TARGET_DOCKER_PATH="{dockertar}" WHALE_WATCHER_TARGET_OCI_PATH="{ocitar}" whale-watcher validate ./ruleset.yaml > {outfile}'
            run(cmd, shell=True)

    return time.time() - start

def run_trivy():
    src_dir = "./scraper/testdata"
    out_dir = "./trivy_out"

    os.makedirs(out_dir, exist_ok=True)

    start = time.time()

    for subdir in os.listdir(src_dir):
        subdir_path = os.path.join(src_dir, subdir)
        if os.path.isdir(subdir_path):
            # Expect exactly one file inside
            dockertar = os.path.join(subdir_path, "docker.tar")
            dockerfile = os.path.join(subdir_path, "Dockerfile")
            if not all([os.path.exists(f) for f in [dockertar]]):
                print(f"⚠️ Skipping {subdir_path}, needed files incomplete")
                continue
            outfile_image = os.path.join(out_dir, f"{subdir}_image.out")
            outfile_dockerfile = os.path.join(out_dir, f"{subdir}_dockerfile.out")
            cmd = f'trivy image -q --image-config-scanners misconfig --scanners misconfig -f json --input {dockertar} -o {outfile_image}'
            run(cmd, shell=True)
            cmd = f'trivy fs -f json --scanners misconfig {dockerfile} -o {outfile_dockerfile}'
            run(cmd, shell=True)

    return time.time() - start


def run(cmd, cwd=None, shell=False, executable="/bin/bash"):
    print(f"\n>>> Running: {cmd}")
    if shell:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, executable=executable)
    else:
        subprocess.run(shlex.split(cmd), check=True, cwd=cwd, executable=executable)


def main():
    print("Preparing data")

#    run("sh ./setup.sh", cwd="./scraper")

    print("Run whalewatcher")

    duration_ww = run_whale_watcher()

    duration_trivy = run_trivy()

    print(f"ww: {duration_ww}")
    print(f"trivy: {duration_trivy}")

    trivy_res = parse_trivy()
    ww_res = parse_ww()

    for key in set(list(trivy_res.keys()) + list(ww_res.keys())):
        print(f"ID:{key}\tTrivy: {trivy_res[key]}\tWW: {ww_res[key]}")


if __name__ == "__main__":
    main()

