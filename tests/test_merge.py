"""Tests for merge functionality in GitData."""

import os
import tempfile
from pathlib import Path

import pytest

from gitdata.dataset import Dataset


def test_merge_no_conflicts():
    """Test merging branches with no conflicts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add initial files to main branch
        main_file = Path(temp_dir) / "main.txt"
        main_file.write_text("Main branch content")

        dataset.commit("Initial commit", add_files=str(main_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Add a file to feature branch
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature branch content")

        dataset.commit("Add feature file", add_files=str(feature_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Merge feature into main
        result = dataset.merge("feature", "main")

        # Check merge result
        assert result["success"] is True
        assert result["source_branch"] == "feature"
        assert result["target_branch"] == "main"
        assert len(result["conflicts"]) == 0
        assert "merge_commit" in result

        # Check that both files are now in main
        dataset.checkout(dataset.current_version_hash())
        files = dataset.file_dict
        assert "main.txt" in files
        assert "feature.txt" in files


def test_merge_with_conflicts():
    """Test merging branches with file conflicts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add a file to main branch
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main branch version")

        dataset.commit("Initial commit", add_files=str(shared_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Modify the same file in feature branch
        shared_file.write_text("Feature branch version")
        dataset.commit("Modify shared file", add_files=str(shared_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Merge feature into main
        result = dataset.merge("feature", "main")

        # Check merge result
        assert result["success"] is True
        assert result["source_branch"] == "feature"
        assert result["target_branch"] == "main"
        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["filename"] == "shared.txt"
        assert "merge_commit" in result

        # Check that the resolved file is in the merge commit
        dataset.checkout(result["merge_commit"])
        files = dataset.file_dict
        assert "shared.txt" in files


def test_merge_strategy_ours():
    """Test merge with 'ours' strategy (keep target branch version)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add a file to main branch
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main branch version")

        dataset.commit("Initial commit", add_files=str(shared_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Modify the same file in feature branch
        shared_file.write_text("Feature branch version")
        dataset.commit("Modify shared file", add_files=str(shared_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Merge with 'ours' strategy
        result = dataset.merge("feature", "main", strategy="ours")

        # Check merge result
        assert result["success"] is True
        assert len(result["conflicts"]) == 1
        assert "resolved_files" in result
        assert "shared.txt" in result["resolved_files"]

        # Check that the target branch version was kept
        dataset.checkout(result["merge_commit"])
        with dataset.local_files() as local_files:
            shared_path = local_files["shared.txt"]
            content = Path(shared_path).read_text()
            assert "Main branch version" in content


def test_merge_strategy_theirs():
    """Test merge with 'theirs' strategy (keep source branch version)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add a file to main branch
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main branch version")

        dataset.commit("Initial commit", add_files=str(shared_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Modify the same file in feature branch
        shared_file.write_text("Feature branch version")
        dataset.commit("Modify shared file", add_files=str(shared_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Merge with 'theirs' strategy
        result = dataset.merge("feature", "main", strategy="theirs")

        # Check merge result
        assert result["success"] is True
        assert len(result["conflicts"]) == 1
        assert "resolved_files" in result
        assert "shared.txt" in result["resolved_files"]

        # Check that the source branch version was kept
        dataset.checkout(result["merge_commit"])
        with dataset.local_files() as local_files:
            shared_path = local_files["shared.txt"]
            content = Path(shared_path).read_text()
            assert "Feature branch version" in content


def test_merge_manual_strategy():
    """Test merge with 'manual' strategy (requires manual resolution)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add a file to main branch
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main branch version")

        dataset.commit("Initial commit", add_files=str(shared_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Modify the same file in feature branch
        shared_file.write_text("Feature branch version")
        dataset.commit("Modify shared file", add_files=str(shared_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Merge with 'manual' strategy
        result = dataset.merge("feature", "main", strategy="manual")

        # Check merge result
        assert result["success"] is False
        assert result["requires_manual_resolution"] is True
        assert len(result["conflicts"]) == 1
        assert "merge_commit" not in result


def test_merge_nonexistent_branches():
    """Test merge with non-existent branches."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add initial commit
        main_file = Path(temp_dir) / "main.txt"
        main_file.write_text("Main branch content")
        dataset.commit("Initial commit", add_files=str(main_file))

        # Try to merge non-existent source branch
        with pytest.raises(
            ValueError, match="Source branch 'nonexistent' does not exist"
        ):
            dataset.merge("nonexistent", "main")

        # Try to merge into non-existent target branch
        with pytest.raises(
            ValueError, match="Target branch 'nonexistent' does not exist"
        ):
            dataset.merge("main", "nonexistent")


def test_merge_same_branch():
    """Test merging a branch into itself."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add initial commit
        main_file = Path(temp_dir) / "main.txt"
        main_file.write_text("Main branch content")
        dataset.commit("Initial commit", add_files=str(main_file))

        # Try to merge main into main
        result = dataset.merge("main", "main")

        # Should succeed with no conflicts
        assert result["success"] is True
        assert len(result["conflicts"]) == 0


def test_merge_detect_conflicts():
    """Test conflict detection between two commits."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add a file to main branch
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main branch version")

        dataset.commit("Initial commit", add_files=str(shared_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Modify the same file in feature branch
        shared_file.write_text("Feature branch version")
        dataset.commit("Modify shared file", add_files=str(shared_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Get commits for conflict detection
        source_commit_hash = dataset.get_branch_commit("feature")
        target_commit_hash = dataset.get_branch_commit("main")

        from gitdata.dataset import DatasetCommit

        source_commit = DatasetCommit.from_json(
            root_dir=dataset.root_dir,
            dataset_name=dataset.dataset_name,
            version_hash=source_commit_hash,
            fs=dataset.fs,
        )
        target_commit = DatasetCommit.from_json(
            root_dir=dataset.root_dir,
            dataset_name=dataset.dataset_name,
            version_hash=target_commit_hash,
            fs=dataset.fs,
        )

        # Detect conflicts
        conflicts = dataset._detect_merge_conflicts(source_commit, target_commit)

        # Check conflicts
        assert len(conflicts) == 1
        assert conflicts[0]["filename"] == "shared.txt"
        assert conflicts[0]["source_hash"] != conflicts[0]["target_hash"]


def test_merge_resolve_conflicts():
    """Test conflict resolution with different strategies."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add a file to main branch
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main branch version")

        dataset.commit("Initial commit", add_files=str(shared_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Modify the same file in feature branch
        shared_file.write_text("Feature branch version")
        dataset.commit("Modify shared file", add_files=str(shared_file))

        # Switch back to main
        dataset.switch_branch("main")

        # Get commits for conflict resolution
        source_commit_hash = dataset.get_branch_commit("feature")
        target_commit_hash = dataset.get_branch_commit("main")

        from gitdata.dataset import DatasetCommit

        source_commit = DatasetCommit.from_json(
            root_dir=dataset.root_dir,
            dataset_name=dataset.dataset_name,
            version_hash=source_commit_hash,
            fs=dataset.fs,
        )
        target_commit = DatasetCommit.from_json(
            root_dir=dataset.root_dir,
            dataset_name=dataset.dataset_name,
            version_hash=target_commit_hash,
            fs=dataset.fs,
        )

        # Detect conflicts
        conflicts = dataset._detect_merge_conflicts(source_commit, target_commit)

        # Test 'ours' strategy
        resolved_files_ours = dataset._resolve_conflicts(
            conflicts, "ours", source_commit, target_commit
        )
        assert "shared.txt" in resolved_files_ours
        assert resolved_files_ours["shared.txt"] == conflicts[0]["target_path"]

        # Test 'theirs' strategy
        resolved_files_theirs = dataset._resolve_conflicts(
            conflicts, "theirs", source_commit, target_commit
        )
        assert "shared.txt" in resolved_files_theirs
        assert resolved_files_theirs["shared.txt"] == conflicts[0]["source_path"]


def test_merge_complex_scenario():
    """Test a complex merge scenario with multiple files and conflicts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add multiple files to main branch
        main_file1 = Path(temp_dir) / "main1.txt"
        main_file1.write_text("Main file 1")
        main_file2 = Path(temp_dir) / "main2.txt"
        main_file2.write_text("Main file 2")
        shared_file = Path(temp_dir) / "shared.txt"
        shared_file.write_text("Main shared version")

        dataset.commit(
            "Initial commit",
            add_files=[str(main_file1), str(main_file2), str(shared_file)],
        )

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Add new file and modify shared file
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature file")
        shared_file.write_text("Feature shared version")

        dataset.commit(
            "Add feature and modify shared",
            add_files=[str(feature_file), str(shared_file)],
        )

        # Switch back to main
        dataset.switch_branch("main")

        # Merge feature into main
        result = dataset.merge("feature", "main")

        # Check merge result
        assert result["success"] is True
        assert result["source_branch"] == "feature"
        assert result["target_branch"] == "main"
        assert len(result["conflicts"]) == 1  # Only shared.txt should conflict
        assert result["conflicts"][0]["filename"] == "shared.txt"

        # Check that all files are in the merge commit
        dataset.checkout(result["merge_commit"])
        files = dataset.file_dict
        assert "main1.txt" in files
        assert "main2.txt" in files
        assert "feature.txt" in files
        assert "shared.txt" in files


def test_merge_default_target_branch():
    """Test merge with default target branch (current branch)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add initial commit
        main_file = Path(temp_dir) / "main.txt"
        main_file.write_text("Main branch content")
        dataset.commit("Initial commit", add_files=str(main_file))

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Add a file to feature branch
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature branch content")
        dataset.commit("Add feature file", add_files=str(feature_file))

        # Merge feature into current branch (feature)
        result = dataset.merge("main")

        # Check merge result
        assert result["success"] is True
        assert result["source_branch"] == "main"
        assert result["target_branch"] == "feature"  # Current branch
        assert len(result["conflicts"]) == 0
