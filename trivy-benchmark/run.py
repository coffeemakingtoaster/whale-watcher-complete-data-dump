import subprocess
import os
import shlex
import time
from collections import defaultdict
import json
import re
from tqdm import tqdm

def get_filelist(path: str):
    return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

def extract_source_information(path: str) -> str:
    path = path.replace("./ww_out/", "")
    path = path.replace("./trivy_out/", "")
    path = path.removesuffix("_dockerfile.out")
    path = path.removesuffix("_image.out")
    return path.removesuffix(".out")


def parse_trivy():
    violation_results = defaultdict(lambda: set())
    all_files = get_filelist("./trivy_out/")
    for filepath in all_files:
        if filepath.endswith("_image.out"):
            continue
        with open(filepath) as f:
            data = json.load(f)
        if not "Results" in data:
            continue
        results = data["Results"]
        filepath = extract_source_information(filepath)
        for entry in results:
            if entry["MisconfSummary"]["Failures"] == 0:
                continue
            for violation in entry["Misconfigurations"]:
                key = violation["ID"]
                violation_results[key].add(filepath)

    return violation_results

def parse_ww():
    violation_results = defaultdict(lambda: set())
    all_files = get_filelist("./ww_out/")

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    for file in tqdm(all_files, desc="ww parse"):
        with open(file) as f:
            lines = f.readlines()
        for line in lines:
            line = ansi_escape.sub('', line)
            title_search = re.search(r".*ruleId=([^\s]+)",line, re.IGNORECASE)
            if title_search:
                rule_id = title_search.group(1)
                violation_results[rule_id].add(extract_source_information(file))

    return violation_results

def run_whale_watcher():
    src_dir = "./scraper/testdata"
    out_dir = "./ww_out"

    if os.path.exists(out_dir):
        print("ww skipped, out dir already present")
        return 0

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

    if os.path.exists(out_dir):
        print("trivy skipped, out dir already present")
        return 0

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

    #run("sh ./setup.sh", cwd="./scraper")

    print("Run whalewatcher")

    duration_ww = run_whale_watcher()

    duration_trivy = run_trivy()

    print(f"ww: {duration_ww}")
    print(f"trivy: {duration_trivy}")

    trivy_res = parse_trivy()
    ww_res = parse_ww()

    keys = set(list(trivy_res.keys()) + list(ww_res.keys()))

    for key in sorted(list(keys)):
        # filter out kubernetes rules
        if key.startswith("KSV"):
            continue
        print(f"ID:{key}\tTrivy: {len(trivy_res[key])}\tWW: {len(ww_res[key])}")
        print([f for f in trivy_res[key] if f not in ww_res[key]])
        print([f for f in ww_res[key] if f not in trivy_res[key]])



if __name__ == "__main__":
    main()

