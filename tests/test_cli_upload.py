"""Tests for the CLI upload command."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from kirin.cli import app
from kirin.web.config import CatalogConfig, CatalogManager


@pytest.fixture
def temp_catalog_manager(temp_dir):
    """Create a temporary catalog manager for testing."""
    manager = CatalogManager(config_dir=temp_dir)
    # Clear any existing catalogs
    manager.clear_all_catalogs()
    return manager


def test_upload_command_single_file(temp_dir, tmp_path, temp_catalog_manager):
    """Test uploading a single file via CLI."""
    # Setup: Create catalog config and test file
    catalog_root = temp_dir / "catalog"
    catalog_root.mkdir()

    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Add catalog to manager
    catalog_config = CatalogConfig(
        id="test-catalog", name="Test Catalog", root_dir=str(catalog_root)
    )
    temp_catalog_manager.add_catalog(catalog_config)

    # Execute: Run upload command using Typer testing
    runner = CliRunner()

    # Mock the CatalogManager to use our test manager
    with patch("kirin.cli.CatalogManager") as mock_manager_class:
        mock_manager = mock_manager_class.return_value
        mock_manager.get_catalog.return_value = catalog_config

        result = runner.invoke(
            app,
            [
                "upload",
                "--catalog",
                "test-catalog",
                "--dataset",
                "my_dataset",
                "--commit-message",
                "Add test file",
                str(test_file),
            ],
        )

    # Verify: Check success and file uploaded
    assert result.exit_code == 0
    assert "✓ Uploaded 1 file(s) to my_dataset" in result.stdout
    assert "Commit:" in result.stdout

    # Verify file in dataset
    from kirin.catalog import Catalog

    catalog = Catalog(root_dir=str(catalog_root))
    dataset = catalog.get_dataset("my_dataset")
    assert dataset.has_file("test.txt")


def test_upload_command_missing_catalog(tmp_path):
    """Test error when catalog not found."""
    # Setup: Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Execute: Run upload command with non-existent catalog
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "upload",
            "--catalog",
            "nonexistent-catalog",
            "--dataset",
            "my_dataset",
            "--commit-message",
            "Add test file",
            str(test_file),
        ],
    )

    # Verify: Check error
    assert result.exit_code != 0
    assert "Catalog not found" in result.stderr


def test_upload_command_missing_file(temp_dir, temp_catalog_manager):
    """Test error when file doesn't exist."""
    # Setup: Create catalog config
    catalog_root = temp_dir / "catalog"
    catalog_root.mkdir()

    catalog_config = CatalogConfig(
        id="test-catalog", name="Test Catalog", root_dir=str(catalog_root)
    )
    temp_catalog_manager.add_catalog(catalog_config)

    # Execute: Run upload command with non-existent file
    runner = CliRunner()

    # Mock the CatalogManager to use our test manager
    with patch("kirin.cli.CatalogManager") as mock_manager_class:
        mock_manager = mock_manager_class.return_value
        mock_manager.get_catalog.return_value = catalog_config

        result = runner.invoke(
            app,
            [
                "upload",
                "--catalog",
                "test-catalog",
                "--dataset",
                "my_dataset",
                "--commit-message",
                "Add missing file",
                "/nonexistent/file.txt",
            ],
        )

    # Verify: Check error
    assert result.exit_code != 0
    assert "File not found" in result.stderr


def test_upload_command_no_files_provided(temp_dir, temp_catalog_manager):
    """Test error when no files are provided."""
    # Setup: Create catalog config
    catalog_root = temp_dir / "catalog"
    catalog_root.mkdir()

    catalog_config = CatalogConfig(
        id="test-catalog", name="Test Catalog", root_dir=str(catalog_root)
    )
    temp_catalog_manager.add_catalog(catalog_config)

    # Execute: Run upload command without files
    runner = CliRunner()

    # Mock the CatalogManager to use our test manager
    with patch("kirin.cli.CatalogManager") as mock_manager_class:
        mock_manager = mock_manager_class.return_value
        mock_manager.get_catalog.return_value = catalog_config

        result = runner.invoke(
            app,
            [
                "upload",
                "--catalog",
                "test-catalog",
                "--dataset",
                "my_dataset",
                "--commit-message",
                "No files",
            ],
        )

    # Verify: Check error
    assert result.exit_code != 0
    assert "Missing argument" in result.stderr


def test_upload_command_help():
    """Test that upload command shows help."""
    runner = CliRunner()
    result = runner.invoke(app, ["upload", "--help"])

    # Verify: Check help output
    assert result.exit_code == 0
    assert "Upload files to a dataset in a catalog" in result.stdout
    assert "--catalog" in result.stdout
    assert "--dataset" in result.stdout
    assert "--commit-message" in result.stdout
