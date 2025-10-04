#!/usr/bin/env python
"""List all commits in a dataset."""

import sys
from gitdata import Dataset

if len(sys.argv) < 3:
    print("Usage: python list_commits.py <root_dir> <dataset_name>")
    sys.exit(1)

root_dir = sys.argv[1]
dataset_name = sys.argv[2]

print(f"\nListing all commits in dataset '{dataset_name}'")
print(f"Root directory: {root_dir}\n")

# Load dataset
ds = Dataset(root_dir=root_dir, dataset_name=dataset_name)

# Get filesystem and list all commit files
from gitdata.dataset import strip_protocol

dataset_path = strip_protocol(ds.dataset_dir)
jsons = ds.fs.glob(f"{dataset_path}/*/commit.json")

print(f"Found {len(jsons)} commit files:\n")

commits_data = []
for json_file in jsons:
    with ds.fs.open(json_file, "r") as f:
        import json5 as json

        data = json.loads(f.read())
        commits_data.append(data)

# Sort by finding the chain from latest to earliest
commit_dict = {c["version_hash"]: c for c in commits_data}
all_parents = {c["parent_hash"] for c in commits_data if c["parent_hash"]}
latest = None
for hash in commit_dict.keys():
    if hash not in all_parents:
        latest = hash
        break

# Traverse from latest to earliest
current = latest
index = 1
while current and current in commit_dict:
    commit = commit_dict[current]
    short_hash = current[:8]
    message = commit.get("commit_message", "(no message)")
    file_count = len(commit.get("file_hashes", []))

    print(f"{index}. {short_hash} (full: {current})")
    print(f"   Message: {message}")
    print(f"   Files: {file_count}")
    print(f"   File hashes: {commit.get('file_hashes', [])}")
    print()

    current = commit.get("parent_hash")
    if not current:
        break
    index += 1
