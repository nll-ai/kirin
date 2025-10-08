"""Pytest configuration and fixtures for Kirin tests."""

import shutil
import tempfile
from pathlib import Path

import pytest

from kirin import Dataset


@pytest.fixture(autouse=False)
def cleanup_local_state():
    """Automatically clean up local state before each test."""
    # Clean up all local state directories
    local_state_base = Path.home() / ".gitdata"
    if local_state_base.exists():
        for item in local_state_base.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)

    yield

    # Clean up after test as well
    if local_state_base.exists():
        for item in local_state_base.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)


@pytest.fixture
def temp_dataset():
    """Create a temporary dataset for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")
        yield dataset
