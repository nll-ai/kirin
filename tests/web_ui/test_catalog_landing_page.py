"""Test catalog landing page functionality.

Tests that the catalog landing page correctly displays dataset information
including commit counts, descriptions, and other metadata.
"""

import os
import tempfile

from fastapi.testclient import TestClient

from kirin.web.app import app
from kirin.web.config import CatalogConfig, CatalogManager


def test_catalog_displays_dataset_commit_counts():
    """Test that catalog landing page shows correct commit counts for datasets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create temporary files for commits
        file1_path = os.path.join(temp_dir, "file1.txt")
        file2_path = os.path.join(temp_dir, "file2.txt")

        with open(file1_path, "w") as f:
            f.write("content1")
        with open(file2_path, "w") as f:
            f.write("content2")

        # Create a test catalog with datasets that have commits
        catalog_manager = CatalogManager()

        # Create catalog config
        catalog_config = CatalogConfig(
            id="test-catalog-1",
            name="Test Catalog 1",
            root_dir=temp_dir,
            aws_profile=None,
        )
        catalog_manager.add_catalog(catalog_config)

        # Create catalog and datasets with commits
        from kirin import Catalog

        catalog = Catalog(root_dir=temp_dir)

        # Create first dataset with commits
        dataset1 = catalog.create_dataset("dataset1", "First dataset")
        dataset1.commit(message="Initial commit", add_files=[file1_path])

        # Create second dataset with multiple commits
        dataset2 = catalog.create_dataset("dataset2", "Second dataset")
        dataset2.commit(message="First commit", add_files=[file1_path])
        dataset2.commit(message="Second commit", add_files=[file2_path])

        # Test the catalog landing page endpoint
        client = TestClient(app)

        # Override the catalog manager dependency
        app.dependency_overrides[app.dependency_overrides.get] = lambda: catalog_manager

        response = client.get("/catalog/test-catalog-1")

        # Verify response is successful
        assert response.status_code == 200

        # Parse the HTML response to check commit counts
        content = response.text

        # Verify dataset1 shows 1 commit
        assert "dataset1" in content
        assert "1 commit" in content or "1 commits" in content

        # Verify dataset2 shows 2 commits
        assert "dataset2" in content
        assert "2 commit" in content or "2 commits" in content


def test_catalog_displays_empty_catalog():
    """Test that empty catalogs (no datasets) show empty state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test catalog with no datasets
        catalog_manager = CatalogManager()

        catalog_config = CatalogConfig(
            id="test-catalog-2",
            name="Test Catalog 2",
            root_dir=temp_dir,
            aws_profile=None,
        )
        catalog_manager.add_catalog(catalog_config)

        # Test the catalog landing page endpoint
        client = TestClient(app)
        app.dependency_overrides[app.dependency_overrides.get] = lambda: catalog_manager

        response = client.get("/catalog/test-catalog-2")

        # Verify response is successful
        assert response.status_code == 200

        content = response.text

        # Verify empty catalog shows empty state
        assert "No datasets yet" in content
        assert "This catalog doesn't have any datasets yet" in content


def test_catalog_displays_datasets_with_commits():
    """Test catalog with datasets that have commits."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_manager = CatalogManager()

        catalog_config = CatalogConfig(
            id="test-catalog-3",
            name="Test Catalog 3",
            root_dir=temp_dir,
            aws_profile=None,
        )
        catalog_manager.add_catalog(catalog_config)

        from kirin import Catalog

        catalog = Catalog(root_dir=temp_dir)

        # Create temporary files for commits
        file1_path = os.path.join(temp_dir, "file1.txt")
        file2_path = os.path.join(temp_dir, "file2.txt")

        with open(file1_path, "w") as f:
            f.write("content1")
        with open(file2_path, "w") as f:
            f.write("content2")

        # Create dataset with commits
        dataset_with_commits = catalog.create_dataset("with-commits", "Has commits")
        dataset_with_commits.commit(message="First commit", add_files=[file1_path])
        dataset_with_commits.commit(message="Second commit", add_files=[file2_path])

        # Test the catalog landing page
        client = TestClient(app)
        app.dependency_overrides[app.dependency_overrides.get] = lambda: catalog_manager

        response = client.get("/catalog/test-catalog-3")
        assert response.status_code == 200

        content = response.text

        # Verify dataset with commits is listed
        assert "with-commits" in content

        # Verify correct commit count
        assert "2 commit" in content or "2 commits" in content


def test_catalog_performance_with_multiple_datasets():
    """Test that catalog landing page loads efficiently with multiple datasets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_manager = CatalogManager()

        catalog_config = CatalogConfig(
            id="test-catalog-4",
            name="Test Catalog 4",
            root_dir=temp_dir,
            aws_profile=None,
        )
        catalog_manager.add_catalog(catalog_config)

        from kirin import Catalog

        catalog = Catalog(root_dir=temp_dir)

        # Create temporary files for commits
        file_paths = []
        for i in range(10):
            file_path = os.path.join(temp_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"content{i}")
            file_paths.append(file_path)

        # Create multiple datasets to test performance
        for i in range(10):
            dataset = catalog.create_dataset(f"dataset-{i}", f"Dataset {i}")
            # Add some commits to each dataset
            for j in range(3):
                dataset.commit(
                    message=f"Commit {j} for dataset {i}", add_files=[file_paths[i]]
                )

        # Test the catalog landing page
        client = TestClient(app)
        app.dependency_overrides[app.dependency_overrides.get] = lambda: catalog_manager

        import time

        start_time = time.time()

        response = client.get("/catalog/test-catalog-4")

        end_time = time.time()
        response_time = end_time - start_time

        # Verify response is successful
        assert response.status_code == 200

        # Verify reasonable performance (should complete in under 5 seconds)
        assert response_time < 5.0, f"Response took {response_time:.2f}s, expected < 5s"

        # Verify all datasets show correct commit counts
        content = response.text
        for i in range(10):
            assert f"dataset-{i}" in content
            assert "3 commit" in content or "3 commits" in content
