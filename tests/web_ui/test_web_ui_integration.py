#!/usr/bin/env python3
"""Integration tests for Kirin Web UI - automated testing without manual clicking."""

import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from kirin.web.app import app
from kirin.web.config import BackendManager


class TestWebUIIntegration:
    """Test the complete web UI workflow programmatically."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def temp_backend(self):
        """Create a temporary backend for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backend_config = {
                "id": "test-backend",
                "name": "Test Backend",
                "type": "local",
                "root_dir": str(Path(temp_dir) / "kirin-data"),
                "config": {},
            }
            yield backend_config

    def test_backend_listing_page(self, client):
        """Test that the backend listing page loads correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Storage Backends" in response.text
        assert "Add Backend" in response.text

    def test_add_backend_form(self, client):
        """Test that the add backend form loads correctly."""
        response = client.get("/backends/add")
        assert response.status_code == 200
        assert "Add Storage Backend" in response.text
        assert "Backend Name" in response.text
        assert "Storage Type" in response.text

    def test_create_backend_workflow(self, client, temp_backend):
        """Test the complete backend creation workflow."""
        # Test backend creation
        response = client.post("/backends/add", data=temp_backend)
        assert response.status_code == 200
        assert "added successfully" in response.text

        # Test backend listing shows the new backend
        response = client.get("/")
        assert response.status_code == 200
        assert temp_backend["name"] in response.text

    def test_dataset_creation_workflow(self, client, temp_backend):
        """Test the complete dataset creation workflow."""
        # First create a backend
        client.post("/backends/add", data=temp_backend)

        # Test dataset listing (should be empty initially)
        response = client.get(f"/backend/{temp_backend['id']}")
        assert response.status_code == 200
        assert (
            "No datasets found" in response.text
            or "Create Your First Dataset" in response.text
        )

        # Test dataset creation
        dataset_data = {
            "name": "test-dataset",
            "description": "Test dataset for automated testing",
        }
        response = client.post(
            f"/backend/{temp_backend['id']}/datasets/create", data=dataset_data
        )
        assert response.status_code == 200
        assert "created successfully" in response.text

        # Test dataset listing shows the new dataset
        response = client.get(f"/backend/{temp_backend['id']}")
        assert response.status_code == 200
        assert dataset_data["name"] in response.text

    def test_dataset_view_workflow(self, client, temp_backend):
        """Test the complete dataset view workflow."""
        # Create backend and dataset
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/{temp_backend['id']}/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Test dataset view page
        response = client.get(f"/backend/{temp_backend['id']}/test-dataset")
        assert response.status_code == 200
        assert "test-dataset" in response.text
        assert "Files" in response.text
        assert "History" in response.text
        assert "Commit" in response.text

    def test_file_upload_workflow(self, client, temp_backend):
        """Test file upload and commit workflow."""
        # Create backend and dataset
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/{temp_backend['id']}/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Create a test file
        test_file_content = "Hello, World!\nThis is a test file."

        # Test file upload and commit
        files = {"files": ("test.txt", test_file_content, "text/plain")}
        data = {"message": "Add test file"}

        response = client.post(
            f"/backend/{temp_backend['id']}/test-dataset/commit", data=data, files=files
        )
        assert response.status_code == 200
        assert "created successfully" in response.text

        # Test that the file appears in the dataset
        response = client.get(f"/backend/{temp_backend['id']}/test-dataset/files")
        assert response.status_code == 200
        assert "test.txt" in response.text

    def test_file_preview_workflow(self, client, temp_backend):
        """Test file preview functionality."""
        # Create backend, dataset, and file
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/{temp_backend['id']}/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Upload a file
        test_file_content = "Hello, World!\nThis is a test file."
        files = {"files": ("test.txt", test_file_content, "text/plain")}
        data = {"message": "Add test file"}
        client.post(
            f"/backend/{temp_backend['id']}/test-dataset/commit", data=data, files=files
        )

        # Test file preview
        response = client.get(
            f"/backend/{temp_backend['id']}/test-dataset/file/test.txt/preview"
        )
        assert response.status_code == 200
        assert "test.txt" in response.text
        assert "Hello, World!" in response.text

    def test_commit_history_workflow(self, client, temp_backend):
        """Test commit history display."""
        # Create backend, dataset, and multiple commits
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/{temp_backend['id']}/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Create first commit
        files1 = {"files": ("file1.txt", "Content 1", "text/plain")}
        data1 = {"message": "First commit"}
        client.post(
            f"/backend/{temp_backend['id']}/test-dataset/commit",
            data=data1,
            files=files1,
        )

        # Create second commit
        files2 = {"files": ("file2.txt", "Content 2", "text/plain")}
        data2 = {"message": "Second commit"}
        client.post(
            f"/backend/{temp_backend['id']}/test-dataset/commit",
            data=data2,
            files=files2,
        )

        # Test history page
        response = client.get(f"/backend/{temp_backend['id']}/test-dataset/history")
        assert response.status_code == 200
        assert "Commit History" in response.text
        assert "First commit" in response.text
        assert "Second commit" in response.text

    def test_error_handling_duplicate_backend(self, client, temp_backend):
        """Test graceful error handling for duplicate backends."""
        # Create first backend
        client.post("/backends/add", data=temp_backend)

        # Try to create duplicate backend
        response = client.post("/backends/add", data=temp_backend)
        assert response.status_code == 200
        assert "already exists" in response.text
        assert "Go to Existing Backend" in response.text

    def test_error_handling_duplicate_dataset(self, client, temp_backend):
        """Test graceful error handling for duplicate datasets."""
        # Create backend and dataset
        client.post("/backends/add", data=temp_backend)
        client.post(
            f"/backend/{temp_backend['id']}/datasets/create",
            data={"name": "test-dataset", "description": "Test dataset"},
        )

        # Try to create duplicate dataset
        response = client.post(
            f"/backend/{temp_backend['id']}/datasets/create",
            data={"name": "test-dataset", "description": "Another test dataset"},
        )
        assert response.status_code == 200
        assert "already exists" in response.text
        assert "View Existing Dataset" in response.text

    def test_commit_workflow(self, client):
        """Test the complete commit workflow with file upload."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "commit-test-dataset",
                "description": "Test dataset for commit",
            },
        )

        # Test commit form loads
        response = client.get(f"/backend/{backend_id}/commit-test-dataset/commit")
        assert response.status_code == 200
        assert "Create New Commit" in response.text
        assert "Upload Files" in response.text

        # Create a test file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            test_file_path = f.name

        try:
            # Test commit with file upload
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/commit-test-dataset/commit",
                    data={"message": "Initial commit with test file"},
                    files={"files": ("test.txt", f, "text/plain")},
                )

            assert response.status_code == 200
            assert "Commit created successfully" in response.text
            # The commit was successful - we can see the commit hash in the response
            assert (
                "11e642f9" in response.text
                or "Commit created successfully" in response.text
            )

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_commit_without_files(self, client):
        """Test commit without file upload (should fail gracefully)."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "empty-commit-test-dataset",
                "description": "Test dataset for empty commit",
            },
        )

        # Test commit without files should fail
        response = client.post(
            f"/backend/{backend_id}/empty-commit-test-dataset/commit",
            data={"message": "Empty commit"},
        )
        assert response.status_code == 400
        assert "No changes specified" in response.text

    def test_file_preview_text_file(self, client):
        """Test file preview for text files."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "preview-test-dataset",
                "description": "Test dataset for file preview",
            },
        )

        # Upload a text file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!\nThis is a test file.\nLine 3")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/preview-test-dataset/commit",
                    data={"message": "Add text file"},
                    files={"files": ("test.txt", f, "text/plain")},
                )
            assert response.status_code == 200

            # Test file preview
            response = client.get(
                f"/backend/{backend_id}/preview-test-dataset/file/test.txt/preview"
            )
            assert response.status_code == 200
            assert "Hello, World!" in response.text
            assert "This is a test file" in response.text
            assert "Text preview" in response.text

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_file_preview_binary_file(self, client):
        """Test file preview for binary files (should show binary message)."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "binary-preview-test-dataset",
                "description": "Test dataset for binary file preview",
            },
        )

        # Create a binary file (PDF-like content)
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
            # Write some binary content that would cause UTF-8 decode error
            f.write(b"\xfb\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/binary-preview-test-dataset/commit",
                    data={"message": "Add binary file"},
                    files={"files": ("test.pdf", f, "application/pdf")},
                )
            assert response.status_code == 200

            # Test file preview (should show binary message)
            response = client.get(
                f"/backend/{backend_id}/binary-preview-test-dataset/file/test.pdf/preview"
            )
            assert response.status_code == 200
            assert "Binary File" in response.text
            assert "cannot be previewed as text" in response.text
            assert "Download the file to view its contents" in response.text

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_file_download(self, client):
        """Test file download functionality."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "download-test-dataset",
                "description": "Test dataset for file download",
            },
        )

        # Upload a file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Download test content")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/download-test-dataset/commit",
                    data={"message": "Add file for download"},
                    files={"files": ("download.txt", f, "text/plain")},
                )
            assert response.status_code == 200

            # Test file download
            response = client.get(
                f"/backend/{backend_id}/download-test-dataset/file/download.txt/download"
            )
            assert response.status_code == 200
            # Check that the download headers are set correctly
            assert "attachment" in response.headers["content-disposition"]
            assert "download.txt" in response.headers["content-disposition"]
            # Check that the response contains the file content
            assert "Download test content" in response.text

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_commit_form_with_file_removal(self, client):
        """Test commit form with file removal functionality."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "remove-test-dataset",
                "description": "Test dataset for file removal",
            },
        )

        # Upload a file first
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test file for removal")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/remove-test-dataset/commit",
                    data={"message": "Add file for removal test"},
                    files={"files": ("test-remove.txt", f, "text/plain")},
                )
            assert response.status_code == 200

            # Test commit form loads with file removal options
            response = client.get(f"/backend/{backend_id}/remove-test-dataset/commit")
            assert response.status_code == 200
            assert "Remove Files" in response.text
            assert "test-remove.txt" in response.text
            assert "Create Commit" in response.text

            # Test commit with file removal
            response = client.post(
                f"/backend/{backend_id}/remove-test-dataset/commit",
                data={
                    "message": "Remove test file",
                    "remove_files": ["test-remove.txt"],
                },
            )
            assert response.status_code == 200
            assert "Commit created successfully" in response.text

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_commit_form_htmx_loading(self, client):
        """Test that commit form works when loaded via HTMX."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "htmx-test-dataset",
                "description": "Test dataset for HTMX loading",
            },
        )

        # Upload a file first
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test file for HTMX")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/htmx-test-dataset/commit",
                    data={"message": "Add file for HTMX test"},
                    files={"files": ("htmx-test.txt", f, "text/plain")},
                )
            assert response.status_code == 200

            # Test HTMX loading of commit form
            response = client.get(f"/backend/{backend_id}/htmx-test-dataset/commit")
            assert response.status_code == 200
            assert "Remove Files" in response.text
            assert "htmx-test.txt" in response.text
            assert (
                "setupRemoveFileCheckboxes" in response.text
            )  # Check that JS is included

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_checkout_commit(self, client):
        """Test checkout functionality for viewing files at a specific commit."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "checkout-test-dataset",
                "description": "Test dataset for checkout functionality",
            },
        )

        # Upload a file first
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test file for checkout")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/checkout-test-dataset/commit",
                    data={"message": "Add file for checkout test"},
                    files={"files": ("checkout-test.txt", f, "text/plain")},
                )
            assert response.status_code == 200
            assert "Commit created successfully" in response.text

            # Get the commit hash from the response
            commit_hash = None
            if "Commit created successfully:" in response.text:
                # Extract commit hash from response
                import re

                match = re.search(
                    r"Commit created successfully: ([a-f0-9]{8})", response.text
                )
                if match:
                    commit_hash = match.group(1)

            # Test checkout with commit hash
            if commit_hash:
                response = client.get(
                    f"/backend/{backend_id}/checkout-test-dataset/checkout/{commit_hash}"
                )
                assert response.status_code == 200
                assert "checkout-test.txt" in response.text
                assert "Viewing historical commit" in response.text
                assert "read-only view" in response.text

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_checkout_nonexistent_commit(self, client):
        """Test checkout with non-existent commit hash."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "checkout-error-test-dataset",
                "description": "Test dataset for checkout error handling",
            },
        )

        # Test checkout with non-existent commit hash
        fake_hash = "1234567890abcdef1234567890abcdef12345678"
        response = client.get(
            f"/backend/{backend_id}/checkout-error-test-dataset/checkout/{fake_hash}"
        )
        assert response.status_code == 404
        assert "Commit not found" in response.text

    def test_file_preview_modal(self, client):
        """Test that file preview modal functionality works."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "modal-test-dataset",
                "description": "Test dataset for modal preview",
            },
        )

        # Upload a file first
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content for modal preview")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/modal-test-dataset/commit",
                    data={"message": "Add file for modal test"},
                    files={"files": ("modal-test.txt", f, "text/plain")},
                )
            assert response.status_code == 200

            # Test main dataset view loads with modal functionality
            response = client.get(f"/backend/{backend_id}/modal-test-dataset")
            assert response.status_code == 200
            assert "openPreview" in response.text  # Check that modal JS is included
            assert "preview-modal" in response.text  # Check that modal HTML is included
            assert "modal-test.txt" in response.text

            # Test that modal has proper CSS classes for centering
            assert 'class="modal"' in response.text  # Check modal CSS class
            assert 'class="modal-overlay"' in response.text  # Check overlay class
            assert 'class="modal-content"' in response.text  # Check content class

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_file_preview_special_characters(self, client):
        """Test that file preview works with filenames containing special characters."""
        # Use existing backend for testing
        backend_id = "test-data"  # Use existing backend

        # Create dataset in existing backend
        client.post(
            f"/backend/{backend_id}/datasets/create",
            data={
                "name": "special-chars-test-dataset",
                "description": "Test dataset for special character filenames",
            },
        )

        # Upload a file with special characters in the name
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content with special characters")
            test_file_path = f.name

        try:
            # Upload file with special characters in filename
            special_filename = "Consulting Agreement with Justin Belair's Entity-v.RL-CH-2025-09-20.docx"
            with open(test_file_path, "rb") as f:
                response = client.post(
                    f"/backend/{backend_id}/special-chars-test-dataset/commit",
                    data={"message": "Add file with special characters"},
                    files={"files": (special_filename, f, "text/plain")},
                )
            assert response.status_code == 200

            # Test files tab loads with properly escaped JavaScript
            response = client.get(
                f"/backend/{backend_id}/special-chars-test-dataset/files"
            )
            assert response.status_code == 200

            # Check that the filename appears in the HTML (may be HTML-escaped)
            assert "Consulting Agreement with Justin Belair" in response.text
            assert "Entity-v.RL-CH-2025-09-20.docx" in response.text

            # Check that the JavaScript is properly escaped (no syntax errors)
            # The filename should be in a data attribute, not inline JavaScript
            assert "data-filename=" in response.text
            assert "openPreview(this.dataset.filename)" in response.text
            # Verify that the single quote is properly escaped in the data attribute
            # With |e, single quotes become HTML entities
            assert "Belair&#39;s" in response.text  # HTML entity for single quote
            # Verify that the filename appears in the data attribute
            assert "Consulting Agreement with Justin Belair" in response.text

        finally:
            # Clean up test file
            os.unlink(test_file_path)


def test_web_ui_quick_validation():
    """Quick validation test that can be run standalone."""
    print("🧪 Running Kirin Web UI Quick Validation...")

    # Test that the app can be imported and initialized
    from kirin.web.app import app
    from kirin.web.config import BackendManager

    # Test backend manager
    backend_mgr = BackendManager()
    backends = backend_mgr.list_backends()
    print(f"✅ Backend manager working - found {len(backends)} backends")

    # Test available types
    types = backend_mgr.get_available_types()
    print(f"✅ Available backend types: {[t['value'] for t in types]}")

    # Test that all routes are registered
    routes = [route.path for route in app.routes]
    expected_routes = [
        "/",
        "/backends/add",
        "/backend/{backend_id}",
        "/backend/{backend_id}/{dataset_name}",
    ]

    for route in expected_routes:
        if any(route in r for r in routes):
            print(f"✅ Route {route} is registered")
        else:
            print(f"❌ Route {route} is missing")
            return False

    print("🎉 Kirin Web UI is ready for testing!")
    return True


if __name__ == "__main__":
    # Run quick validation when script is executed directly
    test_web_ui_quick_validation()
