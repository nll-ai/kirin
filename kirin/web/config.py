"""Backend configuration manager for Kirin Web UI."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from ..cloud_auth import (
    get_azure_filesystem,
    get_gcs_filesystem,
    get_s3_compatible_filesystem,
    get_s3_filesystem,
)
from ..keyring_store import get_backend_credentials


@dataclass
class BackendConfig:
    """Configuration for a storage backend."""

    id: str
    name: str
    type: str  # local, s3, gcs, azure, s3_compatible
    root_dir: str
    config: Dict[str, Any]
    auth_mode: str = "system"  # system, keyring, explicit


class BackendManager:
    """Manages storage backend configurations."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize backend manager.

        Args:
            config_dir: Directory to store config files (defaults to ~/.kirin)
        """
        if config_dir is None:
            config_dir = Path.home() / ".kirin"
        else:
            config_dir = Path(config_dir)

        self.config_dir = config_dir
        self.config_file = config_dir / "backends.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize empty config if file doesn't exist
        if not self.config_file.exists():
            self._save_backends([])

    def _load_backends(self) -> List[Dict[str, Any]]:
        """Load backends from config file."""
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                backends = data.get("backends", [])

                # Migrate old backends to new format
                migrated = False
                for backend in backends:
                    if "auth_mode" not in backend:
                        # Migrate to system auth mode
                        backend["auth_mode"] = "system"

                        # Remove plain-text credentials for security
                        if "config" in backend:
                            config = backend["config"]
                            if "key" in config and "secret" in config:
                                logger.warning(
                                    f"Removing plain-text credentials from backend {backend.get('id', 'unknown')}"
                                )
                                config.pop("key", None)
                                config.pop("secret", None)
                                migrated = True

                # Save migrated backends
                if migrated:
                    self._save_backends(backends)
                    logger.info("Migrated backends to new auth_mode format")

                return backends
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load backends config: {e}")
            return []

    def _save_backends(self, backends: List[Dict[str, Any]]) -> None:
        """Save backends to config file."""
        try:
            data = {"backends": backends}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(backends)} backends to config")
        except Exception as e:
            logger.error(f"Failed to save backends config: {e}")
            raise

    def list_backends(self) -> List[BackendConfig]:
        """List all configured backends."""
        backends_data = self._load_backends()
        return [BackendConfig(**backend) for backend in backends_data]

    def get_backend(self, backend_id: str) -> Optional[BackendConfig]:
        """Get a specific backend by ID."""
        backends = self.list_backends()
        for backend in backends:
            if backend.id == backend_id:
                return backend
        return None

    def add_backend(self, backend: BackendConfig) -> None:
        """Add a new backend configuration."""
        backends = self._load_backends()

        # Check if backend ID already exists
        for existing in backends:
            if existing["id"] == backend.id:
                raise ValueError(f"Backend with ID '{backend.id}' already exists")

        # Add new backend
        backends.append(asdict(backend))
        self._save_backends(backends)
        logger.info(f"Added backend: {backend.name} ({backend.id})")

    def update_backend(self, backend: BackendConfig) -> None:
        """Update an existing backend configuration."""
        backends = self._load_backends()

        # Find and update backend
        for i, existing in enumerate(backends):
            if existing["id"] == backend.id:
                backends[i] = asdict(backend)
                self._save_backends(backends)
                logger.info(f"Updated backend: {backend.name} ({backend.id})")
                return

        raise ValueError(f"Backend with ID '{backend.id}' not found")

    def delete_backend(self, backend_id: str) -> None:
        """Delete a backend configuration."""
        backends = self._load_backends()

        # Find and remove backend
        for i, backend in enumerate(backends):
            if backend["id"] == backend_id:
                del backends[i]
                self._save_backends(backends)
                logger.info(f"Deleted backend: {backend_id}")
                return

        raise ValueError(f"Backend with ID '{backend_id}' not found")

    def clear_all_backends(self) -> None:
        """Clear all backend configurations (for testing)."""
        self._save_backends([])
        logger.info("Cleared all backends")

    def test_connection(self, backend: BackendConfig) -> bool:
        """Test connection to a backend.

        Args:
            backend: Backend configuration to test

        Returns:
            True if connection successful, False otherwise
        """
        logger.info(
            f"Testing connection for backend: {backend.id} (type: {backend.type})"
        )
        logger.info(f"Backend config: {backend.config}")
        logger.info(f"Auth mode: {backend.auth_mode}")
        logger.info(f"Root dir: {backend.root_dir}")

        try:
            logger.info("Creating filesystem...")
            fs = self.create_filesystem(backend)
            logger.info(f"Filesystem created successfully: {type(fs)}")

            # Try to list the root directory
            if backend.type == "local":
                # For local, check if directory exists
                logger.info(f"Checking if local directory exists: {backend.root_dir}")
                exists = os.path.exists(backend.root_dir)
                logger.info(f"Directory exists: {exists}")
                return exists
            else:
                # For cloud storage, try Kirin's Dataset approach first (bypasses SSL issues)
                logger.info(
                    "Testing with Kirin Dataset (bypassing raw filesystem SSL issues)..."
                )
                try:
                    from kirin.dataset import Dataset

                    test_dataset = Dataset(
                        root_dir=backend.root_dir, name="test-connection"
                    )
                    logger.info("Kirin Dataset created successfully")
                    # Try to get the catalog to test the connection
                    from kirin.catalog import Catalog

                    catalog = Catalog(backend.root_dir)
                    datasets = catalog.datasets()
                    logger.info(f"Catalog found {len(datasets)} datasets")
                    logger.info("Kirin Dataset connection test successful")
                    return True
                except Exception as e:
                    logger.warning(f"Kirin Dataset test failed: {e}")
                    logger.warning(f"Dataset exception type: {type(e).__name__}")
                    import traceback

                    logger.warning(f"Dataset traceback: {traceback.format_exc()}")

                    # Fallback to raw filesystem test (may fail with SSL)
                    logger.info("Falling back to raw filesystem test...")
                    try:
                        files = fs.ls(backend.root_dir, detail=False)
                        logger.info(
                            f"Successfully listed {len(files)} items in {backend.root_dir}"
                        )
                        logger.info(
                            f"Sample files: {files[:5] if files else 'No files found'}"
                        )
                        return True
                    except Exception as fs_e:
                        logger.error(f"Raw filesystem test also failed: {fs_e}")
                        raise fs_e

        except Exception as e:
            logger.error(f"Backend connection test failed for {backend.id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def create_filesystem(self, backend: BackendConfig):
        """Create a filesystem instance for a backend.

        Args:
            backend: Backend configuration

        Returns:
            fsspec filesystem instance
        """
        logger.info(f"Creating filesystem for backend: {backend.id}")
        logger.info(f"Backend type: {backend.type}")
        logger.info(f"Auth mode: {backend.auth_mode}")
        logger.info(f"Initial config: {backend.config}")

        if backend.type == "local":
            logger.info("Creating local filesystem")
            import fsspec

            fs = fsspec.filesystem("file")
            logger.info(f"Local filesystem created: {type(fs)}")
            return fs

        # Handle authentication based on auth_mode
        config = backend.config.copy()
        logger.info(f"Starting with config: {config}")

        if backend.auth_mode == "keyring":
            logger.info("Using keyring authentication")
            # Retrieve credentials from keyring
            credentials = get_backend_credentials(backend.id)
            if credentials:
                logger.info("Found keyring credentials, updating config")
                config.update(credentials)
            else:
                logger.info("No keyring credentials found, falling back to system auth")
            # If no credentials found, fall back to system auth

        elif backend.auth_mode == "explicit":
            logger.info("Using explicit authentication")
            # Use explicit credentials from config (backward compatibility)
            pass

        # Remove keyring-specific fields before passing to cloud auth functions
        config.pop("keyring_key", None)
        logger.info(f"Final config for cloud auth: {config}")

        # For "system" auth_mode or when keyring has no credentials,
        # let the cloud_auth functions auto-detect system credentials
        logger.info(f"Calling cloud auth function for type: {backend.type}")

        try:
            if backend.type == "s3":
                logger.info("Creating S3 filesystem")
                fs = get_s3_filesystem(**config)
                logger.info(f"S3 filesystem created: {type(fs)}")
                return fs
            elif backend.type == "gcs":
                logger.info("Creating GCS filesystem")
                fs = get_gcs_filesystem(**config)
                logger.info(f"GCS filesystem created: {type(fs)}")
                return fs
            elif backend.type == "azure":
                logger.info("Creating Azure filesystem")
                fs = get_azure_filesystem(**config)
                logger.info(f"Azure filesystem created: {type(fs)}")
                return fs
            elif backend.type == "s3_compatible":
                logger.info("Creating S3-compatible filesystem")
                fs = get_s3_compatible_filesystem(**config)
                logger.info(f"S3-compatible filesystem created: {type(fs)}")
                return fs
            else:
                raise ValueError(f"Unsupported backend type: {backend.type}")
        except Exception as e:
            logger.error(f"Failed to create filesystem for {backend.type}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def get_available_types(self) -> List[Dict[str, str]]:
        """Get list of available backend types with descriptions."""
        return [
            {
                "value": "local",
                "label": "Local Filesystem",
                "description": "Local directory on your machine",
            },
            {
                "value": "s3",
                "label": "Amazon S3",
                "description": "Amazon Simple Storage Service",
            },
            {
                "value": "gcs",
                "label": "Google Cloud Storage",
                "description": "Google Cloud Storage",
            },
            {
                "value": "azure",
                "label": "Azure Blob Storage",
                "description": "Microsoft Azure Blob Storage",
            },
            {
                "value": "s3_compatible",
                "label": "S3-Compatible",
                "description": "Minio, Backblaze B2, DigitalOcean Spaces, etc.",
            },
        ]

    def get_type_fields(self, backend_type: str) -> List[Dict[str, Any]]:
        """Get form fields for a specific backend type.

        Args:
            backend_type: Type of backend (local, s3, gcs, etc.)

        Returns:
            List of field definitions for the form
        """
        if backend_type == "local":
            return [
                {
                    "name": "name",
                    "label": "Backend Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "root_dir",
                    "label": "Directory Path",
                    "type": "text",
                    "required": True,
                    "placeholder": "/path/to/data",
                },
            ]

        elif backend_type == "s3":
            return [
                {
                    "name": "name",
                    "label": "Backend Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "bucket",
                    "label": "Bucket Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "prefix",
                    "label": "Prefix (optional)",
                    "type": "text",
                    "required": False,
                    "placeholder": "kirin",
                },
                {
                    "name": "region",
                    "label": "Region",
                    "type": "text",
                    "required": True,
                    "placeholder": "us-west-2",
                },
                {
                    "name": "key",
                    "label": "Access Key ID",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "secret",
                    "label": "Secret Access Key",
                    "type": "password",
                    "required": True,
                },
            ]

        elif backend_type == "gcs":
            return [
                {
                    "name": "name",
                    "label": "Backend Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "bucket",
                    "label": "Bucket Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "prefix",
                    "label": "Prefix (optional)",
                    "type": "text",
                    "required": False,
                    "placeholder": "kirin",
                },
                {
                    "name": "project",
                    "label": "GCP Project ID",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "token",
                    "label": "Service Account JSON Path",
                    "type": "text",
                    "required": False,
                    "placeholder": "path/to/key.json or 'cloud'",
                },
            ]

        elif backend_type == "azure":
            return [
                {
                    "name": "name",
                    "label": "Backend Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "container",
                    "label": "Container Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "prefix",
                    "label": "Prefix (optional)",
                    "type": "text",
                    "required": False,
                    "placeholder": "kirin",
                },
                {
                    "name": "account_name",
                    "label": "Storage Account Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "account_key",
                    "label": "Storage Account Key",
                    "type": "password",
                    "required": False,
                },
                {
                    "name": "connection_string",
                    "label": "Connection String",
                    "type": "text",
                    "required": False,
                    "placeholder": "Alternative to account name/key",
                },
            ]

        elif backend_type == "s3_compatible":
            return [
                {
                    "name": "name",
                    "label": "Backend Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "service",
                    "label": "Service",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"value": "minio", "label": "Minio"},
                        {
                            "value": "backblaze_us_west",
                            "label": "Backblaze B2 (US West)",
                        },
                        {
                            "value": "backblaze_us_east",
                            "label": "Backblaze B2 (US East)",
                        },
                        {
                            "value": "digitalocean_nyc3",
                            "label": "DigitalOcean Spaces (NYC3)",
                        },
                        {"name": "custom", "label": "Custom Endpoint"},
                    ],
                },
                {
                    "name": "bucket",
                    "label": "Bucket Name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "prefix",
                    "label": "Prefix (optional)",
                    "type": "text",
                    "required": False,
                    "placeholder": "kirin",
                },
                {
                    "name": "endpoint_url",
                    "label": "Custom Endpoint URL",
                    "type": "text",
                    "required": False,
                    "placeholder": "https://custom-s3-endpoint.com",
                },
                {
                    "name": "key",
                    "label": "Access Key ID",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "secret",
                    "label": "Secret Access Key",
                    "type": "password",
                    "required": True,
                },
            ]

        else:
            return []
