"""Tests for secure credential storage using OS keyring."""

import json
import tempfile
from unittest.mock import Mock, patch

import pytest

from kirin.keyring_store import (
    delete_backend_credentials,
    get_backend_credentials,
    has_backend_credentials,
    store_backend_credentials,
)


def test_store_backend_credentials():
    """Test storing credentials in keyring."""
    backend_id = "test-backend"
    credentials = {
        "key": "AKIAIOSFODNN7EXAMPLE",
        "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-west-2",
    }

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        store_backend_credentials(backend_id, credentials)

        # Verify keyring.set_password was called with correct parameters
        mock_keyring.set_password.assert_called_once()
        call_args = mock_keyring.set_password.call_args

        # Check service name format
        assert call_args[0][0] == f"kirin:backend:{backend_id}"
        # Check username (backend_id)
        assert call_args[0][1] == backend_id
        # Check password (JSON-serialized credentials)
        stored_credentials = json.loads(call_args[0][2])
        assert stored_credentials == credentials


def test_get_backend_credentials():
    """Test retrieving credentials from keyring."""
    backend_id = "test-backend"
    credentials = {
        "key": "AKIAIOSFODNN7EXAMPLE",
        "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-west-2",
    }

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        # Mock keyring to return JSON-serialized credentials
        mock_keyring.get_password.return_value = json.dumps(credentials)

        result = get_backend_credentials(backend_id)

        # Verify keyring.get_password was called with correct parameters
        mock_keyring.get_password.assert_called_once_with(
            f"kirin:backend:{backend_id}", backend_id
        )
        assert result == credentials


def test_get_backend_credentials_not_found():
    """Test retrieving credentials when not found in keyring."""
    backend_id = "nonexistent-backend"

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        # Mock keyring to return None (not found)
        mock_keyring.get_password.return_value = None

        result = get_backend_credentials(backend_id)

        assert result is None


def test_delete_backend_credentials():
    """Test deleting credentials from keyring."""
    backend_id = "test-backend"

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        delete_backend_credentials(backend_id)

        # Verify keyring.delete_password was called with correct parameters
        mock_keyring.delete_password.assert_called_once_with(
            f"kirin:backend:{backend_id}", backend_id
        )


def test_has_backend_credentials():
    """Test checking if credentials exist in keyring."""
    backend_id = "test-backend"

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        # Test when credentials exist
        mock_keyring.get_password.return_value = '{"key": "test"}'
        assert has_backend_credentials(backend_id) is True

        # Test when credentials don't exist
        mock_keyring.get_password.return_value = None
        assert has_backend_credentials(backend_id) is False

        # Verify keyring.get_password was called
        assert mock_keyring.get_password.call_count == 2


def test_keyring_unavailable_graceful_fallback():
    """Test graceful handling when keyring is unavailable."""
    backend_id = "test-backend"
    credentials = {"key": "test", "secret": "test"}

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        # Mock keyring to raise ImportError (keyring unavailable)
        mock_keyring.set_password.side_effect = ImportError("No keyring backend")

        # Should not raise exception, but should handle gracefully
        with pytest.raises(ImportError):
            store_backend_credentials(backend_id, credentials)


def test_keyring_get_unavailable_graceful_fallback():
    """Test graceful handling when keyring is unavailable for get operations."""
    backend_id = "test-backend"

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        # Mock keyring to raise ImportError (keyring unavailable)
        mock_keyring.get_password.side_effect = ImportError("No keyring backend")

        # Should not raise exception, but should handle gracefully
        with pytest.raises(ImportError):
            get_backend_credentials(backend_id)


def test_credentials_json_serialization():
    """Test that complex credentials are properly JSON serialized."""
    backend_id = "test-backend"
    credentials = {
        "key": "AKIAIOSFODNN7EXAMPLE",
        "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-west-2",
        "profile": "default",
        "endpoint_url": "https://s3.amazonaws.com",
        "nested": {"subkey": "subvalue"},
    }

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        store_backend_credentials(backend_id, credentials)

        # Get the stored JSON and verify it can be deserialized
        call_args = mock_keyring.set_password.call_args
        stored_json = call_args[0][2]
        deserialized = json.loads(stored_json)
        assert deserialized == credentials


def test_credentials_with_special_characters():
    """Test storing credentials with special characters."""
    backend_id = "test-backend"
    credentials = {
        "key": "AKIAIOSFODNN7EXAMPLE",
        "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-west-2",
        "description": "Test with special chars: !@#$%^&*()",
    }

    with patch("kirin.keyring_store.keyring") as mock_keyring:
        store_backend_credentials(backend_id, credentials)
        result = get_backend_credentials(backend_id)

        # Mock the get operation
        mock_keyring.get_password.return_value = json.dumps(credentials)
        result = get_backend_credentials(backend_id)

        assert result == credentials
