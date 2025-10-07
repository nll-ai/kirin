"""Tests for partial commit hash resolution functionality."""

import pytest
from unittest.mock import Mock, patch
import pytest
from kirin.dataset import Dataset, DatasetNoCommitsError


class TestPartialHashResolution:
    """Test cases for partial commit hash resolution."""

    def test_resolve_commit_hash_success(self):
        """Test successful resolution of partial hash to full hash."""
        # Mock dataset with sample commit data
        mock_commit_data = {
            "version_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "parent_hash": "",
            "commit_message": "Test commit",
            "file_hashes": [],
        }

        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            # Create a real Dataset instance but mock the filesystem
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            # Mock the glob and file operations
            dataset.fs.glob.return_value = [
                "test-bucket/datasets/test/commit1/commit.json"
            ]

            # Create a proper mock file object with context manager
            mock_file = Mock()
            mock_file.read.return_value = str(mock_commit_data).replace("'", '"')
            dataset.fs.open.return_value.__enter__ = Mock(return_value=mock_file)
            dataset.fs.open.return_value.__exit__ = Mock(return_value=None)

            # Test resolution
            partial_hash = "9f86d081"
            result = dataset.resolve_commit_hash(partial_hash)

            assert result == mock_commit_data["version_hash"]
            dataset.fs.glob.assert_called_once()
            dataset.fs.open.assert_called_once()

    def test_resolve_commit_hash_no_matches(self):
        """Test error when no commits match the partial hash."""
        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            # Mock commit data that doesn't match
            mock_commit_data = {
                "version_hash": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "parent_hash": "",
                "commit_message": "Test commit",
                "file_hashes": [],
            }

            dataset.fs.glob.return_value = [
                "test-bucket/datasets/test/commit1/commit.json"
            ]

            # Create a proper mock file object with context manager
            mock_file = Mock()
            mock_file.read.return_value = str(mock_commit_data).replace("'", '"')
            dataset.fs.open.return_value.__enter__ = Mock(return_value=mock_file)
            dataset.fs.open.return_value.__exit__ = Mock(return_value=None)

            # Test resolution with non-matching partial hash
            with pytest.raises(
                ValueError, match="No commit found matching partial hash"
            ):
                dataset.resolve_commit_hash("nonexistent")

    def test_resolve_commit_hash_multiple_matches(self):
        """Test error when multiple commits match the partial hash."""
        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            # Mock multiple commits with same prefix
            commit1_data = {
                "version_hash": "9f86d0811111111111111111111111111111111111111111111111111111111111",
                "parent_hash": "",
                "commit_message": "Test commit 1",
                "file_hashes": [],
            }
            commit2_data = {
                "version_hash": "9f86d0812222222222222222222222222222222222222222222222222222222222",
                "parent_hash": "",
                "commit_message": "Test commit 2",
                "file_hashes": [],
            }

            dataset.fs.glob.return_value = [
                "test-bucket/datasets/test/commit1/commit.json",
                "test-bucket/datasets/test/commit2/commit.json",
            ]

            # Mock file operations to return different data for each file
            def mock_open_side_effect(path, mode):
                mock_file = Mock()
                if "commit1" in path:
                    mock_file.read.return_value = str(commit1_data).replace("'", '"')
                else:
                    mock_file.read.return_value = str(commit2_data).replace("'", '"')
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock()
                return mock_file

            dataset.fs.open.side_effect = mock_open_side_effect

            # Test resolution with ambiguous partial hash
            with pytest.raises(ValueError, match="Multiple commits match partial hash"):
                dataset.resolve_commit_hash("9f86d081")

    def test_resolve_commit_hash_empty_input(self):
        """Test error when partial hash is empty."""
        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            with pytest.raises(ValueError, match="Partial hash cannot be empty"):
                dataset.resolve_commit_hash("")

    def test_resolve_commit_hash_no_commits(self):
        """Test error when no commits exist in dataset."""
        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            # Mock empty glob result
            dataset.fs.glob.return_value = []

            with pytest.raises(DatasetNoCommitsError):
                dataset.resolve_commit_hash("9f86d081")

    def test_checkout_with_partial_hash(self):
        """Test that checkout method uses hash resolution for partial hashes."""
        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            # Mock the resolve_commit_hash method
            dataset.resolve_commit_hash = Mock(return_value="full_hash_123")

            # Mock DatasetCommit.from_json
            with patch("gitdata.dataset.DatasetCommit.from_json") as mock_from_json:
                mock_commit = Mock()
                mock_from_json.return_value = mock_commit

                # Test checkout with partial hash
                dataset.checkout("partial_hash")

                # Verify resolve_commit_hash was called
                dataset.resolve_commit_hash.assert_called_once_with("partial_hash")

                # Verify DatasetCommit.from_json was called with resolved hash
                mock_from_json.assert_called_once_with(
                    root_dir=dataset.root_dir,
                    dataset_name=dataset.dataset_name,
                    version_hash="full_hash_123",
                    fs=dataset.fs,
                )

                # Verify current_commit was set
                assert dataset.current_commit == mock_commit

    def test_checkout_with_full_hash(self):
        """Test that checkout method works with full hashes without resolution."""
        with patch("gitdata.dataset.Dataset") as mock_dataset_class:
            dataset = Dataset.__new__(Dataset)
            dataset.root_dir = "gs://test-bucket"
            dataset.dataset_name = "test"
            dataset.dataset_dir = "gs://test-bucket/datasets/test"
            dataset.fs = Mock()

            # Mock the resolve_commit_hash method to raise ValueError (simulating full hash)
            dataset.resolve_commit_hash = Mock(
                side_effect=ValueError("Not a partial hash")
            )

            # Mock DatasetCommit.from_json
            with patch("gitdata.dataset.DatasetCommit.from_json") as mock_from_json:
                mock_commit = Mock()
                mock_from_json.return_value = mock_commit

                # Test checkout with full hash
                dataset.checkout("full_hash_123")

                # Verify resolve_commit_hash was called
                dataset.resolve_commit_hash.assert_called_once_with("full_hash_123")

                # Verify DatasetCommit.from_json was called with original hash
                mock_from_json.assert_called_once_with(
                    root_dir=dataset.root_dir,
                    dataset_name=dataset.dataset_name,
                    version_hash="full_hash_123",
                    fs=dataset.fs,
                )

                # Verify current_commit was set
                assert dataset.current_commit == mock_commit
