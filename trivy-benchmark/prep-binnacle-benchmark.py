import subprocess
import os
import shlex

def run_whale_watcher():
    return
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

def run_trivy():
    src_dir = "./scraper/testdata"
    out_dir = "./trivy_out"

    os.makedirs(out_dir, exist_ok=True)

    for subdir in os.listdir(src_dir):
        subdir_path = os.path.join(src_dir, subdir)
        if os.path.isdir(subdir_path):
            # Expect exactly one file inside
            dockertar = os.path.join(subdir_path, "docker.tar")
            if not all([os.path.exists(f) for f in [dockertar]]):
                print(f"⚠️ Skipping {subdir_path}, needed files incomplete")
                continue
            outfile = os.path.join(out_dir, f"{subdir}.out")
            cmd = f'trivy image --scanners misconfig --input {dockertar}> {outfile}'
            run(cmd, shell=True)



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

    run_whale_watcher()

    run_trivy()

if __name__ == "__main__":
    main()

