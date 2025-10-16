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
    # For empty dataset, checkout should work (stay at no commit)
    if ds.current_commit is None:
        ds.checkout()  # Should not raise error for Git implementation
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
