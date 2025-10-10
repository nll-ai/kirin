"""Secure credential storage using OS keyring."""

import json
from typing import Dict, Optional

import keyring
from loguru import logger


def store_backend_credentials(backend_id: str, credentials: Dict[str, str]) -> None:
    """Store backend credentials in OS keyring.

    Args:
        backend_id: Unique identifier for the backend
        credentials: Dictionary of credential key-value pairs
    """
    try:
        service_name = f"kirin:backend:{backend_id}"
        username = backend_id
        password = json.dumps(credentials)

        keyring.set_password(service_name, username, password)
        logger.info(f"Stored credentials for backend: {backend_id}")

    except Exception as e:
        logger.error(f"Failed to store credentials for backend {backend_id}: {e}")
        raise


def get_backend_credentials(backend_id: str) -> Optional[Dict[str, str]]:
    """Retrieve backend credentials from OS keyring.

    Args:
        backend_id: Unique identifier for the backend

    Returns:
        Dictionary of credentials if found, None otherwise
    """
    try:
        service_name = f"kirin:backend:{backend_id}"
        username = backend_id

        password = keyring.get_password(service_name, username)
        if password is None:
            return None

        credentials = json.loads(password)
        logger.debug(f"Retrieved credentials for backend: {backend_id}")
        return credentials

    except json.JSONDecodeError as e:
        logger.error(f"Failed to deserialize credentials for backend {backend_id}: {e}")
        return None
    except ImportError:
        # Re-raise ImportError to indicate keyring is unavailable
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve credentials for backend {backend_id}: {e}")
        return None


def delete_backend_credentials(backend_id: str) -> None:
    """Delete backend credentials from OS keyring.

    Args:
        backend_id: Unique identifier for the backend
    """
    try:
        service_name = f"kirin:backend:{backend_id}"
        username = backend_id

        keyring.delete_password(service_name, username)
        logger.info(f"Deleted credentials for backend: {backend_id}")

    except Exception as e:
        logger.error(f"Failed to delete credentials for backend {backend_id}: {e}")
        raise


def has_backend_credentials(backend_id: str) -> bool:
    """Check if backend credentials exist in OS keyring.

    Args:
        backend_id: Unique identifier for the backend

    Returns:
        True if credentials exist, False otherwise
    """
    try:
        service_name = f"kirin:backend:{backend_id}"
        username = backend_id

        password = keyring.get_password(service_name, username)
        return password is not None

    except Exception as e:
        logger.error(f"Failed to check credentials for backend {backend_id}: {e}")
        return False
