"""Tests for lightweight data catalogs."""

from pathlib import Path
from unittest.mock import Mock, patch

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
    assert dataset.name == "test_dataset"
    assert dataset.description == "Test dataset for testing purposes."
    assert len(catalog) == len(catalog.datasets())

    dataset = catalog.get_dataset("test_dataset")
    assert dataset.name == "test_dataset"


class TestCatalogCloudAuth:
    """Test Catalog class with cloud authentication parameters."""

    def test_catalog_with_aws_profile(self, tmpdir):
        """Test creating Catalog with AWS profile."""
        with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
            mock_fs = Mock()
            mock_get_filesystem.return_value = mock_fs

            catalog = Catalog(root_dir="s3://bucket/path", aws_profile="test-profile")

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
            assert catalog.fs == mock_fs

    def test_catalog_with_gcs_credentials(self, tmpdir):
        """Test creating Catalog with GCS credentials."""
        with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
            mock_fs = Mock()
            mock_get_filesystem.return_value = mock_fs

            catalog = Catalog(
                root_dir="gs://bucket/path",
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
            assert catalog.fs == mock_fs

    def test_catalog_with_azure_credentials(self, tmpdir):
        """Test creating Catalog with Azure credentials."""
        with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
            mock_fs = Mock()
            mock_get_filesystem.return_value = mock_fs

            catalog = Catalog(
                root_dir="az://container/path",
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
            assert catalog.fs == mock_fs

    def test_catalog_backward_compatibility(self, tmpdir):
        """Test that existing code without auth parameters still works."""
        with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
            mock_fs = Mock()
            mock_get_filesystem.return_value = mock_fs

            # Test local path (should not use any cloud auth)
            catalog = Catalog(root_dir=Path(tmpdir))

            # Verify get_filesystem was called with None for all auth params
            mock_get_filesystem.assert_called_once_with(
                str(Path(tmpdir)),
                aws_profile=None,
                gcs_token=None,
                gcs_project=None,
                azure_account_name=None,
                azure_account_key=None,
                azure_connection_string=None,
            )
            assert catalog.fs == mock_fs

    def test_catalog_with_mixed_auth_params(self, tmpdir):
        """Test that only relevant auth parameters are used for each protocol."""
        with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
            mock_fs = Mock()
            mock_get_filesystem.return_value = mock_fs

            # Test S3 with mixed params - only AWS should be used
            catalog = Catalog(
                root_dir="s3://bucket/path",
                aws_profile="aws-profile",
                gcs_token="gcs-token",  # Should be ignored
                azure_account_name="azure-account",  # Should be ignored
            )

            # Verify get_filesystem was called with all params
            # (filtering happens inside)
            mock_get_filesystem.assert_called_once_with(
                "s3://bucket/path",
                aws_profile="aws-profile",
                gcs_token="gcs-token",
                gcs_project=None,
                azure_account_name="azure-account",
                azure_account_key=None,
                azure_connection_string=None,
            )
            assert catalog.fs == mock_fs
