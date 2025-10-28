"""Tests for FileIndex class."""

import json
import tempfile
from pathlib import Path

import pytest

from kirin.file_index import FileIndex


def test_file_index_initialization():
    """Test FileIndex initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        assert file_index.root_dir == temp_dir
        assert file_index.index_dir == f"{temp_dir}/index/files"
        assert file_index.fs is not None


def test_add_file_reference():
    """Test adding file references to the index."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add a file reference
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        # Check that the index file was created
        index_path = file_index.get_index_path("abc123def456")
        assert Path(index_path).exists()
        
        # Check the content
        with open(index_path, "r") as f:
            data = json.load(f)
        
        assert data["file_hash"] == "abc123def456"
        assert "test_dataset" in data["datasets"]
        assert len(data["datasets"]["test_dataset"]) == 1
        
        commit_entry = data["datasets"]["test_dataset"][0]
        assert commit_entry["commit_hash"] == "commit123"
        assert commit_entry["timestamp"] == "2024-01-01T12:00:00"
        assert commit_entry["filenames"] == ["data.csv"]


def test_add_multiple_file_references():
    """Test adding multiple file references for the same file hash."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add references from different datasets
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="dataset1",
            commit_hash="commit1",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="dataset2",
            commit_hash="commit2",
            timestamp="2024-01-02T10:00:00",
            filename="results.csv"
        )
        
        # Check that both datasets are indexed
        datasets = file_index.get_datasets_with_file("abc123def456")
        assert "dataset1" in datasets
        assert "dataset2" in datasets
        assert len(datasets["dataset1"]) == 1
        assert len(datasets["dataset2"]) == 1


def test_add_same_commit_multiple_filenames():
    """Test adding multiple filenames for the same commit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add first filename
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        # Add second filename for same commit
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="backup.csv"
        )
        
        # Check that both filenames are in the same commit entry
        datasets = file_index.get_datasets_with_file("abc123def456")
        commit_entry = datasets["test_dataset"][0]
        assert set(commit_entry["filenames"]) == {"data.csv", "backup.csv"}


def test_remove_file_reference():
    """Test removing file references from the index."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add a file reference
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        # Verify it exists
        datasets = file_index.get_datasets_with_file("abc123def456")
        assert "test_dataset" in datasets
        
        # Remove the reference
        file_index.remove_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123"
        )
        
        # Verify it's gone
        datasets = file_index.get_datasets_with_file("abc123def456")
        assert "test_dataset" not in datasets


def test_remove_file_reference_removes_empty_dataset():
    """Test that removing the last commit for a dataset removes the dataset entry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add a file reference
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        # Remove the reference
        file_index.remove_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123"
        )
        
        # Check that the index file is deleted (no datasets remain)
        index_path = file_index.get_index_path("abc123def456")
        assert not Path(index_path).exists()


def test_get_datasets_with_file():
    """Test querying datasets containing a specific file hash."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add references from multiple datasets
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="dataset1",
            commit_hash="commit1",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="dataset2",
            commit_hash="commit2",
            timestamp="2024-01-02T10:00:00",
            filename="results.csv"
        )
        
        # Query the file hash
        datasets = file_index.get_datasets_with_file("abc123def456")
        
        assert len(datasets) == 2
        assert "dataset1" in datasets
        assert "dataset2" in datasets
        
        # Check dataset1 entry
        dataset1_commits = datasets["dataset1"]
        assert len(dataset1_commits) == 1
        assert dataset1_commits[0]["commit_hash"] == "commit1"
        assert dataset1_commits[0]["filenames"] == ["data.csv"]
        
        # Check dataset2 entry
        dataset2_commits = datasets["dataset2"]
        assert len(dataset2_commits) == 1
        assert dataset2_commits[0]["commit_hash"] == "commit2"
        assert dataset2_commits[0]["filenames"] == ["results.csv"]


def test_get_datasets_with_file_nonexistent():
    """Test querying for a file hash that doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Query non-existent file hash
        datasets = file_index.get_datasets_with_file("nonexistent")
        assert datasets == {}


