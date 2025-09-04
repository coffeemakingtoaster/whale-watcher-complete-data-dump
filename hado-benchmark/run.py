from os import listdir, makedirs
from os.path import exists, isfile, join, basename
import subprocess
import shlex
import time
from collections import defaultdict
import json
import re
from tqdm import tqdm

relevant_ids = [
    "DL3000",
    "DL3004",
    "DL3011",
    "DL3012",
    "DL3020",
    "DL3021",
    "DL3023",
    "DL3024",
    "DL3026",
    "DL3043",
    "DL3044",
    "DL4000",
    "DL4004",
]

def convert_to_dataset_file(path: str) -> str:
    path = path.replace("ww_out", "dataset")
    path = path.replace("hado_out", "dataset")
    return path.rstrip(".out")

def parse_hado():
    violation_results = defaultdict(lambda: set())
    all_files = get_filelist("./hado_out/")
    for file in tqdm(all_files, desc="Hadolint parse"):
        with open(file) as f:
            data = json.load(f)
        for entry in data:
            key = entry["code"]
            violation_results[key].add(convert_to_dataset_file(file))

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
                violation_results[rule_id].add(convert_to_dataset_file(file))

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
    for dockerfile in tqdm(filelist, desc="Hadolint run"):
        outfile = join(out_dir, f"{basename(dockerfile)}.out")
        run(f'hadolint -f json --no-fail {dockerfile}> {outfile}', shell=True)
    return time.time() - start

def run_whale_watcher(filelist):
    print(f"Running whale watcher ({len(filelist)}) files so this may take a bit...")

    out_dir = "./ww_out"

    makedirs(out_dir, exist_ok=True)

    start = time.time()

    for dockerfile in tqdm(filelist, desc="Hadolint run"):
        outfile = join(out_dir, f"{basename(dockerfile)}.out")
        cmd = f'WHALE_WATCHER_TARGET_DOCKERFILE="{dockerfile}" whale-watcher validate ./ruleset.yaml > {outfile}'
        run(cmd, shell=True)

    return time.time() - start

if __name__ == "__main__":
    if exists("./ww_out/") and exists("./hado_out/"):
        print("Skipping benchmark execution, outputs already present")
    else:
        files = get_filelist("./dataset/")
        hado = run_hadolint(filelist=files)
        ww = run_whale_watcher(filelist=files)
        print(f"hado: {hado}")
        print(f"ww: {ww}")
    ww_results = parse_ww()
    hado_results = parse_hado()

    for key in relevant_ids:
        print(f"ID:{key}\tHado: {len(hado_results[key])}\tWW: {len(ww_results[key])}")
