from os import listdir
from os.path import isfile, join
import subprocess
import shlex
import time

def run(cmd, cwd=None, shell=False, executable="/bin/bash"):
    print(f"\n>>> Running: {cmd}")
    if shell:
        return subprocess.run(cmd, shell=True, check=True, cwd=cwd, executable=executable)
    else:
        return subprocess.run(shlex.split(cmd), check=True, cwd=cwd, executable=executable)

def get_filelist(path: str):
    return [join(path, f) for f in listdir(path) if isfile(join(path, f))]

def run_hadolint(filelist):
    start = time.time()
    for f in filelist:
        try:
            run(f'hadolint {f}', shell=True)
        except KeyboardInterrupt:
            return
        except:
            pass
    return time.time() - start

def run_whale_watcher(filelist):
    start = time.time()
    for f in filelist:
        try:
            run(f'WHALE_WATCHER_TARGET_DOCKERFILE="{f}" whale-watcher validate ./ruleset.yaml', shell=True)
        except KeyboardInterrupt:
            return
        except:
            pass
    return time.time() -start

if __name__ == "__main__":
    files = get_filelist("./deduplicated-sources-gold/")
    hado = run_hadolint(filelist=files)
    ww = run_whale_watcher(filelist=files)
    print(f"hado: {hado}")
    print(f"ww: {ww}")
