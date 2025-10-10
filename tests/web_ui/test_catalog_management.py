#!/usr/bin/env python3
"""Tests for catalog management functionality."""

import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from kirin.web.app import app
from kirin.web.config import CatalogManager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Clear any existing catalogs before each test
    catalog_mgr = CatalogManager()
    catalog_mgr.clear_all_catalogs()
    return TestClient(app)


@pytest.fixture
def temp_catalog():
    """Create a temporary catalog for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the directory so connection test passes
        data_dir = Path(temp_dir) / "kirin-data"
        data_dir.mkdir(parents=True, exist_ok=True)

        catalog_config = {
            "name": "Test Catalog",
            "root_dir": str(data_dir),
        }
        yield catalog_config


def test_catalog_list_empty(client):
    """Test that catalog list shows empty state when no catalogs exist."""
    response = client.get("/")
    assert response.status_code == 200
    assert "No data catalogs configured" in response.text
    assert "Add Your First Catalog" in response.text


def test_add_catalog_form_loads(client):
    """Test that add catalog form loads correctly."""
    response = client.get("/catalogs/add")
    assert response.status_code == 200
    assert "Add Data Catalog" in response.text
    assert "Catalog Name" in response.text
    assert "Root Directory" in response.text


def test_add_catalog_success(client, temp_catalog):
    """Test successful catalog creation."""
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200
    assert "Test Catalog" in response.text
    assert "added successfully" in response.text


def test_add_catalog_duplicate_name(client, temp_catalog):
    """Test that duplicate catalog names are handled gracefully."""
    # Create first catalog
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200

    # Try to create another catalog with same name
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200
    assert "already exists" in response.text
    assert "Go to Existing Catalog" in response.text


def test_edit_catalog_form_loads(client, temp_catalog):
    """Test that edit catalog form loads with pre-populated values."""
    # First create a catalog
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200

    # Test edit form loads (catalog ID will be generated from name)
    response = client.get("/catalog/test-catalog/edit")
    assert response.status_code == 200
    assert "Edit Catalog" in response.text
    assert 'value="Test Catalog"' in response.text
    assert temp_catalog["root_dir"] in response.text


def test_update_catalog_success(client, temp_catalog):
    """Test successful catalog update."""
    # Create catalog
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200

    # Update catalog
    updated_data = {
        "name": "Updated Test Catalog",
        "root_dir": temp_catalog["root_dir"],
    }
    response = client.post("/catalog/test-catalog/edit", data=updated_data)
    assert response.status_code == 200
    assert "Updated Test Catalog" in response.text
    assert "updated successfully" in response.text


def test_delete_catalog_confirmation_loads(client, temp_catalog):
    """Test that delete confirmation page loads."""
    # Create catalog
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200

    # Test delete confirmation loads
    response = client.get("/catalog/test-catalog/delete")
    assert response.status_code == 200
    assert "Delete Catalog" in response.text
    assert "Test Catalog" in response.text
    assert "This action cannot be undone" in response.text


def test_delete_catalog_success(client, temp_catalog):
    """Test successful catalog deletion."""
    # Create catalog
    response = client.post("/catalogs/add", data=temp_catalog)
    assert response.status_code == 200

    # Delete catalog
    response = client.post("/catalog/test-catalog/delete")
    assert response.status_code == 200
    assert "deleted successfully" in response.text
    # The success message will contain the catalog name, but the catalog list should be empty
    assert "No data catalogs configured" in response.text


def test_catalog_with_cloud_urls(client):
    """Test that catalogs can be created with cloud URLs."""
    cloud_catalogs = [
        {
            "name": "GCS Catalog",
            "root_dir": "gs://my-bucket/kirin-data",
        },
        {
            "name": "S3 Catalog",
            "root_dir": "s3://my-bucket/kirin-data",
        },
        {
            "name": "Azure Catalog",
            "root_dir": "az://my-container/kirin-data",
        },
    ]

    for catalog_data in cloud_catalogs:
        response = client.post("/catalogs/add", data=catalog_data)
        assert response.status_code == 200
        assert catalog_data["name"] in response.text
        assert catalog_data["root_dir"] in response.text


def test_catalog_validation(client):
    """Test that catalog validation works correctly."""
    # Test missing name
    response = client.post("/catalogs/add", data={"root_dir": "/path/to/data"})
    assert response.status_code == 422  # Validation error

    # Test missing root_dir
    response = client.post("/catalogs/add", data={"name": "Test Catalog"})
    assert response.status_code == 422  # Validation error

    # Test empty name
    response = client.post(
        "/catalogs/add", data={"name": "", "root_dir": "/path/to/data"}
    )
    assert response.status_code == 422  # Validation error

    # Test empty root_dir
    response = client.post(
        "/catalogs/add", data={"name": "Test Catalog", "root_dir": ""}
    )
    assert response.status_code == 422  # Validation error
