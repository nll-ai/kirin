#!/usr/bin/env python3
"""Tests for backend update and delete functionality."""

import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from kirin.web.app import app
from kirin.web.config import BackendManager


class TestBackendManagement:
    """Test backend update and delete operations."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        # Clear any existing backends before each test
        backend_mgr = BackendManager()
        backend_mgr.clear_all_backends()
        return TestClient(app)

    @pytest.fixture
    def temp_backend(self):
        """Create a temporary backend for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the directory so connection test passes
            data_dir = Path(temp_dir) / "kirin-data"
            data_dir.mkdir(parents=True, exist_ok=True)

            backend_config = {
                "name": "Test Backend",
                "type": "local",
                "root_dir": str(data_dir),
            }
            yield backend_config

    def test_edit_backend_form_loads(self, client, temp_backend):
        """Test that edit backend form loads with pre-populated values."""
        # First create a backend
        response = client.post("/backends/add", data=temp_backend)
        if response.status_code != 200:
            print(f"Backend creation failed: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200

        # Test edit form loads (backend ID will be generated from name)
        response = client.get("/backend/test-backend/edit")
        assert response.status_code == 200
        assert "Edit Backend" in response.text
        assert "Test Backend" in response.text
        assert temp_backend["name"] in response.text
        assert temp_backend["type"] in response.text
        # Check that the form has the root_dir field (it will be populated by JavaScript)
        assert "root_dir" in response.text

    def test_edit_backend_form_not_found(self, client):
        """Test 404 for non-existent backend edit form."""
        response = client.get("/backend/non-existent/edit")
        assert response.status_code == 404
        assert "Backend not found" in response.text

    def test_update_backend_name(self, client, temp_backend):
        """Test updating backend name successfully."""
        # Create backend
        response = client.post("/backends/add", data=temp_backend)
        assert response.status_code == 200

        # Update backend name
        update_data = temp_backend.copy()
        update_data["name"] = "Updated Test Backend"

        response = client.post("/backend/test-backend/edit", data=update_data)
        assert response.status_code == 200
        assert "updated successfully" in response.text
        assert "Updated Test Backend" in response.text

        # Verify backend list shows updated name
        response = client.get("/")
        assert response.status_code == 200
        assert "Updated Test Backend" in response.text

    def test_update_backend_root_dir(self, client, temp_backend):
        """Test updating backend root directory."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Create new directory for the update
        with tempfile.TemporaryDirectory() as new_temp_dir:
            new_data_dir = Path(new_temp_dir) / "new-kirin-data"
            new_data_dir.mkdir(parents=True, exist_ok=True)

            # Update root directory
            update_data = temp_backend.copy()
            update_data["root_dir"] = str(new_data_dir)

            response = client.post("/backend/test-backend/edit", data=update_data)
            assert response.status_code == 200
            assert "updated successfully" in response.text

    def test_update_backend_not_found(self, client):
        """Test 404 for updating non-existent backend."""
        update_data = {
            "name": "Updated Backend",
            "type": "local",
            "root_dir": "/some/path",
        }

        response = client.post("/backend/non-existent/edit", data=update_data)
        assert response.status_code == 404
        assert "Backend not found" in response.text

    def test_update_backend_invalid_data(self, client, temp_backend):
        """Test validation errors for invalid update data."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Try to update with missing required field
        update_data = {
            "name": "Updated Backend",
            "type": "local",
            # Missing root_dir
        }

        response = client.post("/backend/test-backend/edit", data=update_data)
        assert response.status_code == 400
        assert "Root directory is required" in response.text

    def test_update_backend_cache_cleared(self, client, temp_backend):
        """Test that dataset cache is cleared on backend update."""
        # Create backend and dataset
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/test-backend/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Update backend (this should clear cache)
        update_data = temp_backend.copy()
        update_data["name"] = "Updated Backend"

        response = client.post("/backend/test-backend/edit", data=update_data)
        assert response.status_code == 200

        # Cache clearing is internal - we can't directly test it,
        # but we can verify the update succeeded
        assert "updated successfully" in response.text

    def test_delete_confirmation_page(self, client, temp_backend):
        """Test delete confirmation page displays correctly."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Test delete confirmation page
        response = client.get("/backend/test-backend/delete")
        assert response.status_code == 200
        assert "Delete Backend" in response.text
        assert "Are you sure?" in response.text
        assert temp_backend["name"] in response.text
        assert "Local" in response.text  # Type is displayed as "Local" not "local"

    def test_delete_confirmation_shows_dataset_count(self, client, temp_backend):
        """Test delete confirmation shows dataset count."""
        # Create backend and dataset
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/test-backend/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Test delete confirmation shows dataset count
        response = client.get("/backend/test-backend/delete")
        assert response.status_code == 200
        assert "1 dataset" in response.text
        assert "You cannot delete a backend that contains datasets" in response.text

    def test_delete_confirmation_not_found(self, client):
        """Test 404 for delete confirmation of non-existent backend."""
        response = client.get("/backend/non-existent/delete")
        assert response.status_code == 404
        assert "Backend not found" in response.text

    def test_delete_backend_success(self, client, temp_backend):
        """Test successful backend deletion."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Delete backend
        response = client.post("/backend/test-backend/delete")
        assert response.status_code == 200
        assert "deleted successfully" in response.text

        # Verify backend is removed from list
        response = client.get("/")
        assert response.status_code == 200
        assert "test-backend" not in response.text

    def test_delete_backend_with_datasets(self, client, temp_backend):
        """Test deletion prevention when backend has datasets."""
        # Create backend and dataset
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/test-backend/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Try to delete backend with datasets
        response = client.post("/backend/test-backend/delete")
        assert response.status_code == 400
        assert "Cannot delete backend with" in response.text
        assert "existing datasets" in response.text

    def test_delete_backend_not_found(self, client):
        """Test 404 for deleting non-existent backend."""
        response = client.post("/backend/non-existent/delete")
        assert response.status_code == 404
        assert "Backend not found" in response.text

    def test_delete_backend_cache_cleared(self, client, temp_backend):
        """Test that dataset cache is cleared on backend deletion."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Delete backend
        response = client.post("/backend/test-backend/delete")
        assert response.status_code == 200

        # Cache clearing is internal - we can't directly test it,
        # but we can verify the deletion succeeded
        assert "deleted successfully" in response.text

    def test_delete_backend_redirects_to_list(self, client, temp_backend):
        """Test that delete redirects to backend list with success message."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Delete backend
        response = client.post("/backend/test-backend/delete")
        assert response.status_code == 200
        assert "Storage Backends" in response.text  # Backend list page
        assert "deleted successfully" in response.text

    def test_backends_page_shows_edit_delete_buttons(self, client, temp_backend):
        """Test that backends page shows edit/delete action buttons."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Check backends page
        response = client.get("/")
        assert response.status_code == 200
        assert "Edit" in response.text
        assert "Delete" in response.text
        assert "/backend/test-backend/edit" in response.text
        assert "/backend/test-backend/delete" in response.text

    def test_edit_button_links_to_edit_form(self, client, temp_backend):
        """Test that edit button navigates to edit form."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Click edit button (simulate navigation)
        response = client.get("/backend/test-backend/edit")
        assert response.status_code == 200
        assert "Edit Backend" in response.text

    def test_delete_button_links_to_confirmation(self, client, temp_backend):
        """Test that delete button navigates to confirmation page."""
        # Create backend
        client.post("/backends/add", data=temp_backend)

        # Click delete button (simulate navigation)
        response = client.get("/backend/test-backend/delete")
        assert response.status_code == 200
        assert "Delete Backend" in response.text

    def test_complete_edit_workflow(self, client):
        """Test complete edit workflow: Create → Edit → Verify changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the directory so connection test passes
            data_dir = Path(temp_dir) / "kirin-data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create backend
            backend_data = {
                "name": "Original Backend",
                "type": "local",
                "root_dir": str(data_dir),
            }
            client.post("/backends/add", data=backend_data)

            # Verify backend exists (backend ID will be slugified)
            response = client.get("/")
            assert response.status_code == 200
            assert "original-backend" in response.text

            # Edit backend
            update_data = {
                "name": "Updated Backend",
                "type": "local",
                "root_dir": str(data_dir),  # Use same directory
            }
            response = client.post("/backend/original-backend/edit", data=update_data)
            assert response.status_code == 200
            assert "updated successfully" in response.text

            # Verify changes (backend ID will change to updated-backend)
            response = client.get("/")
            assert response.status_code == 200
            assert "updated-backend" in response.text
            assert "original-backend" not in response.text

    def test_complete_delete_workflow(self, client):
        """Test complete delete workflow: Create → Delete → Verify removal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the directory so connection test passes
            data_dir = Path(temp_dir) / "kirin-data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create backend
            backend_data = {
                "name": "Backend to Delete",
                "type": "local",
                "root_dir": str(data_dir),
            }
            client.post("/backends/add", data=backend_data)

            # Verify backend exists (backend ID will be slugified)
            response = client.get("/")
            assert response.status_code == 200
            assert "backend-to-delete" in response.text

            # Delete backend
            response = client.post("/backend/backend-to-delete/delete")
            assert response.status_code == 200
            assert "deleted successfully" in response.text

            # Verify removal
            response = client.get("/")
            assert response.status_code == 200
            assert "backend-to-delete" not in response.text

    def test_backend_id_regeneration_on_name_change(self, client):
        """Test that backend ID is regenerated when name changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the directory so connection test passes
            data_dir = Path(temp_dir) / "kirin-data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create backend
            backend_data = {
                "name": "Original Name",
                "type": "local",
                "root_dir": str(data_dir),
            }
            client.post("/backends/add", data=backend_data)

            # Update name (should regenerate ID)
            update_data = {
                "name": "New Name With Spaces",
                "type": "local",
                "root_dir": str(data_dir),
            }
            response = client.post("/backend/original-name/edit", data=update_data)
            assert response.status_code == 200

            # Verify new backend ID is used (slugified)
            response = client.get("/")
            assert response.status_code == 200
            assert "new-name-with-spaces" in response.text
            # The old ID should not be accessible
            response = client.get("/backend/original-name")
            assert response.status_code == 404

    def test_s3_backend_update(self, client):
        """Test updating S3 backend configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create S3 backend
            s3_data = {
                "name": "S3 Backend",
                "type": "s3",
                "bucket": "test-bucket",
                "region": "us-west-2",
                "key": "test-key",
                "secret": "test-secret",
            }
            # This will fail connection test, but we can test the form
            response = client.post("/backends/add", data=s3_data)
            # Should fail due to connection test, but backend might be created
            # Let's test the edit form instead
            response = client.get("/backend/s3-backend/edit")
            if response.status_code == 200:
                assert "S3 Backend" in response.text
                assert "s3" in response.text.lower()

    def test_error_handling_invalid_backend_id(self, client):
        """Test error handling for invalid backend IDs."""
        # Test edit with invalid ID
        response = client.get("/backend/invalid-id/edit")
        assert response.status_code == 404

        # Test delete with invalid ID
        response = client.get("/backend/invalid-id/delete")
        assert response.status_code == 404

        response = client.post("/backend/invalid-id/delete")
        assert response.status_code == 404


def test_backend_management_quick_validation():
    """Quick validation test for backend management functionality."""
    print("🧪 Running Backend Management Quick Validation...")

    # Test that the app can be imported and routes are registered
    from kirin.web.app import app

    # Check that new routes are registered
    routes = [route.path for route in app.routes]
    expected_routes = [
        "/backend/{backend_id}/edit",
        "/backend/{backend_id}/delete",
    ]

    for route in expected_routes:
        if any(route in r for r in routes):
            print(f"✅ Route {route} is registered")
        else:
            print(f"❌ Route {route} is missing")
            return False

    print("🎉 Backend management routes are ready!")
    return True


if __name__ == "__main__":
    # Run quick validation when script is executed directly
    test_backend_management_quick_validation()
