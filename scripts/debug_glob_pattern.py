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
from pathlib import Path
from kirin import Dataset
from kirin.testing_utils import dummy_file
from kirin.utils import strip_protocol


def debug_glob_pattern():
    """Debug the glob pattern used in _get_commits_data."""
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
        except Exception as e:
            print(f"Glob error: {e}")

        # Try alternative patterns
        alt_patterns = [
            f"{ds.dataset_dir}/*/commit.json",
            f"{strip_protocol(ds.dataset_dir)}/*/commit.json",
            f"{ds.dataset_dir}/**/commit.json",
            f"{strip_protocol(ds.dataset_dir)}/**/commit.json",
        ]

        for pattern in alt_patterns:
            try:
                results = ds.fs.glob(pattern)
                print(f"Pattern '{pattern}': {results}")
            except Exception as e:
                print(f"Pattern '{pattern}' error: {e}")


if __name__ == "__main__":
    debug_glob_pattern()
