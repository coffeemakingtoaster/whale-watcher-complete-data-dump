import subprocess
import os
import shlex
from parse import parse_hits, print_rule_hits
import shutil

def copy_dataset_to_binnacle(): 
    src_dir = "./scraper/testdata"
    dst_dir = "./binnacle/datasets/deduplicated-sources"

    # Ensure destination exists
    os.makedirs(dst_dir, exist_ok=True)

    for subdir in os.listdir(src_dir):
        subdir_path = os.path.join(src_dir, subdir)
        if os.path.isdir(subdir_path):
            # Expect exactly one file inside
            dockerfile = os.path.join(subdir_path, "Dockerfile")
            if not os.path.exists(dockerfile):
                print(f"⚠️ Skipping {subdir_path}, no dockerfile found")
                continue
            src_file = os.path.join(dockerfile)
            dst_file = os.path.join(dst_dir, f"{subdir}.Dockerfile")
            shutil.copy(src_file, dst_file)
            print(f"Copied {src_file} → {dst_file}")

    run(f"tar -cf - {dst_dir}/ | xz -z -9 > ./binnacle/datasets/0b-deduplicated-dockerfile-sources/gold.tar.xz", executable='/bin/sh', shell=True)


def run_whale_watcher():
    src_dir = "./scraper/testdata"
    out_dir = "./ww_out"

    os.makedirs(out_dir, exist_ok=True)

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


def run_binnacle_data_pipeline():
    cwd = "./binnacle/datasets"

    # Deduplication loop
    cmd = r'''
        /bin/bash ./1-phase-1-dockerfile-asts/generate.sh
        /bin/bash ./2-phase-2-dockerfile-asts/generate.sh
        /bin/bash ./3-phase-3-dockerfile-asts/generate.sh
        /bin/bash ./4-abstracted-asts/generate.sh
    '''
    run(cmd, cwd=cwd, shell=True)


def run(cmd, cwd=None, shell=False, executable="/bin/bash"):
    print(f"\n>>> Running: {cmd}")
    if shell:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, executable=executable)
    else:
        subprocess.run(shlex.split(cmd), check=True, cwd=cwd, executable=executable)


def main():
    print("Preparing data")

#    run("sh ./setup.sh", cwd="./scraper")

    print("Patching binnacle")

    try:
        run("git apply ../binnacle.patch", cwd="./binnacle", shell=True)
    except:
        print("git apply failed, this does not necessarily mean failure")


    print("Rebuilding archives for binnacle")

    copy_dataset_to_binnacle()

    run_binnacle_data_pipeline()

    print("Running binnacle")

    run('/bin/bash run.sh',
        shell=True,
        cwd='./binnacle/experiments/3-static-rule-enforcement',
    )

    shutil.copy("./binnacle/experiments/3-static-rule-enforcement/experiment/results-gold-summary.txt", './out/results-gold-summary.txt')

    print("Run whalewatcher")

    run_whale_watcher()

    res = parse_hits()

    print_rule_hits(res)

if __name__ == "__main__":
    main()