def test_sharded_storage():
    """Test that files are stored in sharded directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add a file reference
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        # Check that the file is stored in the correct sharded location
        expected_path = f"{temp_dir}/index/files/ab/c123def456.json"
        assert Path(expected_path).exists()
        
        # Check that the directory structure is correct
        assert Path(f"{temp_dir}/index/files/ab").is_dir()


def test_list_file_hashes():
    """Test listing all file hashes in the index."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Initially empty
        hashes = file_index.list_file_hashes()
        assert hashes == []
        
        # Add some file references
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="dataset1",
            commit_hash="commit1",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        file_index.add_file_reference(
            file_hash="def456ghi789",
            dataset_name="dataset2",
            commit_hash="commit2",
            timestamp="2024-01-02T10:00:00",
            filename="results.csv"
        )
        
        # Check that both hashes are listed
        hashes = file_index.list_file_hashes()
        assert len(hashes) == 2
        assert "abc123def456" in hashes
        assert "def456ghi789" in hashes


def test_cleanup_orphaned_entries():
    """Test cleaning up orphaned index entries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add some file references
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="dataset1",
            commit_hash="commit1",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        file_index.add_file_reference(
            file_hash="def456ghi789",
            dataset_name="dataset2",
            commit_hash="commit2",
            timestamp="2024-01-02T10:00:00",
            filename="results.csv"
        )
        
        # Verify both exist
        hashes = file_index.list_file_hashes()
        assert len(hashes) == 2
        
        # Clean up with only one hash still in use
        used_hashes = {"abc123def456"}
        removed_count = file_index.cleanup_orphaned_entries(used_hashes)
        
        # Check that one entry was removed
        assert removed_count == 1
        
        # Check that only the used hash remains
        hashes = file_index.list_file_hashes()
        assert len(hashes) == 1
        assert "abc123def456" in hashes
        assert "def456ghi789" not in hashes


def test_load_index_handles_missing_file():
    """Test that loading index handles missing files gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Try to load index for non-existent file
        data = file_index.load_index("nonexistent")
        assert data == {}


def test_save_and_load_index():
    """Test saving and loading index data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Create test data
        test_data = {
            "file_hash": "abc123def456",
            "datasets": {
                "dataset1": [
                    {
                        "commit_hash": "commit1",
                        "timestamp": "2024-01-01T12:00:00",
                        "filenames": ["data.csv"]
                    }
                ]
            }
        }
        
        # Save the data
        file_index.save_index("abc123def456", test_data)
        
        # Load it back
        loaded_data = file_index.load_index("abc123def456")
        
        # Verify it matches
        assert loaded_data == test_data


def test_delete_index():
    """Test deleting index files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Add a file reference
        file_index.add_file_reference(
            file_hash="abc123def456",
            dataset_name="test_dataset",
            commit_hash="commit123",
            timestamp="2024-01-01T12:00:00",
            filename="data.csv"
        )
        
        # Verify it exists
        index_path = file_index.get_index_path("abc123def456")
        assert Path(index_path).exists()
        
        # Delete it
        file_index.delete_index("abc123def456")
        
        # Verify it's gone
        assert not Path(index_path).exists()


def test_index_path_calculation():
    """Test that index paths are calculated correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_index = FileIndex(temp_dir)
        
        # Test various hash lengths
        test_cases = [
            ("abc123def456", f"{temp_dir}/index/files/ab/c123def456.json"),
            ("a", f"{temp_dir}/index/files/a/.json"),
            ("ab", f"{temp_dir}/index/files/ab/.json"),
            ("abcdef", f"{temp_dir}/index/files/ab/cdef.json"),
        ]
        
        for file_hash, expected_path in test_cases:
            actual_path = file_index.get_index_path(file_hash)
            assert actual_path == expected_path