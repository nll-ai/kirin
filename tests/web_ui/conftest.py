"""Pytest configuration for web UI tests."""

import pytest
from kirin.web.app import backend_manager, dataset_cache


@pytest.fixture(autouse=True, scope="session")
def reset_backend_manager():
    """Reset backend manager state at the start of test session for isolation."""
    # Store original backends
    original_backends = backend_manager._load_backends()

    # Clear the backend manager at the start of test session
    backend_manager._save_backends([])

    yield

    # Restore original backends after all tests
    backend_manager._save_backends(original_backends)


@pytest.fixture(autouse=True)
def clear_dataset_cache():
    """Clear dataset cache between tests for isolation."""
    # Clear dataset cache before each test
    dataset_cache.clear()

    yield

    # Clear dataset cache after each test
    dataset_cache.clear()
