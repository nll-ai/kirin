"""Tests for Commit entity with metadata and tags support."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from kirin.commit import Commit, CommitBuilder
from kirin.file import File
from kirin.storage import ContentStore


class TestCommitMetadata:
    """Test Commit entity with metadata and tags."""

    def test_commit_creation_with_metadata_and_tags(self):
        """Test creating a commit with metadata and tags."""
        metadata = {
            "framework": "pytorch",
            "accuracy": 0.94,
            "hyperparameters": {"lr": 0.001, "epochs": 10},
        }
        tags = ["production", "v2.0"]

        commit = Commit(
            hash="abc123",
            message="Test commit",
            timestamp=datetime.now(),
            parent_hash=None,
            files={},
            metadata=metadata,
            tags=tags,
        )

        assert commit.metadata == metadata
        assert commit.tags == tags
        assert commit.hash == "abc123"
        assert commit.message == "Test commit"

    def test_commit_creation_with_empty_metadata_and_tags(self):
        """Test creating a commit with empty metadata and tags."""
        commit = Commit(
            hash="abc123",
            message="Test commit",
            timestamp=datetime.now(),
            parent_hash=None,
            files={},
        )

        assert commit.metadata == {}
        assert commit.tags == []
        assert commit.hash == "abc123"

    def test_commit_serialization_with_metadata_and_tags(self):
        """Test serializing and deserializing commits with metadata and tags."""
        metadata = {
            "framework": "pytorch",
            "accuracy": 0.94,
            "nested": {"key": "value"},
        }
        tags = ["production", "v2.0"]

        original_commit = Commit(
            hash="abc123",
            message="Test commit",
            timestamp=datetime.now(),
            parent_hash=None,
            files={},
            metadata=metadata,
            tags=tags,
        )

        # Test to_dict
        commit_dict = original_commit.to_dict()
        assert commit_dict["metadata"] == metadata
        assert commit_dict["tags"] == tags
        assert "hash" in commit_dict
        assert "message" in commit_dict

        # Test from_dict
        restored_commit = Commit.from_dict(commit_dict)
        assert restored_commit.metadata == metadata
        assert restored_commit.tags == tags
        assert restored_commit.hash == original_commit.hash
        assert restored_commit.message == original_commit.message

    def test_commit_backward_compatibility(self):
        """Test that old commits without metadata/tags load correctly."""
        # Simulate old commit data without metadata/tags
        old_commit_data = {
            "hash": "abc123",
            "message": "Old commit",
            "timestamp": datetime.now().isoformat(),
            "parent_hash": None,
            "files": {},
        }

        # Should load with empty defaults
        commit = Commit.from_dict(old_commit_data)
        assert commit.metadata == {}
        assert commit.tags == []
        assert commit.hash == "abc123"
        assert commit.message == "Old commit"

    def test_commit_immutability(self):
        """Test that commit fields are immutable."""
        metadata = {"key": "value"}
        tags = ["tag1", "tag2"]

        commit = Commit(
            hash="abc123",
            message="Test commit",
            timestamp=datetime.now(),
            parent_hash=None,
            files={},
            metadata=metadata,
            tags=tags,
        )

        # Should not be able to modify commit fields
        with pytest.raises(AttributeError):
            commit.hash = "new_hash"

        with pytest.raises(AttributeError):
            commit.message = "new_message"

        # Note: metadata and tags are dictionaries/lists, so their contents
        # can be modified, but the commit itself is frozen
        # This is expected behavior for frozen dataclasses


class TestCommitBuilderMetadata:
    """Test CommitBuilder with metadata and tags support."""

    def test_commit_builder_with_metadata_and_tags(self):
        """Test building commits with metadata and tags."""
        metadata = {
            "framework": "pytorch",
            "accuracy": 0.94,
        }
        tags = ["production", "v2.0"]

        builder = CommitBuilder()
        builder.set_metadata(metadata)
        builder.add_tags(tags)

        commit = builder("Test commit")

        assert commit.metadata == metadata
        assert commit.tags == tags
        assert commit.message == "Test commit"

    def test_commit_builder_inherits_from_parent(self):
        """Test that CommitBuilder inherits metadata/tags from parent commit."""
        parent_metadata = {"parent_key": "parent_value"}
        parent_tags = ["parent_tag"]

        parent_commit = Commit(
            hash="parent123",
            message="Parent commit",
            timestamp=datetime.now(),
            parent_hash=None,
            files={},
            metadata=parent_metadata,
            tags=parent_tags,
        )

        builder = CommitBuilder(parent_commit)
        # Don't set new metadata/tags, should inherit from parent
        commit = builder("Child commit")

        # Should inherit from parent
        assert commit.metadata == parent_metadata
        assert commit.tags == parent_tags

    def test_commit_builder_overrides_parent(self):
        """Test that CommitBuilder can override parent metadata/tags."""
        parent_metadata = {"parent_key": "parent_value"}
        parent_tags = ["parent_tag"]

        parent_commit = Commit(
            hash="parent123",
            message="Parent commit",
            timestamp=datetime.now(),
            parent_hash=None,
            files={},
            metadata=parent_metadata,
            tags=parent_tags,
        )

        new_metadata = {"new_key": "new_value"}
        new_tags = ["new_tag"]

        builder = CommitBuilder(parent_commit)
        builder.set_metadata(new_metadata)
        builder.add_tags(new_tags)

        commit = builder("Child commit")

        # Should use new values, not parent values
        assert commit.metadata == new_metadata
        assert commit.tags == new_tags

    def test_commit_builder_method_chaining(self):
        """Test that CommitBuilder methods support chaining."""
        metadata = {"key": "value"}
        tags = ["tag1", "tag2"]

        builder = CommitBuilder()
        result = builder.set_metadata(metadata).add_tags(tags)

        # Should return self for chaining
        assert result is builder
        assert builder.metadata == metadata
        assert builder.tags == tags

    def test_commit_builder_with_files_and_metadata(self):
        """Test CommitBuilder with both files and metadata/tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            # Create storage
            storage = ContentStore(temp_dir)

            # Store file
            content_hash = storage.store_content(b"test content", "test.txt")
            file_obj = File(
                hash=content_hash,
                name="test.txt",
                size=12,
                _storage=storage,
            )

            metadata = {"framework": "pytorch"}
            tags = ["test"]

            builder = CommitBuilder()
            builder.add_file("test.txt", file_obj)
            builder.set_metadata(metadata)
            builder.add_tags(tags)

            commit = builder("Test commit with files and metadata")

            assert commit.metadata == metadata
            assert commit.tags == tags
            assert "test.txt" in commit.files
            assert commit.files["test.txt"] == file_obj
