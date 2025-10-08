# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.1",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import tempfile
import os
import json
from pathlib import Path
from kirin import Dataset
from kirin.testing_utils import dummy_file
from kirin.utils import strip_protocol


def debug_commit_json():
    """Debug the commit.json file content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temp directory: {temp_dir}")

        # Create dataset
        ds = Dataset(root_dir=temp_dir, dataset_name="test_debug")
        print(f"Dataset directory: {ds.dataset_dir}")

        # Create first commit
        print("Creating first commit...")
        commit_hash = ds.commit(commit_message="test commit", add_files=dummy_file())
        print(f"Commit hash: {commit_hash}")

        # Check the glob pattern
        glob_pattern = f"{strip_protocol(ds.dataset_dir)}/*/commit.json"
        print(f"Glob pattern: {glob_pattern}")

        # Try the glob
        try:
            jsons = ds.fs.glob(glob_pattern)
            print(f"Glob results: {jsons}")

            # Read the first commit file
            if jsons:
                first_commit_file = jsons[0]
                print(f"\nReading commit file: {first_commit_file}")

                with ds.fs.open(first_commit_file, "r") as f:
                    content = f.read()
                    print(f"Raw content: {content}")

                    data = json.loads(content)
                    print(f"Parsed data: {data}")
                    print(f"Version hash: {data.get('version_hash')}")

        except Exception as e:
            print(f"Error: {e}")

        # Now try _get_commits_data
        print("\nTrying _get_commits_data...")
        try:
            commits_data = ds._get_commits_data()
            print(f"Commits data: {commits_data}")
            print(f"Number of commits: {len(commits_data)}")
        except Exception as e:
            print(f"Error in _get_commits_data: {e}")


if __name__ == "__main__":
    debug_commit_json()
