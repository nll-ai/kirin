"""Tests for the kirin.dataset.Dataset class."""

from unittest.mock import Mock, patch

import pytest

from kirin.dataset import Dataset
from kirin.testing_utils import dummy_file


@pytest.fixture
def empty_dataset(tmp_path) -> Dataset:
    """Create an empty dataset.

    :param tmp_path: The path to the temporary directory.
    :return: The empty dataset.
    """
    ds = Dataset(root_dir=tmp_path, name="test_create_dataset")
    return ds


@pytest.fixture
def dataset_one_commit(empty_dataset) -> Dataset:
    """Create a dataset with one commit.

    :param empty_dataset: An empty dataset.
    :return: The dataset with one commit.
    """
    # Create the first commit
    empty_dataset.commit(message="test create dataset", add_files=[dummy_file()])
    return empty_dataset


@pytest.fixture
def dataset_two_commits(dataset_one_commit) -> Dataset:
    """Create a dataset with two commits.

    :param dataset_one_commit: A dataset with one commit.
    :return: The dataset with two commits.
    """
    dataset_one_commit.commit(message="test create dataset", add_files=[dummy_file()])
    return dataset_one_commit


def test_commit_to_empty_dataset(empty_dataset):
    """Test committing to an empty dataset.

    :param empty_dataset: An empty dataset.
    """
    assert len(empty_dataset.files) == 0
    empty_dataset.commit(message="test create dataset", add_files=[dummy_file()])
    assert len(empty_dataset.files) == 1


def test_one_commit(dataset_one_commit):
    """Test committing to a dataset with one commit.

    :param dataset_one_commit: A dataset with one commit.
    """
    assert len(dataset_one_commit.files) >= 1
    dataset_one_commit.commit(
        message="test commiting a new data file", add_files=[dummy_file()]
    )
    # Check that we're on the latest commit
    assert dataset_one_commit.current_commit.hash == dataset_one_commit.head.hash
    # Should have files from the latest commit
    assert len(dataset_one_commit.files) >= 1


def test_two_commits(dataset_two_commits):
    """Test committing to a dataset with two commits.

    :param dataset_two_commits: A dataset with two commits.
    """
    # The dataset should have files from the current commit
    assert len(dataset_two_commits.files) >= 1
    dataset_two_commits.commit(
        message="test commiting a new data file", add_files=[dummy_file()]
    )
    # Check that we're on the latest commit
    assert dataset_two_commits.current_commit.hash == dataset_two_commits.head.hash
    # Should have files from the latest commit
    assert len(dataset_two_commits.files) >= 1


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_checkout(request, ds_name):
    """Test checking out a dataset.

    :param request: The pytest request object.
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    # For empty dataset, there's no commit to checkout
    if ds.current_commit is None:
        return
    ds.checkout(ds.current_commit.hash)
    # Check that we're on the latest commit
    assert ds.current_commit.hash == ds.head.hash


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_checkout_latest(request, ds_name):
    """Test checking out the latest commit without specifying a commit hash.

    :param request: The pytest request object.
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    # For empty dataset, checkout should raise ValueError
    if ds.current_commit is None:
        with pytest.raises(ValueError, match="No commits found in dataset"):
            ds.checkout()
        return

    # For datasets with commits, checkout() should work without arguments
    ds.checkout()
    # Check that we're on the latest commit
    assert ds.current_commit.hash == ds.head.hash


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_metadata(request, ds_name):
    """Test getting metadata from a dataset.

    :param request: The pytest request object
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    # Check basic dataset properties
    assert ds.name == "test_create_dataset"
    assert ds.description == ""
    if ds.current_commit:
        assert ds.current_commit.hash is not None


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_file_dict(request, ds_name):
    """Test getting the file dictionary from a dataset.

    :param request: The pytest request object
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    file_dict = ds.files
    if ds.current_commit:
        assert len(file_dict) == len(ds.current_commit.files)
    else:
        assert len(file_dict) == 0


