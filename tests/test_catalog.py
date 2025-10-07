"""Tests for lightweight data catalogs."""

from pathlib import Path

import pytest

from kirin.catalog import Catalog
from kirin.testing_utils import dummy_file


@pytest.fixture
def empty_catalog(tmpdir) -> Catalog:
    """Create an empty catalog.

    :return: The empty catalog.
    """
    return Catalog(root_dir=Path(tmpdir))


@pytest.fixture
def catalog_with_one_dataset(empty_catalog) -> Catalog:
    """Create a catalog with one dataset.

    :param empty_catalog: An empty catalog.
    :return: The catalog with one dataset.
    """
    catalog = empty_catalog
    dataset = catalog.create_dataset(
        "test_dataset", "Test dataset for testing purposes."
    )
    dataset.commit(commit_message="test create dataset", add_files=dummy_file())
    return catalog


@pytest.fixture
def catalog_with_two_datasets(catalog_with_one_dataset) -> Catalog:
    """Create a catalog with two datasets.

    :param catalog_with_one_dataset: A catalog with one dataset.
    :return: The catalog with two datasets.
    """
    catalog = catalog_with_one_dataset
    dataset = catalog.create_dataset(
        "test_dataset_2", "Another dataset for testing purposes."
    )
    dataset.commit(commit_message="test create dataset", add_files=dummy_file())
    return catalog


def test_create_dataset(empty_catalog):
    """Test creating a dataset.

    :param empty_catalog: An empty catalog.
    """
    catalog = empty_catalog
    dataset = catalog.create_dataset(
        "test_dataset", "Test dataset for testing purposes."
    )
    assert dataset.dataset_name == "test_dataset"
    assert dataset.description == "Test dataset for testing purposes."
    assert len(catalog) == len(catalog.datasets())

    dataset = catalog.get_dataset("test_dataset")
    assert dataset.dataset_name == "test_dataset"
