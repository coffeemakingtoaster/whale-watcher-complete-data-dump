# Trivy benchmarks

    The script required tqdm to be installed. `python3 -m pip install -r ./requirements.txt`

Run the benchmark using 
```sh
python3 run.py
```

This will download the dataset deefined in `./scraper/sources.txt`.

## Differences

differences documented:

- DS010 (whale watcher detects one more) whale watcher is not able to parse shell as accurately
- DS013 (trivy detects one more) whale watcher is not able to parse shell as accurately
- DS025 (whale watcher detects one more) whale watcher seems to be able to catch strange edge case that trivy misses
- DS029 (trivy detects one more) whale watcher is not able to parse shell as accurately
- DS031 (trivy detects one more) whale watcher is not able to properly recreate the logic trivy uses
