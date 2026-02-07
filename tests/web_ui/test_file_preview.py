#!/usr/bin/env python3
"""Tests for file preview functionality in the web UI."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from slugify import slugify

from kirin.web.app import app
from kirin.web.config import normalize_root_dir


def catalog_id_from_root(root_dir: str) -> str:
    """Derive catalog id from root directory (same as web app)."""
    return slugify(normalize_root_dir(root_dir))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_catalog():
    """Create a temporary catalog for testing. Yields root_dir and catalog_id."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root_dir = temp_dir
        yield {"root_dir": root_dir, "catalog_id": catalog_id_from_root(root_dir)}


def test_text_file_preview(client, temp_catalog):
    """Test that text files can be previewed correctly."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Add a text file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("print('Hello, World!')\nprint('This is a test file')")
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.py", f, "text/x-python")},
                data={"message": "Add test Python file"},
            )
        assert response.status_code == 200

        # Test preview endpoint
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.py/preview"
        )
        assert response.status_code == 200
        assert "test.py" in response.text
        assert "Hello, World!" in response.text
        assert "This is a test file" in response.text
        assert "File Content" in response.text
        # Should have code block with text content
        assert "<pre" in response.text or "<code" in response.text

    finally:
        Path(temp_file_path).unlink()


def test_image_file_preview(client, temp_catalog):
    """Test that image files can be previewed correctly."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Create a simple WebP image file
    # Using minimal valid WebP bytes for testing
    # WebP file header: RIFF....WEBP
    webp_content = (
        b"RIFF"
        + b"\x00\x00\x00\x00"  # File size (placeholder)
        + b"WEBP"
        + b"VP8 "  # VP8 chunk header
        + b"\x00\x00\x00\x00"  # VP8 chunk size (placeholder)
        + b"\x00" * 10  # Minimal VP8 data
    )

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".webp", delete=False) as f:
        f.write(webp_content)
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.webp", f, "image/webp")},
                data={"message": "Add test WebP file"},
            )
        assert response.status_code == 200

        # Test preview endpoint
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.webp/preview"
        )
        assert response.status_code == 200
        assert "test.webp" in response.text
        assert "File Content" in response.text
        # Should have image tag
        assert "<img" in response.text
        assert "/image" in response.text

        # Test image endpoint directly
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.webp/image"
        )
        assert response.status_code == 200
        # Assert exact content type for WebP files
        assert response.headers["Content-Type"] == "image/webp"
        assert b"WEBP" in response.content

    finally:
        Path(temp_file_path).unlink()


def test_file_preview_with_checkout(client, temp_catalog):
    """Test that file preview works with checkout parameter."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Add first version of file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Version 1")
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Add version 1"},
            )
        assert response.status_code == 200

        # Get first commit hash from history
        from kirin import Catalog

        catalog = Catalog(root_dir=temp_catalog["root_dir"])
        dataset = catalog.get_dataset("test-dataset")
        history = dataset.history()
        assert len(history) > 0
        first_commit_hash = history[-1].hash  # Oldest commit

        # Add second version
        with open(temp_file_path, "w") as f:
            f.write("Version 2")

        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Add version 2"},
            )
        assert response.status_code == 200

        # Test preview with checkout to first commit
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/preview",
            params={"checkout": first_commit_hash},
        )
        assert response.status_code == 200
        assert "Version 1" in response.text
        assert "Version 2" not in response.text

    finally:
        Path(temp_file_path).unlink()


def test_file_commits_endpoint(client, temp_catalog):
    """Test the file commits endpoint returns correct data."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Add file in multiple commits
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Content")
        temp_file_path = f.name

    try:
        # First commit
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "First commit"},
            )
        assert response.status_code == 200

        # Second commit
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Second commit"},
            )
        assert response.status_code == 200

        # Test commits endpoint
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/commits"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        # Should be ordered newest first
        assert data[0]["message"] == "Second commit"
        assert data[1]["message"] == "First commit"
        # Check structure
        assert "hash" in data[0]
        assert "short_hash" in data[0]
        assert "message" in data[0]
        assert "timestamp" in data[0]

    finally:
        Path(temp_file_path).unlink()


