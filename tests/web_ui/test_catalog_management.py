#!/usr/bin/env python3
"""Tests for catalog management functionality."""

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
        data_dir = Path(temp_dir) / "kirin-data"
        data_dir.mkdir(parents=True, exist_ok=True)
        root_dir = str(data_dir)
        yield {"root_dir": root_dir, "catalog_id": catalog_id_from_root(root_dir)}


def test_catalog_list_empty(client):
    """Test that catalog list shows empty state when no catalogs exist."""
    response = client.get("/")
    assert response.status_code == 200
    assert "No data catalogs configured" in response.text
    assert "Add Your First Catalog" in response.text


def test_add_catalog_form_loads(client):
    """Test that add catalog form loads correctly (root directory only, no name)."""
    response = client.get("/catalogs/add")
    assert response.status_code == 200
    assert "Add Data Catalog" in response.text
    assert "Root Directory" in response.text


def test_add_catalog_success(client, temp_catalog):
    """Test successful catalog creation with root_dir only."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] in response.text


def test_add_catalog_duplicate_name(client, temp_catalog):
    """Test that duplicate root directory is handled gracefully."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post("/catalogs/add", data={"root_dir": temp_catalog["root_dir"]})
    assert response.status_code == 400
    assert "already exists" in response.text


def test_edit_catalog_form_loads(client, temp_catalog):
    """Test that edit catalog form loads with pre-populated root_dir."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.get(f"/catalog/{temp_catalog['catalog_id']}/edit")
    assert response.status_code == 200
    assert "Edit Catalog" in response.text
    assert temp_catalog["root_dir"] in response.text


def test_update_catalog_success(client, temp_catalog):
    """Test successful catalog update (root_dir only)."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    updated_root = "/some/other/path"
    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/edit",
        data={"root_dir": updated_root},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert updated_root in response.text


def test_delete_catalog_confirmation_loads(client, temp_catalog):
    """Test that remove-from-list confirmation page loads with correct copy."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.get(f"/catalog/{temp_catalog['catalog_id']}/delete")
    assert response.status_code == 200
    assert "Remove Catalog from List" in response.text
    assert temp_catalog["root_dir"] in response.text
    assert "Remove from List" in response.text
    assert "delete any data" in response.text or "not deleted" in response.text


def test_delete_catalog_confirmation_shows_remove_button_with_datasets(
    client, temp_catalog
):
    """Remove from List button is shown even when catalog has datasets."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/datasets/create",
        data={"name": "some-dataset", "description": ""},
    )
    assert response.status_code in (200, 302)

    response = client.get(f"/catalog/{temp_catalog['catalog_id']}/delete")
    assert response.status_code == 200
    assert "Remove from List" in response.text
    assert "Remove from list only" in response.text


def test_remove_catalog_with_datasets_succeeds(client, temp_catalog):
    """Removing catalog from list succeeds even when it has datasets (302)."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/datasets/create",
        data={"name": "some-dataset", "description": ""},
    )
    assert response.status_code in (200, 302)

    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "No data catalogs configured" in response.text


def test_delete_catalog_success(client, temp_catalog):
    """Test successful catalog removal from list."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "No data catalogs configured" in response.text


def test_catalog_with_cloud_urls(client):
    """Test that catalogs can be created with cloud URLs (root_dir only)."""
    cloud_catalogs = [
        {"root_dir": "gs://my-bucket/kirin-data"},
        {"root_dir": "s3://my-bucket/kirin-data"},
        {"root_dir": "az://my-container/kirin-data"},
    ]

    for catalog_data in cloud_catalogs:
        response = client.post(
            "/catalogs/add", data=catalog_data, follow_redirects=True
        )
        assert response.status_code == 200
        assert catalog_data["root_dir"] in response.text


def test_catalog_validation(client):
    """Test that catalog validation works correctly (root_dir required)."""
    # Only root_dir is required; missing root_dir yields 422
    response = client.post("/catalogs/add", data={})
    assert response.status_code == 422

    response = client.post("/catalogs/add", data={"root_dir": ""})
    assert response.status_code == 422

    # Valid: only root_dir (302 redirect to list or 200 if redirect followed)
    response = client.post("/catalogs/add", data={"root_dir": "/path/to/data"})
    assert response.status_code in (200, 302)


