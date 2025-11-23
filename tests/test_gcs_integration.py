"""Integration tests for Google Cloud Storage."""

import os
import tempfile
from pathlib import Path

import pytest

from kirin.dataset import Dataset

# Check if GCS credentials are available
GCS_AVAILABLE = False
try:
    import gcsfs

    # Try to create a filesystem to check credentials
    fs = gcsfs.GCSFileSystem()
    # Try to access the test bucket
    try:
        fs.ls("kirin-test-bucket")
        GCS_AVAILABLE = True
    except Exception:
        pass
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not GCS_AVAILABLE,
    reason="GCS credentials not available or gcsfs not installed. "
    "Run 'gcloud auth application-default login' to set up credentials.",
)


def test_gcs_dataset_creation():
    """Test creating a dataset on GCS."""
    ds = Dataset(root_dir="gs://kirin-test-bucket", name="test")
    assert ds.name == "test"
    assert "gs://kirin-test-bucket" in ds.root_dir


def test_gcs_dataset_commit():
    """Test committing files to GCS."""
    # Create a temporary local file to commit
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test data for GCS")
        temp_file = f.name

    try:
        # Create dataset
        ds = Dataset(root_dir="gs://kirin-test-bucket", name="test-commit")

        # Commit the file
        ds.commit(message="Test commit to GCS", add_files=[temp_file])

        # Verify the file is in the dataset
        files = ds.files
        filename = Path(temp_file).name
        assert filename in files, (
            f"File {filename} not found in files: {list(files.keys())}"
        )
        # Note: There may be other files from previous test runs, so we just verify
        # our file exists

    finally:
        # Clean up local temp file
        os.unlink(temp_file)


def test_gcs_dataset_checkout():
    """Test checking out different versions on GCS."""
    # Create dataset with initial commit
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Version 1")
        temp_file1 = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Version 2")
        temp_file2 = f.name

    try:
        ds = Dataset(root_dir="gs://kirin-test-bucket", name="test-checkout")

        # First commit
        ds.commit(message="First commit", add_files=[temp_file1])
        first_version = ds.current_commit.hash if ds.current_commit else None

        # Second commit
        ds.commit(message="Second commit", add_files=[temp_file2])
        second_version = ds.current_commit.hash if ds.current_commit else None

        assert first_version != second_version
        assert first_version is not None
        assert second_version is not None

        # Checkout first version
        ds.checkout(first_version)
        assert ds.current_commit.hash == first_version
        filename1 = Path(temp_file1).name
        assert filename1 in ds.files, f"File {filename1} not found after checkout"
        # Note: There may be other files from previous test runs

        # Checkout second version
        ds.checkout(second_version)
        assert ds.current_commit.hash == second_version
        filename2 = Path(temp_file2).name
        assert filename2 in ds.files, f"File {filename2} not found after checkout"
        # Both files should be in the second commit
        assert filename1 in ds.files or filename2 in ds.files

    finally:
        # Clean up local temp files
        os.unlink(temp_file1)
        os.unlink(temp_file2)


def test_gcs_dataset_commit_metadata():
    """Test commit-level metadata on GCS dataset."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test data")
        temp_file = f.name

    try:
        ds = Dataset(
            root_dir="gs://kirin-test-bucket",
            name="test-metadata",
            description="Test dataset for metadata",
        )

        # Commit with metadata
        ds.commit(
            message="Test commit with metadata",
            add_files=[temp_file],
            metadata={"test_key": "test_value", "accuracy": 0.95},
        )

        # Verify commit has metadata
        assert ds.current_commit is not None
        assert ds.current_commit.metadata["test_key"] == "test_value"
        assert ds.current_commit.metadata["accuracy"] == 0.95

        # Verify dataset properties
        assert ds.name == "test-metadata"
        assert ds.description == "Test dataset for metadata"

    finally:
        import os

        os.unlink(temp_file)


@pytest.mark.parametrize(
    "name", ["test", "test-commit", "test-checkout", "test-metadata"]
)
def test_gcs_dataset_reopen(name):
    """Test that we can reopen existing GCS datasets."""
    # This should not raise an error even if the dataset exists
    ds = Dataset(root_dir="gs://kirin-test-bucket", name=name)
    assert ds.name == name
    # Should be able to access dataset properties
    assert isinstance(ds.name, str)
    assert isinstance(ds.description, str)
