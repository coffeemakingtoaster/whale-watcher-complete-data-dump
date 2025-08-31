from os import listdir, makedirs
from os.path import isfile, join, basename
import subprocess
import shlex
import time
from collections import defaultdict
import json

def parse_hado():
    violation_results = defaultdict(lambda: 0)
    all_files = get_filelist("./hado_out/")
    for file in all_files:
        with open(file) as f:
            data = json.load(f)
        for entry in data:
            key = entry["code"]
            violation_results[key] += 1

    return violation_results

def parse_ww():
    violation_results = defaultdict(lambda: 0)
    all_files = get_filelist("./ww_out/")
    for file in all_files:
        with open(file) as f:
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

def run(cmd, cwd=None, shell=False, executable="/bin/bash"):
    #print(f"\n>>> Running: {cmd}")
    if shell:
        return subprocess.run(cmd, shell=True, check=True, cwd=cwd, executable=executable)
    else:
        return subprocess.run(shlex.split(cmd), check=True, cwd=cwd, executable=executable)

def get_filelist(path: str):
    return [join(path, f) for f in listdir(path) if isfile(join(path, f))]

def run_hadolint(filelist):
    print(f"Running hado ({len(filelist)}) files so this may take a bit...")
    out_dir = "./hado_out"

    makedirs(out_dir, exist_ok=True)

    start = time.time()
    for dockerfile in filelist:
        outfile = join(out_dir, f"{basename(dockerfile)}.out")
        run(f'hadolint -f json --no-fail {dockerfile}> {outfile}', shell=True)
    return time.time() - start

def run_whale_watcher(filelist):
    print(f"Running whale watcher ({len(filelist)}) files so this may take a bit...")

    out_dir = "./ww_out"

    makedirs(out_dir, exist_ok=True)

    start = time.time()

    for dockerfile in filelist:
        outfile = join(out_dir, f"{basename(dockerfile)}.out")
        cmd = f'WHALE_WATCHER_TARGET_DOCKERFILE="{dockerfile}" whale-watcher validate ./ruleset.yaml > {outfile}'
        run(cmd, shell=True)

    return time.time() - start

if __name__ == "__main__":
    files = get_filelist("./dataset/")
    hado = run_hadolint(filelist=files)
    ww = run_whale_watcher(filelist=files)
    print(f"hado: {hado}")
    print(f"ww: {ww}")
    ww_results = parse_ww()
    hado_results = parse_hado()

    for key in set(list(hado_results.keys()) + list(ww_results.keys())):
        print(f"ID:{key}\tTrivy: {hado_results[key]}\tWW: {ww_results[key]}")