def test_catalog_config_to_catalog_basic():
    """Test CatalogConfig.to_catalog() method with basic configuration."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        # Create a basic catalog config
        config = CatalogConfig(
            id="test-catalog", name="Test Catalog", root_dir="/path/to/data"
        )

        # Test to_catalog() method
        catalog = config.to_catalog()

        # Verify the catalog was created correctly
        assert catalog.root_dir == "/path/to/data"
        assert catalog.fs == mock_fs

        # Verify get_filesystem was called with None for all auth params
        mock_get_filesystem.assert_called_once_with(
            "/path/to/data",
            aws_profile=None,
            gcs_token=None,
            gcs_project=None,
            azure_account_name=None,
            azure_account_key=None,
            azure_connection_string=None,
        )


def test_catalog_config_to_catalog_with_aws_profile():
    """Test CatalogConfig.to_catalog() method with AWS profile."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        # Create a catalog config with AWS profile
        config = CatalogConfig(
            id="test-catalog",
            name="Test Catalog",
            root_dir="s3://bucket/path",
            aws_profile="test-profile",
        )

        # Test to_catalog() method
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


def test_catalog_config_to_catalog_with_gcs_credentials():
    """Test CatalogConfig.to_catalog() method with GCS credentials."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        # Create a catalog config with GCS credentials
        config = CatalogConfig(
            id="test-catalog",
            name="Test Catalog",
            root_dir="gs://bucket/path",
            gcs_token="/path/to/service-account.json",
            gcs_project="test-project",
        )

        # Test to_catalog() method
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


def test_catalog_config_to_catalog_with_azure_credentials():
    """Test CatalogConfig.to_catalog() method with Azure credentials."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        # Create a catalog config with Azure credentials
        config = CatalogConfig(
            id="test-catalog",
            name="Test Catalog",
            root_dir="az://container/path",
            azure_account_name="test-account",
            azure_account_key="test-key",
            azure_connection_string="test-connection",
        )

        # Test to_catalog() method
        catalog = config.to_catalog()

        # Verify the catalog was created correctly
        assert catalog.root_dir == "az://container/path"
        assert catalog.fs == mock_fs

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


def test_catalog_config_to_catalog_with_mixed_credentials():
    """Test CatalogConfig.to_catalog() method with mixed credentials."""
    from unittest.mock import Mock, patch

    from kirin.web.config import CatalogConfig

    with patch("kirin.catalog.get_filesystem") as mock_get_filesystem:
        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        # Create a catalog config with mixed credentials (S3 should use only AWS)
        config = CatalogConfig(
            id="test-catalog",
            name="Test Catalog",
            root_dir="s3://bucket/path",
            aws_profile="aws-profile",
            gcs_token="gcs-token",  # Should be ignored
            azure_account_name="azure-account",  # Should be ignored
        )

        # Test to_catalog() method
        catalog = config.to_catalog()

        # Verify the catalog was created correctly
        assert catalog.root_dir == "s3://bucket/path"
        assert catalog.fs == mock_fs

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


def test_hide_catalog_success(client, temp_catalog):
    """Test successful catalog hiding."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] in response.text

    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/hide", follow_redirects=True
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] not in response.text

    response = client.get("/?show_hidden=true")
    assert response.status_code == 200
    assert temp_catalog["root_dir"] in response.text
    assert "Hidden" in response.text


def test_unhide_catalog_success(client, temp_catalog):
    """Test successful catalog unhiding."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/hide", follow_redirects=True
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] not in response.text

    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/unhide", follow_redirects=True
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] in response.text
    assert (
        '<span class="badge badge-secondary text-xs">Hidden</span>' not in response.text
    )


