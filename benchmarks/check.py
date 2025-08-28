import json
from collections import defaultdict

with open("./gold_index.json") as f:
    data = json.load(f)

overview = defaultdict(lambda: 0)

for entry in data:
    overview[entry["repo_full_name"]] = entry

for key in overview.keys():
    item = overview[key]
    print(f"Repo={item['file_url']} Date={item['file_contents_scraped_at']}")
