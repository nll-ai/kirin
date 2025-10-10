"""Tests for backend configuration with authentication modes."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kirin.web.config import BackendConfig, BackendManager


def test_backend_config_with_auth_mode():
    """Test BackendConfig includes auth_mode field."""
    config = BackendConfig(
        id="test-backend",
        name="Test Backend",
        type="s3",
        root_dir="s3://test-bucket",
        auth_mode="system",
        config={"region": "us-west-2"},
    )

    assert config.auth_mode == "system"
    assert config.id == "test-backend"
    assert config.type == "s3"


def test_backend_config_default_auth_mode():
    """Test BackendConfig defaults to system auth mode."""
    config = BackendConfig(
        id="test-backend",
        name="Test Backend",
        type="s3",
        root_dir="s3://test-bucket",
        config={"region": "us-west-2"},
    )

    assert config.auth_mode == "system"


def test_backend_manager_create_filesystem_system_auth():
    """Test BackendManager creates filesystem with system auth mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend_mgr = BackendManager(temp_dir)

        # Create backend with system auth
        backend = BackendConfig(
            id="test-s3",
            name="Test S3",
            type="s3",
            root_dir="s3://test-bucket",
            auth_mode="system",
            config={"region": "us-west-2"},
        )

        with patch("kirin.web.config.get_s3_filesystem") as mock_get_s3:
            mock_fs = Mock()
            mock_get_s3.return_value = mock_fs

            fs = backend_mgr.create_filesystem(backend)

            # Should call get_s3_filesystem with no explicit credentials
            mock_get_s3.assert_called_once_with(region="us-west-2")
            assert fs == mock_fs


def test_backend_manager_create_filesystem_keyring_auth():
    """Test BackendManager creates filesystem with keyring auth mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend_mgr = BackendManager(temp_dir)

        # Create backend with keyring auth
        backend = BackendConfig(
            id="test-s3",
            name="Test S3",
            type="s3",
            root_dir="s3://test-bucket",
            auth_mode="keyring",
            config={"region": "us-west-2", "keyring_key": "kirin:backend:test-s3"},
        )

        with patch("kirin.web.config.get_backend_credentials") as mock_get_creds:
            with patch("kirin.web.config.get_s3_filesystem") as mock_get_s3:
                # Mock keyring credentials
                mock_creds = {
                    "key": "AKIAIOSFODNN7EXAMPLE",
                    "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                }
                mock_get_creds.return_value = mock_creds

                mock_fs = Mock()
                mock_get_s3.return_value = mock_fs

                fs = backend_mgr.create_filesystem(backend)

                # Should retrieve credentials from keyring
                mock_get_creds.assert_called_once_with("test-s3")

                # Should call get_s3_filesystem with credentials
                mock_get_s3.assert_called_once_with(
                    region="us-west-2",
                    key="AKIAIOSFODNN7EXAMPLE",
                    secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                )
                assert fs == mock_fs


def test_backend_manager_create_filesystem_keyring_no_credentials():
    """Test BackendManager handles missing keyring credentials gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend_mgr = BackendManager(temp_dir)

        # Create backend with keyring auth
        backend = BackendConfig(
            id="test-s3",
            name="Test S3",
            type="s3",
            root_dir="s3://test-bucket",
            auth_mode="keyring",
            config={"region": "us-west-2", "keyring_key": "kirin:backend:test-s3"},
        )

        with patch("kirin.web.config.get_backend_credentials") as mock_get_creds:
            with patch("kirin.web.config.get_s3_filesystem") as mock_get_s3:
                # Mock no credentials found
                mock_get_creds.return_value = None

                mock_fs = Mock()
                mock_get_s3.return_value = mock_fs

                fs = backend_mgr.create_filesystem(backend)

                # Should still call get_s3_filesystem but without credentials
                mock_get_creds.assert_called_once_with("test-s3")
                mock_get_s3.assert_called_once_with(region="us-west-2")
                assert fs == mock_fs


def test_backend_manager_create_filesystem_gcs_system_auth():
    """Test BackendManager creates GCS filesystem with system auth."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend_mgr = BackendManager(temp_dir)

        backend = BackendConfig(
            id="test-gcs",
            name="Test GCS",
            type="gcs",
            root_dir="gs://test-bucket",
            auth_mode="system",
            config={"project": "test-project"},
        )

        with patch("kirin.web.config.get_gcs_filesystem") as mock_get_gcs:
            mock_fs = Mock()
            mock_get_gcs.return_value = mock_fs

            fs = backend_mgr.create_filesystem(backend)

            # Should call get_gcs_filesystem with no explicit credentials
            mock_get_gcs.assert_called_once_with(project="test-project")
            assert fs == mock_fs


def test_backend_manager_create_filesystem_azure_system_auth():
    """Test BackendManager creates Azure filesystem with system auth."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend_mgr = BackendManager(temp_dir)

        backend = BackendConfig(
            id="test-azure",
            name="Test Azure",
            type="azure",
            root_dir="az://test-container",
            auth_mode="system",
            config={"account_name": "testaccount"},
        )

        with patch("kirin.web.config.get_azure_filesystem") as mock_get_azure:
            mock_fs = Mock()
            mock_get_azure.return_value = mock_fs

            fs = backend_mgr.create_filesystem(backend)

            # Should call get_azure_filesystem with no explicit credentials
            mock_get_azure.assert_called_once_with(account_name="testaccount")
            assert fs == mock_fs


def test_backend_manager_migration_from_old_config():
    """Test BackendManager handles migration from old config format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create old-style config file
        old_config = {
            "backends": [
                {
                    "id": "old-backend",
                    "name": "Old Backend",
                    "type": "s3",
                    "root_dir": "s3://old-bucket",
                    "config": {
                        "key": "AKIAIOSFODNN7EXAMPLE",
                        "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                        "region": "us-west-2",
                    },
                }
            ]
        }

        config_file = Path(temp_dir) / "backends.json"
        with open(config_file, "w") as f:
            json.dump(old_config, f)

        backend_mgr = BackendManager(temp_dir)
        backends = backend_mgr.list_backends()

        # Should have migrated to system auth mode
        assert len(backends) == 1
        backend = backends[0]
        assert backend.auth_mode == "system"
        assert backend.id == "old-backend"
        # Old credentials should be removed
        assert "key" not in backend.config
        assert "secret" not in backend.config
        assert backend.config["region"] == "us-west-2"


def test_backend_manager_save_backend_with_auth_mode():
    """Test BackendManager saves backend with auth_mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend_mgr = BackendManager(temp_dir)

        backend = BackendConfig(
            id="test-backend",
            name="Test Backend",
            type="s3",
            root_dir="s3://test-bucket",
            auth_mode="keyring",
            config={"region": "us-west-2"},
        )

        backend_mgr.add_backend(backend)

        # Verify backend was saved with auth_mode
        saved_backends = backend_mgr.list_backends()
        assert len(saved_backends) == 1
        assert saved_backends[0].auth_mode == "keyring"

        # Verify JSON contains auth_mode
        with open(backend_mgr.config_file, "r") as f:
            data = json.load(f)
            assert data["backends"][0]["auth_mode"] == "keyring"
