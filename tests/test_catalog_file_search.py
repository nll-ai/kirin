"""Tests for catalog file search functionality."""

import tempfile
from pathlib import Path

import pytest

from kirin.catalog import Catalog
from kirin.dataset import Dataset
from kirin.file_index import FileIndex


def test_find_datasets_with_file_single_dataset():
    """Test finding datasets with a file in a single dataset."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create catalog and dataset
        catalog = Catalog(root_dir=temp_dir)
        dataset = catalog.create_dataset("test_dataset", "Test dataset")
        
        # Create a test file
        test_file = Path(temp_dir) / "test_data.csv"
        test_file.write_text("col1,col2\n1,2\n3,4\n")
        
        # Commit the file
        commit_hash = dataset.commit(
            message="Initial commit",
            add_files=[str(test_file)]
        )
        
        # Get the file hash from the commit
        commit = dataset.get_commit(commit_hash)
        file_obj = list(commit.files.values())[0]
        file_hash = file_obj.hash
        
        # Search for the file
        results = catalog.find_datasets_with_file(file_hash)
        
        # Verify results
        assert "test_dataset" in results
        assert len(results["test_dataset"]) == 1
        
        commit_entry = results["test_dataset"][0]
        assert commit_entry["commit_hash"] == commit_hash
        assert commit_entry["filenames"] == ["test_data.csv"]


def test_find_datasets_with_file_multiple_datasets():
    """Test finding datasets with a file in multiple datasets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create catalog and datasets
        catalog = Catalog(root_dir=temp_dir)
        dataset1 = catalog.create_dataset("dataset1", "First dataset")
        dataset2 = catalog.create_dataset("dataset2", "Second dataset")
        
        # Create the same test file content
        test_file1 = Path(temp_dir) / "test_data1.csv"
        test_file2 = Path(temp_dir) / "test_data2.csv"
        test_file1.write_text("col1,col2\n1,2\n3,4\n")
        test_file2.write_text("col1,col2\n1,2\n3,4\n")  # Same content
        
        # Commit files to both datasets
        commit1 = dataset1.commit(
            message="Add data to dataset1",
            add_files=[str(test_file1)]
        )
        
        commit2 = dataset2.commit(
            message="Add data to dataset2",
            add_files=[str(test_file2)]
        )
        
        # Get the file hash (should be the same for both)
        commit1_obj = dataset1.get_commit(commit1)
        commit2_obj = dataset2.get_commit(commit2)
        file1_obj = list(commit1_obj.files.values())[0]
        file2_obj = list(commit2_obj.files.values())[0]
        
        # Both files should have the same hash (same content)
        assert file1_obj.hash == file2_obj.hash
        file_hash = file1_obj.hash
        
        # Search for the file
        results = catalog.find_datasets_with_file(file_hash)
        
        # Verify results
        assert len(results) == 2
        assert "dataset1" in results
        assert "dataset2" in results
        
        # Check dataset1 entry
        dataset1_commits = results["dataset1"]
        assert len(dataset1_commits) == 1
        assert dataset1_commits[0]["commit_hash"] == commit1
        assert dataset1_commits[0]["filenames"] == ["test_data1.csv"]
        
        # Check dataset2 entry
        dataset2_commits = results["dataset2"]
        assert len(dataset2_commits) == 1
        assert dataset2_commits[0]["commit_hash"] == commit2
        assert dataset2_commits[0]["filenames"] == ["test_data2.csv"]


def test_find_datasets_with_file_nonexistent():
    """Test finding datasets with a non-existent file hash."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog = Catalog(root_dir=temp_dir)
        
        # Search for non-existent file
        results = catalog.find_datasets_with_file("nonexistent_hash")
        
        # Should return empty results
        assert results == {}


def test_find_datasets_with_file_multiple_commits():
    """Test finding datasets with a file in multiple commits."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create catalog and dataset
        catalog = Catalog(root_dir=temp_dir)
        dataset = catalog.create_dataset("test_dataset", "Test dataset")
        
        # Create test file
        test_file = Path(temp_dir) / "test_data.csv"
        test_file.write_text("col1,col2\n1,2\n3,4\n")
        
        # Commit the file
        commit1 = dataset.commit(
            message="Initial commit",
            add_files=[str(test_file)]
        )
        
        # Get the file hash
        commit1_obj = dataset.get_commit(commit1)
        file_obj = list(commit1_obj.files.values())[0]
        file_hash = file_obj.hash
        
        # Modify the file and commit again
        test_file.write_text("col1,col2\n1,2\n3,4\n5,6\n")  # Different content
        commit2 = dataset.commit(
            message="Updated data",
            add_files=[str(test_file)]
        )
        
        # Get the new file hash
        commit2_obj = dataset.get_commit(commit2)
        file2_obj = list(commit2_obj.files.values())[0]
        file2_hash = file2_obj.hash
        
        # Search for the original file
        results1 = catalog.find_datasets_with_file(file_hash)
        assert "test_dataset" in results1
        assert len(results1["test_dataset"]) == 1
        assert results1["test_dataset"][0]["commit_hash"] == commit1
        
        # Search for the updated file
        results2 = catalog.find_datasets_with_file(file2_hash)
        assert "test_dataset" in results2
        assert len(results2["test_dataset"]) == 1
        assert results2["test_dataset"][0]["commit_hash"] == commit2


