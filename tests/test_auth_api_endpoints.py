"""Tests for authentication API endpoints."""

import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from kirin.web.app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_get_auth_status_s3(client):
    """Test getting auth status for S3 backend."""
    with patch("kirin.auth_helpers.get_auth_status") as mock_get_auth:
        mock_get_auth.return_value = {
            "backend_type": "s3",
            "available": True,
            "source": "environment",
            "region": "us-west-2",
        }

        response = client.get("/api/auth-status/s3")

        assert response.status_code == 200
        data = response.json()
        assert data["backend_type"] == "s3"
        assert data["available"] is True
        assert data["source"] == "environment"
        assert data["region"] == "us-west-2"


def test_get_auth_status_gcs(client):
    """Test getting auth status for GCS backend."""
    with patch("kirin.web.app.get_auth_status") as mock_get_auth:
        mock_get_auth.return_value = {
            "backend_type": "gcs",
            "available": True,
            "source": "adc",
        }

        response = client.get("/api/auth-status/gcs")

        assert response.status_code == 200
        data = response.json()
        assert data["backend_type"] == "gcs"
        assert data["available"] is True
        assert data["source"] == "adc"


def test_get_auth_status_azure(client):
    """Test getting auth status for Azure backend."""
    with patch("kirin.auth_helpers.get_auth_status") as mock_get_auth:
        mock_get_auth.return_value = {
            "backend_type": "azure",
            "available": True,
            "source": "az_cli",
        }

        response = client.get("/api/auth-status/azure")

        assert response.status_code == 200
        data = response.json()
        assert data["backend_type"] == "azure"
        assert data["available"] is True
        assert data["source"] == "az_cli"


def test_get_auth_status_not_available(client):
    """Test getting auth status when credentials not available."""
    with patch("kirin.web.app.get_auth_status") as mock_get_auth:
        mock_get_auth.return_value = {
            "backend_type": "s3",
            "available": False,
            "source": None,
        }

        response = client.get("/api/auth-status/s3")

        assert response.status_code == 200
        data = response.json()
        assert data["backend_type"] == "s3"
        assert data["available"] is False
        assert data["source"] is None


def test_get_auth_status_error(client):
    """Test getting auth status when error occurs."""
    with patch("kirin.auth_helpers.get_auth_status") as mock_get_auth:
        mock_get_auth.side_effect = Exception("Auth detection failed")

        response = client.get("/api/auth-status/s3")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to get auth status" in data["detail"]


def test_get_setup_instructions_s3(client):
    """Test getting setup instructions for S3 backend."""
    with patch("kirin.web.app.get_setup_instructions") as mock_get_instructions:
        mock_instructions = """AWS Authentication Setup:

Option 1: AWS CLI Configuration (Recommended)
  aws configure

Option 2: AWS SSO
  aws configure sso
  aws sso login

After setup, refresh this page and test the connection."""

        mock_get_instructions.return_value = {"instructions": mock_instructions}

        response = client.get("/api/setup-instructions/s3")

        assert response.status_code == 200
        data = response.json()
        assert "instructions" in data
        assert "aws configure" in data["instructions"]
        assert "aws sso login" in data["instructions"]


def test_get_setup_instructions_gcs(client):
    """Test getting setup instructions for GCS backend."""
    with patch("kirin.web.app.get_setup_instructions") as mock_get_instructions:
        mock_instructions = """Google Cloud Authentication Setup:

Option 1: Application Default Credentials (Recommended)
  gcloud auth application-default login

Option 2: Service Account Key File
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

After setup, refresh this page and test the connection."""

        mock_get_instructions.return_value = {"instructions": mock_instructions}

        response = client.get("/api/setup-instructions/gcs")

        assert response.status_code == 200
        data = response.json()
        assert "instructions" in data
        assert "gcloud auth application-default login" in data["instructions"]
        assert "GOOGLE_APPLICATION_CREDENTIALS" in data["instructions"]


def test_get_setup_instructions_azure(client):
    """Test getting setup instructions for Azure backend."""
    with patch("kirin.web.app.get_setup_instructions") as mock_get_instructions:
        mock_instructions = """Azure Authentication Setup:

Option 1: Azure CLI (Recommended)
  az login

Option 2: Connection String
  export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=your-account;AccountKey=your-key"

After setup, refresh this page and test the connection."""

        mock_get_instructions.return_value = {"instructions": mock_instructions}

        response = client.get("/api/setup-instructions/azure")

        assert response.status_code == 200
        data = response.json()
        assert "instructions" in data
        assert "az login" in data["instructions"]
        assert "AZURE_STORAGE_CONNECTION_STRING" in data["instructions"]


def test_get_setup_instructions_unknown_backend(client):
    """Test getting setup instructions for unknown backend."""
    with patch("kirin.web.app.get_setup_instructions") as mock_get_instructions:
        mock_instructions = (
            "Unknown backend type: unknown. Please check the backend configuration."
        )

        mock_get_instructions.return_value = {"instructions": mock_instructions}

        response = client.get("/api/setup-instructions/unknown")

        assert response.status_code == 200
        data = response.json()
        assert "instructions" in data
        assert "Unknown backend type" in data["instructions"]


def test_get_setup_instructions_error(client):
    """Test getting setup instructions when error occurs."""
    with patch("kirin.auth_helpers.get_setup_instructions") as mock_get_instructions:
        mock_get_instructions.side_effect = Exception("Setup instructions failed")

        response = client.get("/api/setup-instructions/s3")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to get setup instructions" in data["detail"]


def test_auth_status_endpoint_imports():
    """Test that auth status endpoint imports work correctly."""
    # This test ensures the import in the endpoint works
    from kirin.auth_helpers import get_auth_status

    # Test that the function exists and is callable
    assert callable(get_auth_status)

    # Test with a known backend type
    result = get_auth_status("s3")
    assert isinstance(result, dict)
    assert "backend_type" in result
    assert "available" in result


def test_setup_instructions_endpoint_imports():
    """Test that setup instructions endpoint imports work correctly."""
    # This test ensures the import in the endpoint works
    from kirin.auth_helpers import get_setup_instructions

    # Test that the function exists and is callable
    assert callable(get_setup_instructions)

    # Test with a known backend type
    result = get_setup_instructions("s3")
    assert isinstance(result, str)
    assert len(result) > 0


def test_auth_status_endpoint_with_real_backend_types(client):
    """Test auth status endpoint with various backend types."""
    backend_types = ["s3", "gcs", "azure", "s3_compatible", "local"]

    for backend_type in backend_types:
        response = client.get(f"/api/auth-status/{backend_type}")

        # Should return 200 for all backend types
        assert response.status_code == 200

        data = response.json()
        assert "backend_type" in data
        assert "available" in data
        assert data["backend_type"] == backend_type


def test_setup_instructions_endpoint_with_real_backend_types(client):
    """Test setup instructions endpoint with various backend types."""
    backend_types = ["s3", "gcs", "azure", "s3_compatible", "local", "unknown"]

    for backend_type in backend_types:
        response = client.get(f"/api/setup-instructions/{backend_type}")

        # Should return 200 for all backend types
        assert response.status_code == 200

        data = response.json()
        assert "instructions" in data
        assert isinstance(data["instructions"], str)
        assert len(data["instructions"]) > 0
