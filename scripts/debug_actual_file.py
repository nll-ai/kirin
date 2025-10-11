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


def debug_actual_file():
    """Debug the actual file that was written."""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temp directory: {temp_dir}")

        # Create dataset
        ds = Dataset(root_dir=temp_dir, dataset_name="test_debug")
        print(f"Dataset directory: {ds.dataset_dir}")

        # Create first commit
        print("Creating first commit...")
        commit_hash = ds.commit(commit_message="test commit", add_files=dummy_file())
        print(f"Commit hash: {commit_hash}")

        # Check the actual file that was written
        commit_json_path = f"{ds.dataset_dir}/{commit_hash}/commit.json"
        print(f"Commit json path: {commit_json_path}")

        # Read the actual file
        with ds.fs.open(commit_json_path, "r") as f:
            actual_content = f.read()
            print(f"Actual file content: {actual_content}")

            # Try to parse it
            try:
                parsed = json.loads(actual_content)
                print(f"Successfully parsed: {parsed}")
            except Exception as e:
                print(f"Failed to parse: {e}")

                # Check if it's a repr() vs json issue
                print(f"Content type: {type(actual_content)}")
                print(f"Content length: {len(actual_content)}")
                print(f"First 100 chars: {actual_content[:100]}")


if __name__ == "__main__":
    debug_actual_file()
