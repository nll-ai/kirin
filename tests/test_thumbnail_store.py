"""Tests for the kirin.thumbnail_store module."""

import io

import pytest

from kirin.storage import ContentStore
from kirin.thumbnail_store import ThumbnailStore


def test_thumbnail_store_initialization(temp_dir):
    """Test ThumbnailStore initialization."""
    store = ThumbnailStore(temp_dir)

    assert store.root_dir == str(temp_dir)
    assert store.thumbnails_dir == f"{temp_dir}/thumbnails"


def test_get_thumbnail_path(temp_dir):
    """Test getting thumbnail path from file hash."""
    store = ThumbnailStore(temp_dir)

    file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    thumbnail_path = store.get_thumbnail_path(file_hash)

    # Should be thumbnails/{hash[:2]}/{hash[2:]}/thumbnail.webp
    expected = (
        f"{temp_dir}/thumbnails/ab/"
        f"cdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890/"
        f"thumbnail.webp"
    )
    assert thumbnail_path == expected


def test_store_and_retrieve_thumbnail(temp_dir):
    """Test storing and retrieving a thumbnail."""
    store = ThumbnailStore(temp_dir)

    file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    thumbnail_bytes = b"fake thumbnail webp content"

    # Store thumbnail
    store.store_thumbnail(file_hash, thumbnail_bytes)

    # Verify it exists
    assert store.thumbnail_exists(file_hash)

    # Retrieve thumbnail
    retrieved = store.retrieve_thumbnail(file_hash)
    assert retrieved == thumbnail_bytes


def test_get_or_generate_thumbnail_new(temp_dir):
    """Test getting or generating a thumbnail when it doesn't exist."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    store = ThumbnailStore(temp_dir)

    # Create a simple valid image using PIL
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    file_content = buffer.getvalue()

    file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    # Get or generate thumbnail
    thumbnail_bytes = store.get_or_generate_thumbnail(file_hash, file_content)

    # Verify thumbnail was generated
    assert thumbnail_bytes is not None
    assert len(thumbnail_bytes) > 0

    # Verify it was stored
    assert store.thumbnail_exists(file_hash)


def test_get_or_generate_thumbnail_cached(temp_dir):
    """Test getting cached thumbnail when it already exists."""
    store = ThumbnailStore(temp_dir)

    file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    thumbnail_bytes = b"cached thumbnail content"

    # Store thumbnail first
    store.store_thumbnail(file_hash, thumbnail_bytes)

    # Get or generate should return cached version
    file_content = b"some file content"
    retrieved = store.get_or_generate_thumbnail(file_hash, file_content)

    assert retrieved == thumbnail_bytes


def test_thumbnail_exists(temp_dir):
    """Test checking if thumbnail exists."""
    store = ThumbnailStore(temp_dir)

    file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    # Initially doesn't exist
    assert not store.thumbnail_exists(file_hash)

    # Store thumbnail
    store.store_thumbnail(file_hash, b"thumbnail content")

    # Now exists
    assert store.thumbnail_exists(file_hash)


def test_thumbnail_store_with_content_store(temp_dir):
    """Test thumbnail store integration with ContentStore."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    content_store = ContentStore(temp_dir)
    thumbnail_store = ThumbnailStore(temp_dir)

    # Create a valid image file
    img = Image.new("RGB", (200, 200), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    file_content = buffer.getvalue()

    # Store image in content store
    filename = "test_image.png"
    file_hash = content_store.store_content(file_content, filename)

    # Generate thumbnail for the image
    thumbnail_bytes = thumbnail_store.get_or_generate_thumbnail(
        file_hash, file_content
    )

    # Verify thumbnail was created
    assert thumbnail_bytes is not None
    assert thumbnail_store.thumbnail_exists(file_hash)


def test_thumbnail_deterministic_path(temp_dir):
    """Test that thumbnail path is deterministic based on file hash."""
    store = ThumbnailStore(temp_dir)

    file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    # Get path multiple times
    path1 = store.get_thumbnail_path(file_hash)
    path2 = store.get_thumbnail_path(file_hash)

    # Should be the same
    assert path1 == path2
