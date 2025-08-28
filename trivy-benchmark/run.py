import subprocess
import os
import shlex
import time

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
            outfile = os.path.join(out_dir, f"{subdir}.out")
            cmd = f'trivy image --image-config-scanners misconfig --scanners misconfig -f json --input {dockertar}> {outfile}'
            run(cmd, shell=True)
            cmd = f'trivy fs -f json --scanners misconfig {dockerfile} >> {outfile}'
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


if __name__ == "__main__":
    main()

