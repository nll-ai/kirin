"""Pytest configuration for web UI tests."""

import pytest
from kirin.web.app import catalog_manager


@pytest.fixture(autouse=True, scope="session")
def reset_catalog_manager():
    """Reset catalog manager state at the start of test session for isolation."""
    # Store original catalogs
    original_catalogs = catalog_manager._load_catalogs()

    # Clear the catalog manager at the start of test session
    catalog_manager._save_catalogs([])

    yield

    # Restore original catalogs after all tests
    catalog_manager._save_catalogs(original_catalogs)
