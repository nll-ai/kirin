"""Integration tests for Dataset with metadata and tags support."""

import tempfile
from pathlib import Path

import pytest

from kirin import Dataset


class TestDatasetMetadata:
    """Test Dataset functionality with metadata and tags."""

    def test_commit_with_metadata_and_tags(self):
        """Test committing with metadata and tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = Path(temp_dir) / "model.pt"
            test_file1.write_text("model content")

            test_file2 = Path(temp_dir) / "config.json"
            test_file2.write_text('{"lr": 0.001}')

            # Create dataset
            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Commit with metadata and tags
            metadata = {
                "framework": "pytorch",
                "accuracy": 0.94,
                "hyperparameters": {"lr": 0.001, "epochs": 10},
            }
            tags = ["production", "v2.0"]

            commit_hash = dataset.commit(
                message="Initial model commit",
                add_files=[str(test_file1), str(test_file2)],
                metadata=metadata,
                tags=tags,
            )

            # Verify commit was created
            assert commit_hash is not None
            commit = dataset.get_commit(commit_hash)
            assert commit is not None
            assert commit.metadata == metadata
            assert commit.tags == tags
            assert commit.message == "Initial model commit"

    def test_commit_without_metadata_and_tags(self):
        """Test that commits work without metadata and tags (backward compatibility)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            # Create dataset
            dataset = Dataset(root_dir=temp_dir, name="test_dataset")

            # Commit without metadata/tags
            commit_hash = dataset.commit(
                message="Simple commit",
                add_files=[str(test_file)],
            )

            # Verify commit was created with empty metadata/tags
            commit = dataset.get_commit(commit_hash)
            assert commit is not None
            assert commit.metadata == {}
            assert commit.tags == []
            assert commit.message == "Simple commit"

    def test_find_commits_by_tags(self):
        """Test finding commits by tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Create multiple commits with different tags
            dataset.commit(
                message="Dev commit",
                add_files=[str(test_file)],
                tags=["dev"],
            )

            dataset.commit(
                message="Staging commit",
                add_files=[str(test_file)],
                tags=["staging"],
            )

            dataset.commit(
                message="Production commit",
                add_files=[str(test_file)],
                tags=["production"],
            )

            # Find commits by tags
            dev_commits = dataset.find_commits(tags=["dev"])
            assert len(dev_commits) == 1
            assert dev_commits[0].tags == ["dev"]

            staging_commits = dataset.find_commits(tags=["staging"])
            assert len(staging_commits) == 1
            assert staging_commits[0].tags == ["staging"]

            production_commits = dataset.find_commits(tags=["production"])
            assert len(production_commits) == 1
            assert production_commits[0].tags == ["production"]

            # Find commits with multiple tags
            multi_tag_commits = dataset.find_commits(tags=["dev", "staging"])
            assert len(multi_tag_commits) == 0  # No commit has both tags

    def test_find_commits_by_metadata_filter(self):
        """Test finding commits by metadata filter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Create commits with different metadata
            dataset.commit(
                message="Low accuracy model",
                add_files=[str(test_file)],
                metadata={"accuracy": 0.85, "framework": "pytorch"},
            )

            dataset.commit(
                message="High accuracy model",
                add_files=[str(test_file)],
                metadata={"accuracy": 0.95, "framework": "pytorch"},
            )

            dataset.commit(
                message="TensorFlow model",
                add_files=[str(test_file)],
                metadata={"accuracy": 0.91, "framework": "tensorflow"},
            )

            # Find high accuracy models
            high_accuracy = dataset.find_commits(
                metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
            )
            assert len(high_accuracy) == 2
            assert all(c.metadata["accuracy"] > 0.9 for c in high_accuracy)

            # Find PyTorch models
            pytorch_models = dataset.find_commits(
                metadata_filter=lambda m: m.get("framework") == "pytorch"
            )
            assert len(pytorch_models) == 2
            assert all(c.metadata["framework"] == "pytorch" for c in pytorch_models)

            # Find high accuracy PyTorch models
            high_pytorch = dataset.find_commits(
                metadata_filter=lambda m: (
                    m.get("accuracy", 0) > 0.9 and m.get("framework") == "pytorch"
                )
            )
            assert len(high_pytorch) == 1
            assert high_pytorch[0].metadata["accuracy"] == 0.95

    def test_find_commits_with_limit(self):
        """Test finding commits with limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Create multiple commits
            for i in range(5):
                dataset.commit(
                    message=f"Commit {i}",
                    add_files=[str(test_file)],
                    metadata={"index": i},
                )

            # Find with limit
            limited_commits = dataset.find_commits(limit=3)
            assert len(limited_commits) == 3

            # Should be newest first
            assert limited_commits[0].metadata["index"] == 4
            assert limited_commits[1].metadata["index"] == 3
            assert limited_commits[2].metadata["index"] == 2

    def test_compare_commits(self):
        """Test comparing commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Create first commit
            commit1_hash = dataset.commit(
                message="First commit",
                add_files=[str(test_file)],
                metadata={"accuracy": 0.85, "framework": "pytorch"},
                tags=["dev"],
            )

            # Create second commit
            commit2_hash = dataset.commit(
                message="Second commit",
                add_files=[str(test_file)],
                metadata={"accuracy": 0.95, "framework": "pytorch", "epochs": 100},
                tags=["production"],
            )

            # Compare commits
            comparison = dataset.compare_commits(commit1_hash, commit2_hash)

            # Check basic info
            commit1 = dataset.get_commit(commit1_hash)
            commit2 = dataset.get_commit(commit2_hash)
            assert comparison["commit1"]["hash"] == commit1.short_hash
            assert comparison["commit2"]["hash"] == commit2.short_hash

            # Check metadata diff
            assert comparison["metadata_diff"]["added"] == {"epochs": 100}
            assert comparison["metadata_diff"]["changed"]["accuracy"] == {
                "old": 0.85,
                "new": 0.95,
            }

            # Check tags diff
            assert comparison["tags_diff"]["added"] == ["production"]
            assert comparison["tags_diff"]["removed"] == ["dev"]

    def test_compare_commits_not_found(self):
        """Test comparing commits when one doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Try to compare non-existent commits
            with pytest.raises(ValueError, match="One or both commits not found"):
                dataset.compare_commits("nonexistent1", "nonexistent2")

    def test_round_trip_serialization(self):
        """Test that metadata and tags survive round-trip serialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Create commit with metadata and tags
            metadata = {
                "framework": "pytorch",
                "accuracy": 0.94,
                "nested": {"key": "value"},
            }
            tags = ["production", "v2.0"]

            commit_hash = dataset.commit(
                message="Test commit",
                add_files=[str(test_file)],
                metadata=metadata,
                tags=tags,
            )

            # Create new dataset instance (simulates loading from storage)
            new_dataset = Dataset(root_dir=temp_dir, name="test_model")

            # Verify metadata and tags are preserved
            commit = new_dataset.get_commit(commit_hash)
            assert commit is not None
            assert commit.metadata == metadata
            assert commit.tags == tags
            assert commit.message == "Test commit"