def test_dataset_with_aws_profile(tmp_path):
    """Test creating Dataset with AWS profile."""
    with patch("kirin.dataset.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_fs.exists.return_value = False  # No commits file exists
        mock_get_filesystem.return_value = mock_fs

        dataset = Dataset(
            root_dir="s3://bucket/path", name="test-dataset", aws_profile="test-profile"
        )

        # Verify get_filesystem was called with AWS profile
        mock_get_filesystem.assert_called_once_with(
            "s3://bucket/path",
            aws_profile="test-profile",
            gcs_token=None,
            gcs_project=None,
            azure_account_name=None,
            azure_account_key=None,
            azure_connection_string=None,
        )
        assert dataset.fs == mock_fs


def test_dataset_with_gcs_credentials(tmp_path):
    """Test creating Dataset with GCS credentials."""
    with patch("kirin.dataset.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_fs.exists.return_value = False  # No commits file exists
        mock_get_filesystem.return_value = mock_fs

        dataset = Dataset(
            root_dir="gs://bucket/path",
            name="test-dataset",
            gcs_token="/path/to/service-account.json",
            gcs_project="test-project",
        )

        # Verify get_filesystem was called with GCS credentials
        mock_get_filesystem.assert_called_once_with(
            "gs://bucket/path",
            aws_profile=None,
            gcs_token="/path/to/service-account.json",
            gcs_project="test-project",
            azure_account_name=None,
            azure_account_key=None,
            azure_connection_string=None,
        )
        assert dataset.fs == mock_fs


def test_dataset_with_azure_credentials(tmp_path):
    """Test creating Dataset with Azure credentials."""
    with patch("kirin.dataset.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_fs.exists.return_value = False  # No commits file exists
        mock_get_filesystem.return_value = mock_fs

        dataset = Dataset(
            root_dir="az://container/path",
            name="test-dataset",
            azure_account_name="test-account",
            azure_account_key="test-key",
            azure_connection_string="test-connection",
        )

        # Verify get_filesystem was called with Azure credentials
        mock_get_filesystem.assert_called_once_with(
            "az://container/path",
            aws_profile=None,
            gcs_token=None,
            gcs_project=None,
            azure_account_name="test-account",
            azure_account_key="test-key",
            azure_connection_string="test-connection",
        )
        assert dataset.fs == mock_fs


def test_dataset_backward_compatibility(tmp_path):
    """Test that existing code without auth parameters still works."""
    with patch("kirin.dataset.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_fs.exists.return_value = False  # No commits file exists
        mock_get_filesystem.return_value = mock_fs

        # Test local path (should not use any cloud auth)
        dataset = Dataset(root_dir=tmp_path, name="test-dataset")

        # Verify get_filesystem was called with None for all auth params
        mock_get_filesystem.assert_called_once_with(
            str(tmp_path),
            aws_profile=None,
            gcs_token=None,
            gcs_project=None,
            azure_account_name=None,
            azure_account_key=None,
            azure_connection_string=None,
        )
        assert dataset.fs == mock_fs


def test_dataset_with_mixed_auth_params(tmp_path):
    """Test that only relevant auth parameters are used for each protocol."""
    with patch("kirin.dataset.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_fs.exists.return_value = False  # No commits file exists
        mock_get_filesystem.return_value = mock_fs

        # Test S3 with mixed params - only AWS should be used
        dataset = Dataset(
            root_dir="s3://bucket/path",
            name="test-dataset",
            aws_profile="aws-profile",
            gcs_token="gcs-token",  # Should be ignored
            azure_account_name="azure-account",  # Should be ignored
        )

        # Verify get_filesystem was called with all params (filtering happens inside)
        mock_get_filesystem.assert_called_once_with(
            "s3://bucket/path",
            aws_profile="aws-profile",
            gcs_token="gcs-token",
            gcs_project=None,
            azure_account_name="azure-account",
            azure_account_key=None,
            azure_connection_string=None,
        )
        assert dataset.fs == mock_fs
