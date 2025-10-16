"""Test the simplified Git-based implementation."""

import tempfile
from pathlib import Path

from kirin.dataset import Dataset, Commit, BlobStorage


def test_git_dataset_basic_workflow():
    """Test basic Dataset workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dataset
        dataset = Dataset(
            root_dir=temp_dir,
            name="test_dataset",
            description="Test dataset for Git implementation"
        )

        # Initially no commits
        assert dataset.current_commit is None
        assert len(dataset.list_files()) == 0

        # Create test files
        test_file1 = Path(temp_dir) / "test1.txt"
        test_file2 = Path(temp_dir) / "test2.txt"

        test_file1.write_text("Hello from test1")
        test_file2.write_text("Hello from test2")

        # First commit
        commit_hash1 = dataset.commit(
            message="Initial commit",
            add_files=[test_file1, test_file2]
        )

        # Verify commit
        assert len(commit_hash1) == 40  # Git SHA-1
        assert dataset.current_commit is not None
        assert dataset.current_commit.hash == commit_hash1
        assert len(dataset.list_files()) == 2
        assert "test1.txt" in dataset.list_files()
        assert "test2.txt" in dataset.list_files()

        # Verify file content
        assert dataset.read_file("test1.txt") == "Hello from test1"
        assert dataset.read_file("test2.txt") == "Hello from test2"

        # Add another file
        test_file3 = Path(temp_dir) / "test3.txt"
        test_file3.write_text("Hello from test3")

        commit_hash2 = dataset.commit(
            message="Add test3",
            add_files=[test_file3]
        )

        # Verify second commit
        assert len(dataset.list_files()) == 3
        assert "test3.txt" in dataset.list_files()
        assert dataset.read_file("test3.txt") == "Hello from test3"

        # Remove a file
        commit_hash3 = dataset.commit(
            message="Remove test2",
            remove_files=["test2.txt"]
        )

        # Verify removal
        assert len(dataset.list_files()) == 2
        assert "test2.txt" not in dataset.list_files()
        assert "test1.txt" in dataset.list_files()
        assert "test3.txt" in dataset.list_files()


def test_git_dataset_history():
    """Test commit history functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, name="history_test")

        # Create multiple commits
        for i in range(3):
            test_file = Path(temp_dir) / f"file{i}.txt"
            test_file.write_text(f"Content {i}")
            dataset.commit(
                message=f"Commit {i}",
                add_files=[test_file]
            )

        # Check history
        history = dataset.history()
        assert len(history) == 3

        # Verify commit order (newest first)
        assert history[0].message == "Commit 2"
        assert history[1].message == "Commit 1"
        assert history[2].message == "Commit 0"

        # Test limited history
        limited_history = dataset.history(limit=2)
        assert len(limited_history) == 2
        assert limited_history[0].message == "Commit 2"
        assert limited_history[1].message == "Commit 1"

        # Test commit properties
        latest_commit = history[0]
        assert len(latest_commit.hash) == 40
        assert len(latest_commit.short_hash) == 8
        assert latest_commit.is_initial is False

        earliest_commit = history[-1]
        assert earliest_commit.is_initial is True
        assert earliest_commit.parent_hash is None


def test_git_dataset_branching():
    """Test basic branching functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, name="branch_test")

        # Create initial commit
        test_file = Path(temp_dir) / "initial.txt"
        test_file.write_text("Initial content")
        dataset.commit(message="Initial commit", add_files=[test_file])

        # Initially on main/master branch
        current_branch = dataset.current_branch()
        assert current_branch in ["main", "master"]

        # Create new branch
        dataset.create_branch("feature")
        dataset.checkout_branch("feature")

        # Verify branch switch
        assert dataset.current_branch() == "feature"

        # List branches
        branches = dataset.list_branches()
        assert "feature" in branches
        assert current_branch in branches

        # Add commit on feature branch
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature content")
        dataset.commit(message="Feature commit", add_files=[feature_file])

        # Verify file exists on feature branch
        assert "feature.txt" in dataset.list_files()

        # Switch back to main
        dataset.checkout_branch(current_branch)
        assert dataset.current_branch() == current_branch

        # Verify feature file doesn't exist on main
        assert "feature.txt" not in dataset.list_files()

        # Switch back to feature
        dataset.checkout_branch("feature")
        assert "feature.txt" in dataset.list_files()


def test_git_blob_storage():
    """Test BlobStorage functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, name="blob_test")

        # Create a file and commit it
        test_file = Path(temp_dir) / "test.txt"
        test_content = b"Test blob content"
        test_file.write_bytes(test_content)

        dataset.commit(message="Test commit", add_files=[test_file])

        # Get the file object
        file_obj = dataset.get_file("test.txt")
        assert file_obj is not None

        # Test blob storage directly
        blob_storage = BlobStorage(dataset.repo)

        # Verify blob exists
        assert blob_storage.exists(file_obj.hash)

        # Retrieve blob content
        retrieved_content = blob_storage.retrieve(file_obj.hash)
        assert retrieved_content == test_content

        # Test non-existent blob
        fake_hash = "0" * 40
        assert not blob_storage.exists(fake_hash)


def test_git_commit_properties():
    """Test Commit object properties."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, name="commit_test")

        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content")

        # Create commit
        commit_hash = dataset.commit(
            message="Test commit message",
            add_files=[test_file]
        )

        commit = dataset.current_commit
        assert commit is not None

        # Test commit properties
        assert commit.hash == commit_hash
        assert len(commit.short_hash) == 8
        assert commit.short_hash == commit_hash[:8]
        assert commit.message == "Test commit message"
        assert commit.is_initial is True
        assert commit.parent_hash is None

        # Test file access through commit
        assert commit.has_file("test.txt")
        assert not commit.has_file("nonexistent.txt")
        assert len(commit.list_files()) == 1
        assert commit.get_file_count() == 1
        assert commit.get_total_size() > 0

        file_obj = commit.get_file("test.txt")
        assert file_obj is not None
        assert file_obj.name == "test.txt"
        assert file_obj.read_bytes() == b"Test content"

        # Test commit serialization
        commit_dict = commit.to_dict()
        assert commit_dict["hash"] == commit_hash
        assert commit_dict["message"] == "Test commit message"
        assert "test.txt" in commit_dict["files"]


def test_dataset_file_context():
    """Test file context manager functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, name="context_test")

        # Create and commit a file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello, context manager!"
        test_file.write_text(test_content)

        dataset.commit(message="Test commit", add_files=[test_file])

        # Test file context manager
        with dataset.file_context("test.txt") as temp_path:
            assert temp_path.exists()
            assert temp_path.read_text() == test_content
            # File should exist during context

        # File should be cleaned up after context
        assert not temp_path.exists()


def test_dataset_download_file():
    """Test file download functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, name="download_test")

        # Create and commit a file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello, download!"
        test_file.write_text(test_content)

        dataset.commit(message="Test commit", add_files=[test_file])

        # Test download
        download_dir = Path(temp_dir) / "downloads"
        download_path = dataset.download_file("test.txt", download_dir / "downloaded.txt")

        assert Path(download_path).exists()
        assert Path(download_path).read_text() == test_content