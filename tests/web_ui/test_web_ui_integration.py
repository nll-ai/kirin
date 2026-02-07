#!/usr/bin/env python3
"""Integration tests for Kirin Web UI - automated testing without manual clicking."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from slugify import slugify

from kirin.web.app import app
from kirin.web.config import CatalogManager, normalize_root_dir


def catalog_id_from_root(root_dir: str) -> str:
    """Derive catalog id from root directory (same as web app)."""
    return slugify(normalize_root_dir(root_dir))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    catalog_mgr = CatalogManager()
    catalog_mgr.clear_all_catalogs()
    return TestClient(app)


@pytest.fixture
def temp_catalog():
    """Create a temporary catalog for testing. Yields root_dir and catalog_id."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_dir = Path(temp_dir) / "kirin-data"
        catalog_dir.mkdir(parents=True, exist_ok=True)
        root_dir = str(catalog_dir)
        yield {"root_dir": root_dir, "catalog_id": catalog_id_from_root(root_dir)}


def test_catalog_listing_page(client):
    """Test that the catalog listing page loads correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Data Catalogs" in response.text
    assert "Add Catalog" in response.text


def test_add_catalog_form(client):
    """Test that the add catalog form loads correctly (root directory only)."""
    response = client.get("/catalogs/add")
    assert response.status_code == 200
    assert "Add Data Catalog" in response.text
    assert "Root Directory" in response.text


def test_create_catalog_and_dataset_workflow(client, temp_catalog):
    """Test the complete workflow: create catalog -> create dataset -> commit files."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] in response.text

    catalog_id = temp_catalog["catalog_id"]

    response = client.get(f"/catalog/{catalog_id}")
    assert response.status_code == 200
    assert temp_catalog["root_dir"] in response.text
    assert "Create Dataset" in response.text

    # Step 3: Create a dataset
    dataset_data = {
        "name": "test-dataset",
        "description": "A test dataset for integration testing",
    }
    response = client.post(f"/catalog/{catalog_id}/datasets/create", data=dataset_data)
    # The endpoint redirects to the dataset view page after successful creation
    assert response.status_code == 200
    assert "test-dataset" in response.text
    # Check that we're on the dataset view page (not a success message)
    assert "No commits" in response.text  # Empty dataset shows "No commits"

    # Step 4: Navigate to dataset view
    response = client.get(f"/catalog/{catalog_id}/test-dataset")
    assert response.status_code == 200
    assert "test-dataset" in response.text
    assert "No files in this commit" in response.text  # Empty dataset

    # Step 5: Test commit form loads
    response = client.get(f"/catalog/{catalog_id}/test-dataset/commit")
    assert response.status_code == 200
    assert "Create New Commit" in response.text
    assert "Upload Files" in response.text


def test_catalog_with_cloud_urls(client):
    """Test that catalogs work with cloud URLs (root_dir only)."""
    cloud_catalogs = [
        {"root_dir": "gs://test-bucket/kirin-data"},
        {"root_dir": "s3://test-bucket/kirin-data"},
        {"root_dir": "az://test-container/kirin-data"},
    ]

    for catalog_data in cloud_catalogs:
        response = client.post(
            "/catalogs/add", data=catalog_data, follow_redirects=True
        )
        assert response.status_code == 200
        assert catalog_data["root_dir"] in response.text


def test_catalog_edit_workflow(client, temp_catalog):
    """Test catalog editing workflow (root_dir only)."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]
    updated_root = "/some/updated/path"
    response = client.post(
        f"/catalog/{catalog_id}/edit",
        data={"root_dir": updated_root},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert updated_root in response.text


def test_catalog_delete_workflow(client, temp_catalog):
    """Test catalog removal-from-list workflow."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]
    response = client.post(f"/catalog/{catalog_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert (
        "No data catalogs configured" in response.text
        or catalog_id not in response.text
    )


def test_dataset_files_tab(client, temp_catalog):
    """Test that dataset files tab loads correctly."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    dataset_data = {"name": "test-dataset", "description": "Test dataset"}
    response = client.post(f"/catalog/{catalog_id}/datasets/create", data=dataset_data)
    assert response.status_code == 200

    # Test files tab
    response = client.get(f"/catalog/{catalog_id}/test-dataset/files")
    assert response.status_code == 200
    assert "No files in this commit" in response.text


def test_dataset_history_tab(client, temp_catalog):
    """Test that dataset history tab loads correctly."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    dataset_data = {"name": "test-dataset", "description": "Test dataset"}
    response = client.post(f"/catalog/{catalog_id}/datasets/create", data=dataset_data)
    assert response.status_code == 200

    # Test history tab
    response = client.get(f"/catalog/{catalog_id}/test-dataset/history")
    assert response.status_code == 200
    # Should show empty history for new dataset


