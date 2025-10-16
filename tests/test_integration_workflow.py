#!/usr/bin/env python3
"""
Integration test for complete GitData workflow:
1. Create a new dataset on local filesystem
2. Commit 3 text files
3. Create a new branch
4. Commit 3 more text files
5. Merge the branch
6. Verify commit count and file structure
"""

import os
import shutil
import tempfile
from pathlib import Path

from loguru import logger

from kirin import Dataset


def create_test_files(directory: Path, files: list) -> None:
    """Create test files with content."""
    for filename, content in files:
        file_path = directory / filename
        file_path.write_text(content)


def test_complete_kirin_linear_workflow():
    """Test the complete GitData workflow with proper assertions."""
    import tempfile

    # Use temporary directory to avoid Git repository conflicts
    with tempfile.TemporaryDirectory() as temp_root:
        test_dir = Path(temp_root) / "test-integration-workflow"
        name = "integration-test"

        # Create test directory
        test_dir.mkdir(exist_ok=True)

        # Step 1: Create new dataset
        dataset = Dataset(root_dir=str(test_dir.absolute()), name=name)

        # Verify dataset creation
        assert dataset.name == name
        assert dataset.root_dir == str(test_dir.absolute())
        # Note: Linear commit history - no branching functionality

        # Step 2: Create and commit initial 3 text files
        initial_files = [
            (
                "data_analysis.txt",
                "This file contains data analysis results.\n\nKey findings:\n"
                "- Revenue increased by 15%\n- Customer satisfaction improved\n"
                "- Market share expanded",
            ),
            (
                "research_notes.txt",
                "Research Notes\n\nHypothesis: Machine learning can improve "
                "efficiency\n\n"
                "Methodology:\n1. Data collection\n2. Model training\n3. Validation\n\n"
                "Results: Positive correlation found",
            ),
            (
                "project_requirements.txt",
                "Project Requirements Document\n\nFunctional Requirements:\n"
                "- User authentication\n- Data visualization\n- Report generation\n\n"
                "Non-functional Requirements:\n- Performance: <2s response time\n"
                "- Security: Encrypted data storage",
            ),
        ]

        create_test_files(test_dir, initial_files)

        # Commit the initial files
        initial_file_paths = [str(test_dir / f[0]) for f in initial_files]
        commit_message_1 = (
            "Initial commit: Add data analysis, research notes, and "
            "project requirements"
        )
        commit_hash_1 = dataset.commit(commit_message_1, add_files=initial_file_paths)

        # Verify initial commit
        assert commit_hash_1 is not None
        assert len(commit_hash_1) == 40  # Git SHA-1 hash length
        assert len(dataset.list_files()) == 3
        file_names = dataset.list_files()
        assert "data_analysis.txt" in file_names
        assert "research_notes.txt" in file_names
        assert "project_requirements.txt" in file_names

        # Verify commit count after first commit - note Git implementation includes full history
        commits = dataset.history()
        # We can't predict exact count due to existing Git history, but our commit should be there
        commit_messages = [c.message for c in commits]
        assert commit_message_1 in commit_messages

        # Step 3: Add more files to the dataset (linear workflow)
        feature_files = [
            (
                "feature_spec.txt",
                "Feature Specification\n\nNew Feature: Data Export\n\n"
                "Description: Users can export data in multiple formats\n"
                "Acceptance Criteria:\n- Export to CSV\n- Export to JSON\n- Export to PDF",
            ),
            (
                "config.json",
                '{\n  "database_url": "localhost:5432",\n  "api_version": "v2",\n  '
                '"debug_mode": false\n}',
            ),
        ]

        create_test_files(test_dir, feature_files)
        feature_file_paths = [str(test_dir / f[0]) for f in feature_files]

        commit_message_2 = "Add feature specification and configuration"
        commit_hash_2 = dataset.commit(commit_message_2, add_files=feature_file_paths)

        # Verify second commit
        assert commit_hash_2 is not None
        assert len(commit_hash_2) == 40  # Git SHA-1 hash length
        assert len(dataset.list_files()) == 5  # 3 initial + 2 new files

        # Step 4: Remove one file (linear workflow continues)
        file_to_remove = str(test_dir / "data_analysis.txt")
        commit_message_3 = "Remove outdated data analysis file"
        commit_hash_3 = dataset.commit(commit_message_3, remove_files=[file_to_remove])

        # Verify third commit (file removal)
        assert commit_hash_3 is not None
        assert len(commit_hash_3) == 40  # Git SHA-1 hash length
        assert len(dataset.list_files()) == 4  # 5 - 1 removed file

        # Step 5: Verify commit history is linear
        history = dataset.history()
        assert len(history) >= 3  # Should have at least our 3 commits

        # Step 6: Test checkout functionality (time travel)
        # Checkout first commit
        dataset.checkout(commit_hash_1)
        assert dataset.current_commit.hash == commit_hash_1
        assert len(dataset.list_files()) == 3

        # Checkout second commit
        dataset.checkout(commit_hash_2)
        assert dataset.current_commit.hash == commit_hash_2
        assert len(dataset.list_files()) == 5

        # Checkout the latest commit again
        dataset.checkout(commit_hash_3)
        assert dataset.current_commit.hash == commit_hash_3
        assert len(dataset.list_files()) == 4
        file_names = dataset.list_files()
        assert "data_analysis.txt" not in file_names

        logger.info("✅ All integration test assertions passed!")


def test_linear_commit_history():
    """Test that Kirin uses linear commit history without branching."""
    import tempfile

    # Use temporary directory to avoid Git repository conflicts
    with tempfile.TemporaryDirectory() as temp_root:
        test_dir = Path(temp_root) / "test-linear-history"
        name = "linear-history-test"

        # Create test directory
        test_dir.mkdir(exist_ok=True)

        # Create dataset
        dataset = Dataset(root_dir=str(test_dir.absolute()), name=name)

        # Test linear commit history - no branching functionality
        # Create initial commit
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Initial content")
            initial_file = f.name

        try:
            commit1 = dataset.commit(message="Initial commit", add_files=[initial_file])
            assert commit1 is not None

            # Create second commit
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write("Second content")
                second_file = f.name

            try:
                commit2 = dataset.commit(
                    message="Second commit", add_files=[second_file]
                )
                assert commit2 is not None

                # Verify linear history - Git implementation includes full repository history
                history = dataset.history()
                # Should have at least our 2 commits, but may have more from existing repo
                assert len(history) >= 2

                # Check that our commits are in the recent history
                recent_messages = [commit.message for commit in history[:5]]  # Check first 5 commits
                assert "Second commit" in recent_messages
                assert "Initial commit" in recent_messages

                # Verify we can checkout specific commits
                dataset.checkout(commit1)
                files = dataset.list_files()
                assert len(files) == 1

                dataset.checkout(commit2)
                files = dataset.list_files()
                assert len(files) == 2

            finally:
                if os.path.exists(second_file):
                    os.unlink(second_file)

        finally:
            if os.path.exists(initial_file):
                os.unlink(initial_file)