def test_image_file_loading(client, temp_catalog):
    """Test that image files load correctly through the image endpoint."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Create a simple PNG-like file (actually just text, but with .png extension)
    # For a real test, we'd need actual image bytes, but this tests the endpoint
    png_content = b"fake png content"

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as f:
        f.write(png_content)
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.png", f, "image/png")},
                data={"message": "Add test PNG file"},
            )
        assert response.status_code == 200

        # Test image endpoint
        response = client.get(f"/catalog/{catalog_id}/test-dataset/file/test.png/image")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        assert response.content == png_content

        # Test image endpoint with checkout
        from kirin import Catalog

        catalog = Catalog(root_dir=temp_catalog["root_dir"])
        dataset = catalog.get_dataset("test-dataset")
        commit_hash = dataset.current_commit.hash

        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.png/image",
            params={"checkout": commit_hash},
        )
        assert response.status_code == 200
        assert response.content == png_content

    finally:
        Path(temp_file_path).unlink()


def test_file_commits_not_in_latest(client, temp_catalog):
    """Test commits endpoint for file that exists in older commits but not HEAD."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Add file in first commit
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Version 1")
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Add file"},
            )
        assert response.status_code == 200

        # Get first commit hash
        from kirin import Catalog

        catalog = Catalog(root_dir=temp_catalog["root_dir"])
        dataset = catalog.get_dataset("test-dataset")
        history = dataset.history()
        assert len(history) > 0
        first_commit_hash = history[-1].hash  # Oldest commit (first one)

        # Remove file in second commit
        response = client.post(
            f"/catalog/{catalog_id}/test-dataset/commit",
            data={"message": "Remove file", "remove_files": ["test.txt"]},
        )
        assert response.status_code == 200

        # Verify file doesn't exist in latest commit
        dataset = catalog.get_dataset("test-dataset")
        assert not dataset.has_file("test.txt")

        # Test commits endpoint - should return only the first commit
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/commits"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["hash"] == first_commit_hash
        assert data[0]["message"] == "Add file"

        # Test preview with checkout to first commit (where file exists)
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/preview",
            params={"checkout": first_commit_hash},
        )
        assert response.status_code == 200
        assert "Version 1" in response.text

    finally:
        Path(temp_file_path).unlink()


def test_file_commits_removed_and_readded(client, temp_catalog):
    """Test commits endpoint for file that was removed and re-added (gap scenario)."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Commit 1: Add file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Version 1")
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Add file"},
            )
        assert response.status_code == 200

        from kirin import Catalog

        catalog = Catalog(root_dir=temp_catalog["root_dir"])
        dataset = catalog.get_dataset("test-dataset")
        history = dataset.history()
        commit1_hash = history[-1].hash

        # Commit 2: Remove file
        response = client.post(
            f"/catalog/{catalog_id}/test-dataset/commit",
            data={"message": "Remove file", "remove_files": ["test.txt"]},
        )
        assert response.status_code == 200

        # Commit 3: Re-add file (different content)
        with open(temp_file_path, "w") as f:
            f.write("Version 2")

        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Re-add file"},
            )
        assert response.status_code == 200

        dataset = catalog.get_dataset("test-dataset")
        commit3_hash = dataset.current_commit.hash

        # Commit 4: Modify file
        with open(temp_file_path, "w") as f:
            f.write("Version 3")

        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Modify file"},
            )
        assert response.status_code == 200

        dataset = catalog.get_dataset("test-dataset")
        commit4_hash = dataset.current_commit.hash

        # Test commits endpoint - should return commits 1, 3, 4 (skipping commit 2)
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/commits"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        # Should be ordered newest first
        assert data[0]["hash"] == commit4_hash
        assert data[0]["message"] == "Modify file"
        assert data[1]["hash"] == commit3_hash
        assert data[1]["message"] == "Re-add file"
        assert data[2]["hash"] == commit1_hash
        assert data[2]["message"] == "Add file"

        # Test that preview works for each commit
        # Commit 1
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/preview",
            params={"checkout": commit1_hash},
        )
        assert response.status_code == 200
        assert "Version 1" in response.text

        # Commit 3
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/preview",
            params={"checkout": commit3_hash},
        )
        assert response.status_code == 200
        assert "Version 2" in response.text

        # Commit 4
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/preview",
            params={"checkout": commit4_hash},
        )
        assert response.status_code == 200
        assert "Version 3" in response.text

    finally:
        Path(temp_file_path).unlink()


def test_file_preview_invalid_checkout(client, temp_catalog):
    """Test preview with invalid checkout hash handles gracefully."""
    response = client.post(
        "/catalogs/add",
        data={"root_dir": temp_catalog["root_dir"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    catalog_id = temp_catalog["catalog_id"]

    # Create dataset
    response = client.post(
        f"/catalog/{catalog_id}/datasets/create",
        data={"name": "test-dataset", "description": "Test dataset"},
    )
    assert response.status_code == 200

    # Add file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Content")
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                f"/catalog/{catalog_id}/test-dataset/commit",
                files={"files": ("test.txt", f, "text/plain")},
                data={"message": "Add file"},
            )
        assert response.status_code == 200

        # Test preview with invalid checkout hash
        invalid_hash = "invalid1234567890abcdef"
        response = client.get(
            f"/catalog/{catalog_id}/test-dataset/file/test.txt/preview",
            params={"checkout": invalid_hash},
        )
        # Should return 400 Bad Request for invalid hash
        assert response.status_code == 400
        assert (
            "Invalid checkout hash" in response.text
            or "not found" in response.text.lower()
        )

    finally:
        Path(temp_file_path).unlink()
