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

import json
import tempfile

from kirin import Dataset
from kirin.testing_utils import dummy_file


def debug_json_writing():
    """Debug the JSON writing process."""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temp directory: {temp_dir}")

        # Create dataset
        ds = Dataset(root_dir=temp_dir, dataset_name="test_debug")
        print(f"Dataset directory: {ds.dataset_dir}")

        # Create first commit
        print("Creating first commit...")
        commit_hash = ds.commit(commit_message="test commit", add_files=dummy_file())
        print(f"Commit hash: {commit_hash}")

        # Check the current commit's to_dict method
        current_commit = ds.current_commit
        print(f"Current commit: {current_commit}")
        print(f"Current commit type: {type(current_commit)}")

        # Check the to_dict method
        commit_dict = current_commit.to_dict()
        print(f"Commit dict: {commit_dict}")

        # Check json.dumps
        json_str = json.dumps(commit_dict)
        print(f"JSON string: {json_str}")

        # Try to parse it back
        try:
            parsed = json.loads(json_str)
            print(f"Parsed back: {parsed}")
        except Exception as e:
            print(f"Error parsing back: {e}")


if __name__ == "__main__":
    debug_json_writing()
