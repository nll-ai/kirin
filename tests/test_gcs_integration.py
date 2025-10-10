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
        fs.ls("gitdata-test-bucket")
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
    ds = Dataset(root_dir="gs://gitdata-test-bucket", name="test")
    assert ds.name == "test"
    assert "gs://gitdata-test-bucket" in ds.root_dir


def test_gcs_dataset_commit():
    """Test committing files to GCS."""
    # Create a temporary local file to commit
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test data for GCS")
        temp_file = f.name

    try:
        # Create dataset
        ds = Dataset(root_dir="gs://gitdata-test-bucket", name="test-commit")

        # Commit the file
        ds.commit(commit_message="Test commit to GCS", add_files=[temp_file])

        # Verify the file is in the dataset
        file_dict = ds.file_dict
        assert len(file_dict) == 1
        filename = Path(temp_file).name
        assert filename in file_dict

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
        ds = Dataset(root_dir="gs://gitdata-test-bucket", name="test-checkout")

        # First commit
        ds.commit(commit_message="First commit", add_files=[temp_file1])
        first_version = ds.current_version_hash()

        # Second commit
        ds.commit(commit_message="Second commit", add_files=[temp_file2])
        second_version = ds.current_version_hash()

        assert first_version != second_version

        # Checkout first version
        ds.checkout(first_version)
        assert ds.current_version_hash() == first_version
        assert len(ds.file_dict) == 1

        # Checkout second version
        ds.checkout(second_version)
        assert ds.current_version_hash() == second_version
        assert len(ds.file_dict) == 2

    finally:
        # Clean up local temp files
        os.unlink(temp_file1)
        os.unlink(temp_file2)


def test_gcs_dataset_metadata():
    """Test reading metadata from GCS dataset."""
    ds = Dataset(
        root_dir="gs://gitdata-test-bucket",
        name="test-metadata",
        description="Test dataset for metadata",
    )

    metadata = ds.metadata()
    assert metadata["name"] == "test-metadata"
    assert metadata["description"] == "Test dataset for metadata"


@pytest.mark.parametrize(
    "name", ["test", "test-commit", "test-checkout", "test-metadata"]
)
def test_gcs_dataset_reopen(name):
    """Test that we can reopen existing GCS datasets."""
    # This should not raise an error even if the dataset exists
    ds = Dataset(root_dir="gs://gitdata-test-bucket", name=name)
    assert ds.name == name
    # Should be able to get metadata
    metadata = ds.metadata()
    assert "name" in metadata
