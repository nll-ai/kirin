"""Tests for the kirin.dataset.Dataset class."""

import pytest

from kirin.dataset import Dataset
from kirin.testing_utils import dummy_file


@pytest.fixture
def empty_dataset(tmp_path) -> Dataset:
    """Create an empty dataset.

    :param tmp_path: The path to the temporary directory.
    :return: The empty dataset.
    """
    ds = Dataset(root_dir=tmp_path, dataset_name="test_create_dataset")
    return ds


@pytest.fixture
def dataset_one_commit(empty_dataset) -> Dataset:
    """Create a dataset with one commit.

    :param empty_dataset: An empty dataset.
    :return: The dataset with one commit.
    """
    # Create the first commit
    empty_dataset.commit(commit_message="test create dataset", add_files=[dummy_file()])
    return empty_dataset


@pytest.fixture
def dataset_two_commits(dataset_one_commit) -> Dataset:
    """Create a dataset with two commits.

    :param dataset_one_commit: A dataset with one commit.
    :return: The dataset with two commits.
    """
    dataset_one_commit.commit(
        commit_message="test create dataset", add_files=dummy_file()
    )
    return dataset_one_commit


def test_commit_to_empty_dataset(empty_dataset):
    """Test committing to an empty dataset.

    :param empty_dataset: An empty dataset.
    """
    assert len(empty_dataset.file_dict) == 0
    empty_dataset.commit(commit_message="test create dataset", add_files=dummy_file())
    assert len(empty_dataset.file_dict) == 1


def test_one_commit(dataset_one_commit):
    """Test committing to a dataset with one commit.

    :param dataset_one_commit: A dataset with one commit.
    """
    assert len(dataset_one_commit.file_dict) == 1
    dataset_one_commit.commit(
        commit_message="test commiting a new data file", add_files=dummy_file()
    )
    assert (
        dataset_one_commit.current_version_hash()
        == dataset_one_commit.latest_version_hash()
    )
    assert len(dataset_one_commit.file_dict) == 2


def test_two_commits(dataset_two_commits):
    """Test committing to a dataset with two commits.

    :param dataset_two_commits: A dataset with two commits.
    """
    assert len(dataset_two_commits.file_dict) == 2
    dataset_two_commits.commit(
        commit_message="test commiting a new data file", add_files=dummy_file()
    )
    assert (
        dataset_two_commits.current_version_hash()
        == dataset_two_commits.latest_version_hash()
    )
    assert len(dataset_two_commits.file_dict) == 3


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_checkout(request, ds_name):
    """Test checking out a dataset.

    :param request: The pytest request object.
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    ds.checkout()
    assert ds.current_version_hash() == ds.latest_version_hash()


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_metadata(request, ds_name):
    """Test getting metadata from a dataset.

    :param request: The pytest request object
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    metadata = ds.metadata()
    assert metadata["dataset_name"] == ds.dataset_name
    assert metadata["current_version_hash"] == ds.current_version_hash()
    assert metadata["description"] == ds.description


@pytest.mark.parametrize(
    "ds_name", ["empty_dataset", "dataset_one_commit", "dataset_two_commits"]
)
def test_file_dict(request, ds_name):
    """Test getting the file dictionary from a dataset.

    :param request: The pytest request object
    :param ds_name: The name of the dataset to checkout.
    """
    ds = request.getfixturevalue(ds_name)
    file_dict = ds.file_dict
    assert len(file_dict) == len(ds.current_commit._file_dict())