def test_dataset_commit_form(client, temp_catalog):
    """Test that dataset commit form loads correctly."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    dataset_data = {"name": "test-dataset", "description": "Test dataset"}
    response = client.post(f"/catalog/{catalog_id}/datasets/create", data=dataset_data)
    assert response.status_code == 200

    # Test commit form
    response = client.get(f"/catalog/{catalog_id}/test-dataset/commit")
    assert response.status_code == 200
    assert "Create New Commit" in response.text
    assert "Upload Files" in response.text
    assert "Commit Message" in response.text


def test_catalog_help_examples(client):
    """Test that catalog help examples are shown correctly."""
    response = client.get("/catalogs/add")
    assert response.status_code == 200

    # Check that help examples are present
    assert "Examples:" in response.text
    assert "Local:" in response.text
    assert "Google Cloud:" in response.text
    assert "Amazon S3:" in response.text
    assert "Azure:" in response.text
    assert "gs://" in response.text
    assert "s3://" in response.text
    assert "az://" in response.text


def test_catalog_validation_errors(client):
    """Test that catalog validation shows appropriate errors (root_dir required)."""
    response = client.post("/catalogs/add", data={})
    assert response.status_code == 422

    response = client.post(
        "/catalogs/add", data={"root_dir": ""}
    )
    assert response.status_code == 422


def test_download_file(client, temp_catalog):
    """Test file download functionality."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create a dataset with a file
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test_dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200  # Should redirect to dataset view

    # Add a file to the dataset
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content for download")
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test_dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Add test file"},
            )
        assert response.status_code == 200  # Should show dataset view page

        # Test download
        response = client.get(
            f"/catalog/{catalog_id}/test_dataset/file/test.txt/download"
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=test.txt"
        )
        # Ensure we read the full response to trigger the generate function
        content = response.content
        assert content == b"Test content for download"

    finally:
        os.unlink(temp_file_path)


def test_web_ui_uses_catalog_to_catalog_pattern():
    """Test that web UI uses catalog.to_catalog() pattern."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    # Create a catalog config with cloud auth
    config = CatalogConfig(
        id="test-catalog",
        name="Test Catalog",
        root_dir="s3://bucket/path",
        aws_profile="test-profile",
    )

    # Test that to_catalog() method works
    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        catalog = config.to_catalog()

        # Verify the catalog was created correctly
        assert catalog.root_dir == "s3://bucket/path"
        assert catalog.fs == mock_fs

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


def test_web_ui_catalog_manager_has_to_catalog_method():
    """Test that CatalogManager can create catalogs with to_catalog() method."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    # Create a catalog config
    config = CatalogConfig(
        id="test-catalog",
        name="Test Catalog",
        root_dir="gs://bucket/path",
        gcs_token="/path/to/service-account.json",
        gcs_project="test-project",
    )

    # Test that to_catalog() method works
    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        catalog = config.to_catalog()

        # Verify the catalog was created correctly
        assert catalog.root_dir == "gs://bucket/path"
        assert catalog.fs == mock_fs

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


def test_web_ui_catalog_config_serialization():
    """Test that CatalogConfig can be serialized with cloud auth parameters."""
    from dataclasses import asdict

    from kirin.web.config import CatalogConfig

    # Create a catalog config with all cloud auth parameters
    config = CatalogConfig(
        id="test-catalog",
        name="Test Catalog",
        root_dir="az://container/path",
        aws_profile="aws-profile",
        gcs_token="/path/to/service-account.json",
        gcs_project="gcs-project",
        azure_account_name="azure-account",
        azure_account_key="azure-key",
        azure_connection_string="azure-connection",
    )

    # Test serialization
    config_dict = asdict(config)

    # Verify all fields are present
    assert config_dict["id"] == "test-catalog"
    assert config_dict["name"] == "Test Catalog"
    assert config_dict["root_dir"] == "az://container/path"
    assert config_dict["aws_profile"] == "aws-profile"
    assert config_dict["gcs_token"] == "/path/to/service-account.json"
    assert config_dict["gcs_project"] == "gcs-project"
    assert config_dict["azure_account_name"] == "azure-account"
    assert config_dict["azure_account_key"] == "azure-key"
    assert config_dict["azure_connection_string"] == "azure-connection"

    # Test deserialization
    config_from_dict = CatalogConfig(**config_dict)
    assert config_from_dict.id == "test-catalog"
    assert config_from_dict.name == "Test Catalog"
    assert config_from_dict.root_dir == "az://container/path"
    assert config_from_dict.aws_profile == "aws-profile"
    assert config_from_dict.gcs_token == "/path/to/service-account.json"
    assert config_from_dict.gcs_project == "gcs-project"
    assert config_from_dict.azure_account_name == "azure-account"
    assert config_from_dict.azure_account_key == "azure-key"
    assert config_from_dict.azure_connection_string == "azure-connection"
