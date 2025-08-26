
import subprocess
import os
import shlex
from parse import parse_hits
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
            src_file = os.path.join(dockerfile)
            dst_file = os.path.join(dst_dir, f"{subdir}.Dockerfile")
            shutil.copy(src_file, dst_file)
            print(f"Copied {src_file} → {dst_file}")

    run(f"tar -cf - {dst_dir}/ | xz -z -9 > ./binnacle/datasets/0b-deduplicated-dockerfile-sources/gold.tar.xz", executable='/bin/sh', shell=True)

def run_binnacle_data_pipeline():
    cwd = "./binnacle/datasets"

    # Deduplication loop
    cmd = r'''
        sh ./1-phase-1-dockerfile-asts/generate.sh
        sh ./2-phase-2-dockerfile-asts/generate.sh
        sh ./3-phase-3-dockerfile-asts/generate.sh
        sh ./4-abstracted-asts/generate.sh
    '''
    run(cmd, cwd=cwd, shell=True)



def run(cmd, cwd=None, shell=False, executable="/bin/bash"):
    print(f"\n>>> Running: {cmd}")
    if shell:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, executable=executable)
    else:
        subprocess.run(shlex.split(cmd), check=True, cwd=cwd, executable=executable)

def main():
    print("Preparing binnacle image...")

    run("docker build -t binnacle/artifact:experiment-3 -f ./binnacle.Dockerfile ./binnacle/experiments/3-static-rule-enforcement/experiment", shell=True)

    print("Preparing data")

    #run("sh ./setup.sh", cwd="./scraper")

    print("Rebuilding archives for binnacle")

    copy_dataset_to_binnacle()

    run_binnacle_data_pipeline()

    exit(1)

    print("Running binnacle")

    run(
        'docker run -it --rm -v "./binnacle/datasets:/datasets" -v "./out:/out" binnacle/artifact:experiment-3 /datasets/4-abstracted-asts/gold.jsonl.xz gold',
        shell=True
    )

    run("tar -xvJf ./binnacle/datasets/0a-original-dockerfile-sources/gold.tar.xz")

    print("Run whalewatcher")

    sources_gold = "./sources-gold"
    for fname in os.listdir(sources_gold):
        if fname.endswith(".Dockerfile"):
            fpath = os.path.join(sources_gold, fname)
            print(fpath)
            cmd = f'WHALE_WATCHER_TARGET_DOCKERFILE="{fpath}" whale-watcher validate ./ruleset.yaml > {fpath}.out'
            run(cmd, shell=True)


    parse_hits()

if __name__ == "__main__":
    main()

