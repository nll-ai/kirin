#!/usr/bin/env python3
"""
Integration test for complete Kirin workflow:
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
    """Test the complete Kirin workflow with proper assertions."""

    # Setup test environment
    test_dir = Path("test-integration-workflow")
    name = "integration-test"

    try:
        # Clean up any existing test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)

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
        assert len(commit_hash_1) == 64  # SHA-256 hash length
        assert len(dataset.list_files()) == 3
        file_names = dataset.list_files()
        assert "data_analysis.txt" in file_names
        assert "research_notes.txt" in file_names
        assert "project_requirements.txt" in file_names

        # Verify commit count after first commit
        commits = dataset.get_commits()
        assert len(commits) == 1  # Our commit (no initial commit in linear workflow)

        # Step 3: Add more files to the dataset (linear workflow)
        feature_files = [
            (
                "experimental_results.txt",
                "Experimental Results\n\nTest Configuration:\n- Sample size: 1000\n"
                "- Duration: 30 days\n- Control group: 500\n- Treatment group: 500\n\n"
                "Key Metrics:\n- Conversion rate: +12%\n- User engagement: +8%\n"
                "- Revenue impact: +$50K",
            ),
            (
                "algorithm_optimization.txt",
                "Algorithm Optimization Report\n\nOriginal Algorithm:\n"
                "- Processing time: 2.5s\n- Memory usage: 512MB\n- Accuracy: 94.2%\n\n"
                "Optimized Algorithm:\n- Processing time: 1.8s (-28%)\n"
                "- Memory usage: 384MB (-25%)\n- Accuracy: 95.1% (+0.9%)",
            ),
            (
                "user_feedback.txt",
                "User Feedback Analysis\n\nSurvey Results (n=500):\n\n"
                "Satisfaction Scores:\n- Overall: 4.2/5.0\n- Ease of use: 4.5/5.0\n"
                "- Performance: 4.1/5.0\n- Support: 4.3/5.0\n\nCommon Requests:\n"
                "- Faster loading times\n- Better mobile experience\n"
                "- More customization options",
            ),
        ]

        create_test_files(test_dir, feature_files)

        # Commit the feature files
        feature_file_paths = [str(test_dir / f[0]) for f in feature_files]
        commit_message_2 = (
            "Add experimental analysis, algorithm optimization, and user feedback"
        )
        commit_hash_2 = dataset.commit(commit_message_2, add_files=feature_file_paths)

        # Verify feature commit
        assert commit_hash_2 is not None
        assert len(commit_hash_2) == 64
        assert len(dataset.list_files()) == 6  # 3 initial + 3 feature files
        file_names = dataset.list_files()
        assert "experimental_results.txt" in file_names
        assert "algorithm_optimization.txt" in file_names
        assert "user_feedback.txt" in file_names

        # Verify commit count after second commit
        commits = dataset.get_commits()
        assert len(commits) == 2

        # Step 5: Remove a file and commit
        file_to_remove = "data_analysis.txt"
        commit_message_3 = f"Remove {file_to_remove}"
        commit_hash_3 = dataset.commit(commit_message_3, remove_files=[file_to_remove])

        # Verify third commit
        assert commit_hash_3 is not None
        assert len(commit_hash_3) == 64
        assert len(dataset.list_files()) == 5
        file_names = dataset.list_files()
        assert file_to_remove not in file_names

        # Verify commit count after third commit
        commits = dataset.get_commits()
        assert len(commits) == 3

        # Step 6: Checkout a previous commit
        dataset.checkout(commit_hash_1)
        assert dataset.current_commit.hash == commit_hash_1
        assert len(dataset.list_files()) == 3
        file_names = dataset.list_files()
        assert "data_analysis.txt" in file_names
        assert "experimental_results.txt" not in file_names

        # Checkout the latest commit again
        dataset.checkout(commit_hash_3)
        assert dataset.current_commit.hash == commit_hash_3
        assert len(dataset.list_files()) == 5
        file_names = dataset.list_files()
        assert "data_analysis.txt" not in file_names

        logger.info("✅ All integration test assertions passed!")

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_linear_commit_history():
    """Test that Kirin uses linear commit history without branching."""

    test_dir = Path("test-linear-history")
    name = "linear-history-test"

    try:
        # Clean up any existing test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)

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

                # Verify linear history
                history = dataset.history()
                assert len(history) == 2
                assert history[0].message == "Second commit"
                assert history[1].message == "Initial commit"

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

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