def test_find_datasets_with_file_different_filenames():
    """Test finding datasets with the same content but different filenames."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create catalog and dataset
        catalog = Catalog(root_dir=temp_dir)
        dataset = catalog.create_dataset("test_dataset", "Test dataset")
        
        # Create files with same content but different names
        file1 = Path(temp_dir) / "data.csv"
        file2 = Path(temp_dir) / "backup.csv"
        content = "col1,col2\n1,2\n3,4\n"
        file1.write_text(content)
        file2.write_text(content)
        
        # Commit both files
        commit = dataset.commit(
            message="Add files",
            add_files=[str(file1), str(file2)]
        )
        
        # Get the file hash (should be the same for both)
        commit_obj = dataset.get_commit(commit)
        files = list(commit_obj.files.values())
        assert len(files) == 2
        assert files[0].hash == files[1].hash  # Same content
        file_hash = files[0].hash
        
        # Search for the file
        results = catalog.find_datasets_with_file(file_hash)
        
        # Verify results
        assert "test_dataset" in results
        assert len(results["test_dataset"]) == 1
        
        commit_entry = results["test_dataset"][0]
        assert commit_entry["commit_hash"] == commit
        assert set(commit_entry["filenames"]) == {"data.csv", "backup.csv"}


def test_find_datasets_with_file_error_handling():
    """Test error handling in find_datasets_with_file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog = Catalog(root_dir=temp_dir)
        
        # This should not raise an exception, just return empty results
        results = catalog.find_datasets_with_file("invalid_hash")
        assert results == {}


def test_file_index_integration_with_dataset_commit():
    """Test that file index is updated when datasets commit files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create catalog and dataset
        catalog = Catalog(root_dir=temp_dir)
        dataset = catalog.create_dataset("test_dataset", "Test dataset")
        
        # Create a test file
        test_file = Path(temp_dir) / "test_data.csv"
        test_file.write_text("col1,col2\n1,2\n3,4\n")
        
        # Commit the file
        commit_hash = dataset.commit(
            message="Initial commit",
            add_files=[str(test_file)]
        )
        
        # Get the file hash
        commit = dataset.get_commit(commit_hash)
        file_obj = list(commit.files.values())[0]
        file_hash = file_obj.hash
        
        # Verify that the file index was updated
        file_index = FileIndex(temp_dir)
        datasets = file_index.get_datasets_with_file(file_hash)
        
        assert "test_dataset" in datasets
        assert len(datasets["test_dataset"]) == 1
        
        commit_entry = datasets["test_dataset"][0]
        assert commit_entry["commit_hash"] == commit_hash
        assert commit_entry["filenames"] == ["test_data.csv"]


def test_file_index_cleanup_with_orphaned_files():
    """Test that file index is cleaned up when orphaned files are removed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create catalog and dataset
        catalog = Catalog(root_dir=temp_dir)
        dataset = catalog.create_dataset("test_dataset", "Test dataset")
        
        # Create and commit a file
        test_file = Path(temp_dir) / "test_data.csv"
        test_file.write_text("col1,col2\n1,2\n3,4\n")
        
        commit1 = dataset.commit(
            message="Initial commit",
            add_files=[str(test_file)]
        )
        
        # Get the file hash
        commit1_obj = dataset.get_commit(commit1)
        file_obj = list(commit1_obj.files.values())[0]
        file_hash = file_obj.hash
        
        # Verify file is indexed
        file_index = FileIndex(temp_dir)
        datasets = file_index.get_datasets_with_file(file_hash)
        assert "test_dataset" in datasets
        
        # Create a new commit that removes the file
        commit2 = dataset.commit(
            message="Remove file",
            remove_files=["test_data.csv"]
        )
        
        # Clean up orphaned files
        removed_count = dataset.cleanup_orphaned_files()
        assert removed_count > 0
        
        # Verify file is no longer indexed
        datasets = file_index.get_datasets_with_file(file_hash)
        assert "test_dataset" not in datasets