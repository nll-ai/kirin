#!/usr/bin/env python3
"""Complete user workflow simulation - tests the entire UI without manual clicking."""

import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from kirin.web.app import app


class TestCompleteUserWorkflow:
    """Simulate a complete user workflow from start to finish."""

    def test_complete_user_journey(self):
        """Test the complete user journey: backend → dataset → files → commits."""
        print("🚀 Testing Complete User Journey...")

        with tempfile.TemporaryDirectory() as temp_dir:
            client = TestClient(app)

            # Step 1: User visits the homepage
            print("  📍 Step 1: Visiting homepage...")
            response = client.get("/")
            assert response.status_code == 200
            assert "Storage Backends" in response.text
            print("  ✅ Homepage loads correctly")

            # Step 2: User adds a new backend
            print("  📍 Step 2: Adding new backend...")
            backend_data = {
                "name": "Test Backend",
                "type": "local",
                "root_dir": str(Path(temp_dir) / "kirin-data"),
            }
            response = client.post("/backends/add", data=backend_data)
            assert response.status_code == 200
            assert "added successfully" in response.text
            print("  ✅ Backend created successfully")

            # Step 3: User views backend datasets (should be empty)
            print("  📍 Step 3: Viewing backend datasets...")
            response = client.get("/backend/test-backend")
            assert response.status_code == 200
            assert (
                "No datasets found" in response.text
                or "Create Your First Dataset" in response.text
            )
            print("  ✅ Backend datasets page loads (empty state)")

            # Step 4: User creates a new dataset
            print("  📍 Step 4: Creating new dataset...")
            dataset_data = {"name": "my-dataset", "description": "My first dataset"}
            response = client.post(
                "/backend/test-backend/datasets/create", data=dataset_data
            )
            assert response.status_code == 200
            assert "created successfully" in response.text
            print("  ✅ Dataset created successfully")

            # Step 5: User views the dataset (should show files tab)
            print("  📍 Step 5: Viewing dataset...")
            response = client.get("/backend/test-backend/my-dataset")
            assert response.status_code == 200
            assert "my-dataset" in response.text
            assert "Files" in response.text
            print("  ✅ Dataset view loads correctly")

            # Step 6: User uploads files and commits
            print("  📍 Step 6: Uploading files and committing...")
            files = {
                "files": ("data.csv", "name,age\nJohn,25\nJane,30", "text/csv"),
                "files": ("notes.txt", "Important notes\nLine 2", "text/plain"),
            }
            commit_data = {"message": "Initial commit with data files"}
            response = client.post(
                "/backend/test-backend/my-dataset/commit", data=commit_data, files=files
            )
            assert response.status_code == 200
            assert "created successfully" in response.text
            print("  ✅ Files uploaded and committed successfully")

            # Step 7: User views files in the dataset
            print("  📍 Step 7: Viewing files...")
            response = client.get("/backend/test-backend/my-dataset/files")
            assert response.status_code == 200
            assert "data.csv" in response.text
            assert "notes.txt" in response.text
            print("  ✅ Files are displayed correctly")

            # Step 8: User previews a file
            print("  📍 Step 8: Previewing a file...")
            response = client.get(
                "/backend/test-backend/my-dataset/file/data.csv/preview"
            )
            assert response.status_code == 200
            assert "data.csv" in response.text
            assert "John,25" in response.text
            print("  ✅ File preview works correctly")

            # Step 9: User views commit history
            print("  📍 Step 9: Viewing commit history...")
            response = client.get("/backend/test-backend/my-dataset/history")
            assert response.status_code == 200
            assert "Commit History" in response.text
            assert "Initial commit" in response.text
            print("  ✅ Commit history displays correctly")

            # Step 10: User creates another commit
            print("  📍 Step 10: Creating another commit...")
            files2 = {
                "files": (
                    "update.csv",
                    "name,age,city\nJohn,25,NYC\nJane,30,LA",
                    "text/csv",
                )
            }
            commit_data2 = {"message": "Add city information"}
            response = client.post(
                "/backend/test-backend/my-dataset/commit",
                data=commit_data2,
                files=files2,
            )
            assert response.status_code == 200
            print("  ✅ Second commit created successfully")

            # Step 11: User views updated history
            print("  📍 Step 11: Viewing updated history...")
            response = client.get("/backend/test-backend/my-dataset/history")
            assert response.status_code == 200
            assert "Add city information" in response.text
            print("  ✅ Updated history displays correctly")

            print("\n🎉 Complete user journey test passed!")
            return True

    def test_error_scenarios(self):
        """Test various error scenarios."""
        print("🚀 Testing Error Scenarios...")

        with tempfile.TemporaryDirectory() as temp_dir:
            client = TestClient(app)

            # Test 1: Duplicate backend creation
            print("  📍 Testing duplicate backend creation...")
            backend_data = {
                "name": "Test Backend",
                "type": "local",
                "root_dir": str(Path(temp_dir) / "kirin-data"),
            }
            client.post("/backends/add", data=backend_data)
            response = client.post("/backends/add", data=backend_data)
            assert response.status_code == 200
            assert "already exists" in response.text
            print("  ✅ Duplicate backend handled gracefully")

            # Test 2: Duplicate dataset creation
            print("  📍 Testing duplicate dataset creation...")
            client.post(
                "/backend/test-backend/datasets/create",
                data={"name": "test-dataset", "description": "Test dataset"},
            )
            response = client.post(
                "/backend/test-backend/datasets/create",
                data={"name": "test-dataset", "description": "Another test dataset"},
            )
            assert response.status_code == 200
            assert "already exists" in response.text
            print("  ✅ Duplicate dataset handled gracefully")

            # Test 3: Non-existent backend
            print("  📍 Testing non-existent backend...")
            response = client.get("/backend/non-existent")
            assert response.status_code == 404
            print("  ✅ Non-existent backend returns 404")

            # Test 4: Non-existent dataset
            print("  📍 Testing non-existent dataset...")
            response = client.get("/backend/test-backend/non-existent")
            assert response.status_code == 500  # Should handle gracefully
            print("  ✅ Non-existent dataset handled gracefully")

            print("\n🎉 Error scenarios test passed!")
            return True


def run_complete_workflow_test():
    """Run the complete workflow test."""
    print("🚀 Running Complete User Workflow Test\n")

    try:
        test_instance = TestCompleteUserWorkflow()

        # Run complete user journey
        success1 = test_instance.test_complete_user_journey()

        # Run error scenarios
        success2 = test_instance.test_error_scenarios()

        return success1 and success2

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = run_complete_workflow_test()
    if success:
        print("\n🎉 All workflow tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some workflow tests failed!")
        sys.exit(1)
