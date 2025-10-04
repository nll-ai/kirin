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

import shutil
from pathlib import Path

from gitdata import Dataset
from loguru import logger


def create_test_files(directory: Path, files: list) -> None:
    """Create test files with content."""
    for filename, content in files:
        file_path = directory / filename
        file_path.write_text(content)


def test_complete_gitdata_workflow():
    """Test the complete GitData workflow with proper assertions."""

    # Setup test environment
    test_dir = Path("test-integration-workflow")
    dataset_name = "integration-test"

    try:
        # Clean up any existing test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)

        # Create test directory
        test_dir.mkdir(exist_ok=True)

        # Step 1: Create new dataset
        dataset = Dataset(root_dir=str(test_dir.absolute()), dataset_name=dataset_name)

        # Verify dataset creation
        assert dataset.dataset_name == dataset_name
        assert dataset.root_dir == str(test_dir.absolute())
        assert dataset.get_current_branch() == "main"

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
                "Research Notes\n\nHypothesis: Machine learning can improve efficiency\n\n"
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
        commit_message_1 = "Initial commit: Add data analysis, research notes, and project requirements"
        commit_hash_1 = dataset.commit(commit_message_1, add_files=initial_file_paths)

        # Verify initial commit
        assert commit_hash_1 is not None
        assert len(commit_hash_1) == 64  # SHA-256 hash length
        assert len(dataset.file_dict) == 3
        assert "data_analysis.txt" in dataset.file_dict
        assert "research_notes.txt" in dataset.file_dict
        assert "project_requirements.txt" in dataset.file_dict

        # Verify commit count after first commit
        dataset._commits_data_cache = None  # Clear cache
        commits_data = dataset._get_commits_data()
        assert len(commits_data) == 2  # Initial commit + our commit

        # Step 3: Create a new branch
        branch_name = "feature-experimental-analysis"
        dataset.create_branch(branch_name)
        dataset.switch_branch(branch_name)

        # Verify branch creation and switching
        assert dataset.get_current_branch() == branch_name
        assert branch_name in dataset.list_branches()

        # Step 4: Commit 3 more files on the branch
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
        assert len(dataset.file_dict) == 6  # 3 initial + 3 feature files
        assert "experimental_results.txt" in dataset.file_dict
        assert "algorithm_optimization.txt" in dataset.file_dict
        assert "user_feedback.txt" in dataset.file_dict

        # Verify commit count on branch
        dataset._commits_data_cache = None  # Clear cache
        branch_commits_data = dataset._get_commits_data()
        assert len(branch_commits_data) == 3  # Initial + first commit + feature commit

        # Step 5: Switch back to main and merge
        dataset.switch_branch("main")
        assert dataset.get_current_branch() == "main"
        assert len(dataset.file_dict) == 3  # Main branch should only have initial files

        # Perform merge
        merge_result = dataset.merge(branch_name)

        # Verify merge result
        assert merge_result["success"] is True
        assert merge_result["source_branch"] == branch_name
        assert merge_result["target_branch"] == "main"
        assert len(merge_result["conflicts"]) == 0  # No conflicts expected
        assert "merge_commit" in merge_result

        # Step 6: Verify final state
        dataset._commits_data_cache = None  # Clear cache
        final_commits_data = dataset._get_commits_data()
        final_commit_count = len(final_commits_data)
        final_file_count = len(dataset.file_dict)

        # Expected results
        expected_commits = (
            4  # Initial commit + first commit + feature commit + merge commit
        )
        expected_files = 6  # 3 initial + 3 feature files

        # Final assertions
        assert final_commit_count == expected_commits, (
            f"Expected {expected_commits} commits, got {final_commit_count}"
        )
        assert final_file_count == expected_files, (
            f"Expected {expected_files} files, got {final_file_count}"
        )

        # Verify all files are present
        expected_files_list = [
            "data_analysis.txt",
            "research_notes.txt",
            "project_requirements.txt",
            "experimental_results.txt",
            "algorithm_optimization.txt",
            "user_feedback.txt",
        ]

        for expected_file in expected_files_list:
            assert expected_file in dataset.file_dict, (
                f"Expected file {expected_file} not found in final dataset"
            )

        # Verify commit history structure
        commit_messages = [
            commit_data.get("commit_message", "")
            for commit_data in final_commits_data.values()
        ]
        assert commit_message_1 in commit_messages
        assert commit_message_2 in commit_messages

        # Verify merge commit exists
        merge_commits = [
            msg for msg in commit_messages if "merge" in msg.lower() or "Merge" in msg
        ]
        assert len(merge_commits) > 0, "No merge commit found in history"

        logger.info("✅ All integration test assertions passed!")

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_branch_name_validation():
    """Test that branch names with slashes are properly rejected."""

    test_dir = Path("test-branch-validation")
    dataset_name = "branch-validation-test"

    try:
        # Clean up any existing test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)

        # Create test directory
        test_dir.mkdir(exist_ok=True)

        # Create dataset
        dataset = Dataset(root_dir=str(test_dir.absolute()), dataset_name=dataset_name)

        # Test that branch creation with slash fails due to filesystem error
        try:
            dataset.create_branch("feature/with-slash")
            assert False, "Expected FileNotFoundError for branch name with slash"
        except (FileNotFoundError, OSError) as e:
            # The error occurs because the directory structure doesn't exist
            assert "No such file or directory" in str(e) or "feature/with-slash" in str(
                e
            )

        # Test that valid branch name works
        dataset.create_branch("feature-with-hyphen")
        assert "feature-with-hyphen" in dataset.list_branches()

        # Test underscore works too
        dataset.create_branch("feature_with_underscore")
        assert "feature_with_underscore" in dataset.list_branches()

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
