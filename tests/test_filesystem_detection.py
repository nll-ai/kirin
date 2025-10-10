"""Tests for filesystem auto-detection and error handling."""

import pytest

from kirin.dataset import get_filesystem


def test_local_filesystem_absolute_path():
    """Test that absolute local paths use the file filesystem."""
    fs = get_filesystem("/local/path/to/data")
    # Protocol can be string, list, or tuple
    protocols = fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
    assert "file" in protocols or "local" in protocols


def test_local_filesystem_relative_path():
    """Test that relative local paths use the file filesystem."""
    fs = get_filesystem("relative/path/to/data")
    protocols = fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
    assert "file" in protocols or "local" in protocols


def test_local_filesystem_file_uri():
    """Test that file:// URIs use the file filesystem."""
    fs = get_filesystem("file:///absolute/path")
    protocols = fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
    assert "file" in protocols or "local" in protocols


def test_s3_filesystem():
    """Test that s3:// URIs create S3 filesystem."""
    try:
        fs = get_filesystem("s3://my-bucket/path")
        protocols = (
            fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
        )
        assert "s3" in protocols or "s3a" in protocols
    except ValueError as e:
        # Should get error about s3fs not installed or AWS profile not found
        error_msg = str(e).lower()
        assert (
            "s3fs" in error_msg and "pip install" in error_msg
        ) or "aws profile" in error_msg


def test_gcs_filesystem():
    """Test that gs:// URIs create GCS filesystem."""
    try:
        fs = get_filesystem("gs://my-bucket/path")
        protocols = (
            fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
        )
        assert "gs" in protocols or "gcs" in protocols
    except ValueError as e:
        # If gcsfs is not installed, should get helpful error message
        assert "gcsfs" in str(e).lower()
        assert "pip install" in str(e).lower()


def test_http_filesystem():
    """Test that http:// URIs create HTTP filesystem."""
    try:
        fs = get_filesystem("http://example.com/data")
        protocols = (
            fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
        )
        assert "http" in protocols or "https" in protocols
    except ValueError as e:
        # If aiohttp is not installed, should get helpful error message
        assert "aiohttp" in str(e).lower() or "http" in str(e).lower()


def test_unknown_protocol_error():
    """Test that unknown protocols raise ValueError with helpful message."""
    with pytest.raises(ValueError) as excinfo:
        get_filesystem("completely_unknown_protocol://some/path")

    error_msg = str(excinfo.value)
    # Should mention the protocol
    assert "completely_unknown_protocol" in error_msg
    # Should mention that the protocol is not known
    assert "not known" in error_msg.lower()


def test_memory_filesystem():
    """Test that memory:// URIs work (no extra deps needed)."""
    fs = get_filesystem("memory://")
    protocols = fs.protocol if isinstance(fs.protocol, (list, tuple)) else [fs.protocol]
    assert "memory" in protocols


def test_multiple_calls_same_protocol():
    """Test that multiple calls to get_filesystem work correctly."""
    fs1 = get_filesystem("/path/one")
    fs2 = get_filesystem("/path/two")
    assert fs1.protocol == fs2.protocol
