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


def debug_commit_storage():
    """Debug how commits are stored."""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temp directory: {temp_dir}")

        # Create dataset
        ds = Dataset(root_dir=temp_dir, dataset_name="test_debug")
        print(f"Dataset directory: {ds.dataset_dir}")

        # Check if dataset directory exists
        print(f"Dataset dir exists: {ds.fs.exists(ds.dataset_dir)}")

        # Create first commit
        print("Creating first commit...")
        commit_hash = ds.commit(commit_message="test commit", add_files=dummy_file())
        print(f"Commit hash: {commit_hash}")

        # Check if commit directory exists
        commit_dir = f"{ds.dataset_dir}/{commit_hash}"
        print(f"Commit dir: {commit_dir}")
        print(f"Commit dir exists: {ds.fs.exists(commit_dir)}")

        # Check if commit.json exists
        commit_json_path = f"{commit_dir}/commit.json"
        print(f"Commit json path: {commit_json_path}")
        print(f"Commit json exists: {ds.fs.exists(commit_json_path)}")

        # List all files in dataset directory
        print("\nFiles in dataset directory:")
        try:
            files = ds.fs.glob(f"{ds.dataset_dir}/*")
            for file in files:
                print(f"  {file}")
        except Exception as e:
            print(f"Error listing files: {e}")

        # Try to get commits data
        print("\nTrying to get commits data...")
        try:
            commits_data = ds._get_commits_data()
            print(f"Commits data: {commits_data}")
        except Exception as e:
            print(f"Error getting commits data: {e}")

        # Try latest_version_hash
        print("\nTrying latest_version_hash...")
        try:
            latest = ds.latest_version_hash()
            print(f"Latest version hash: {latest}")
        except Exception as e:
            print(f"Error getting latest version hash: {e}")


if __name__ == "__main__":
    debug_commit_storage()
