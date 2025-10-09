"""Pytest configuration and fixtures for Kirin tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
