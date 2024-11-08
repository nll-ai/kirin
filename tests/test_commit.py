"""Tests for the DatasetCommit class."""
import tempfile
from pathlib import Path

from gitdata.dataset import DatasetCommit


def test_from_empty_commit(tmp_path):
    """Tests the DatasetCommit."""
    # A commit with an empty commit hash is an empty commit hash.
    # This is a special case.
    commit1 = DatasetCommit(root_dir=tmp_path, dataset_name="test_dataset")
    assert len(commit1._file_dict()) == 0
    assert commit1.version_hash

    # Create a dummy text file and add it into the dataset.
    content = "This is a dummy text file."
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        # Write the content to the temporary file
        temp_file.write(content)

    commit2 = commit1.create(
        commit_message="test from empty commit",
        add_files=[Path(temp_file.name)],
    )
    assert len(commit2._file_dict()) == 1
    assert commit2.version_hash != commit1.version_hash

    commit3 = commit2.create(
        commit_message="test adding from existing commit",
        remove_files=[Path(temp_file.name).name],
    )
    assert len(commit3._file_dict()) == 0
    assert commit3.version_hash != commit2.version_hash
    assert commit3.version_hash != commit1.version_hash