def test_hide_catalog_from_delete_page(client, temp_catalog):
    """Test hiding catalog from remove-from-list confirmation page."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.get(f"/catalog/{temp_catalog['catalog_id']}/delete")
    assert response.status_code == 200
    assert "Hide Catalog" in response.text

    response = client.post(
        f"/catalog/{temp_catalog['catalog_id']}/hide", follow_redirects=True
    )
    assert response.status_code == 200
    assert temp_catalog["root_dir"] not in response.text


def test_list_catalogs_hides_hidden_by_default(client, temp_catalog):
    """Test that hidden catalogs are filtered out by default."""
    with tempfile.TemporaryDirectory() as temp_dir2:
        root1 = temp_catalog["root_dir"]
        root2 = str(Path(temp_dir2) / "data")
        Path(root2).mkdir(parents=True, exist_ok=True)
        id2 = catalog_id_from_root(root2)

        response = client.post(
            "/catalogs/add", data={"root_dir": root1}, follow_redirects=True
        )
        assert response.status_code == 200
        response = client.post(
            "/catalogs/add", data={"root_dir": root2}, follow_redirects=True
        )
        assert response.status_code == 200

        response = client.post(f"/catalog/{id2}/hide", follow_redirects=True)
        assert response.status_code == 200

        response = client.get("/")
        assert response.status_code == 200
        assert root1 in response.text
        assert root2 not in response.text

        response = client.get("/?show_hidden=true")
        assert response.status_code == 200
        assert root1 in response.text
        assert root2 in response.text
        assert "Hidden" in response.text


def test_hide_catalog_not_found(client):
    """Test hiding a non-existent catalog returns 404."""
    response = client.post("/catalog/non-existent/hide")
    assert response.status_code == 404


def test_unhide_catalog_not_found(client):
    """Test unhiding a non-existent catalog returns 404."""
    response = client.post("/catalog/non-existent/unhide")
    assert response.status_code == 404


def test_hide_unhide_toggle(client, temp_catalog):
    """Test that hide/unhide can be toggled multiple times."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    cid = temp_catalog["catalog_id"]
    root = temp_catalog["root_dir"]

    response = client.post(f"/catalog/{cid}/hide", follow_redirects=True)
    assert response.status_code == 200
    assert root not in response.text

    response = client.post(f"/catalog/{cid}/unhide", follow_redirects=True)
    assert response.status_code == 200
    assert root in response.text

    response = client.post(f"/catalog/{cid}/hide", follow_redirects=True)
    assert response.status_code == 200
    assert root not in response.text

    response = client.post(f"/catalog/{cid}/unhide", follow_redirects=True)
    assert response.status_code == 200
    assert root in response.text


def test_catalog_manager_hide_catalog():
    """Test CatalogManager.hide_catalog() method directly."""
    import tempfile

    from kirin.web.config import CatalogConfig, CatalogManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CatalogManager(config_dir=temp_dir)

        # Create a catalog
        catalog = CatalogConfig(
            id="test-catalog", name="Test Catalog", root_dir="/path/to/data"
        )
        manager.add_catalog(catalog)

        # Verify it's visible
        catalogs = manager.list_catalogs()
        assert len(catalogs) == 1
        assert catalogs[0].id == "test-catalog"
        assert catalogs[0].hidden is False

        # Hide it
        manager.hide_catalog("test-catalog")

        # Verify it's hidden in default list
        catalogs = manager.list_catalogs()
        assert len(catalogs) == 0

        # Verify it's in all catalogs list
        all_catalogs = manager.list_all_catalogs()
        assert len(all_catalogs) == 1
        assert all_catalogs[0].id == "test-catalog"
        assert all_catalogs[0].hidden is True


def test_catalog_manager_unhide_catalog():
    """Test CatalogManager.unhide_catalog() method directly."""
    import tempfile

    from kirin.web.config import CatalogConfig, CatalogManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CatalogManager(config_dir=temp_dir)

        # Create a catalog
        catalog = CatalogConfig(
            id="test-catalog", name="Test Catalog", root_dir="/path/to/data"
        )
        manager.add_catalog(catalog)

        # Hide it
        manager.hide_catalog("test-catalog")
        catalogs = manager.list_catalogs()
        assert len(catalogs) == 0

        # Unhide it
        manager.unhide_catalog("test-catalog")

        # Verify it's visible again
        catalogs = manager.list_catalogs()
        assert len(catalogs) == 1
        assert catalogs[0].id == "test-catalog"
        assert catalogs[0].hidden is False


def test_catalog_config_hidden_field_default():
    """Test that CatalogConfig.hidden defaults to False."""
    from kirin.web.config import CatalogConfig

    catalog = CatalogConfig(
        id="test-catalog", name="Test Catalog", root_dir="/path/to/data"
    )
    assert catalog.hidden is False


def test_catalog_config_hidden_field_persistence():
    """Test that hidden field persists through save/load cycle."""
    import json
    import tempfile
    from pathlib import Path

    from kirin.web.config import CatalogConfig, CatalogManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CatalogManager(config_dir=temp_dir)

        # Create a catalog
        catalog = CatalogConfig(
            id="test-catalog", name="Test Catalog", root_dir="/path/to/data"
        )
        manager.add_catalog(catalog)

        # Hide it
        manager.hide_catalog("test-catalog")

        # Verify persistence by creating new manager instance
        manager2 = CatalogManager(config_dir=temp_dir)
        all_catalogs = manager2.list_all_catalogs()
        assert len(all_catalogs) == 1
        assert all_catalogs[0].hidden is True

        # Verify JSON file contains hidden field
        config_file = Path(temp_dir) / "catalogs.json"
        with open(config_file) as f:
            data = json.load(f)
            assert data["catalogs"][0]["hidden"] is True
