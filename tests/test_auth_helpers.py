"""Tests for authentication detection and setup instructions."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kirin.auth_helpers import (
    detect_aws_credentials,
    detect_azure_credentials,
    detect_gcp_credentials,
    get_auth_status,
    get_setup_instructions,
)


def test_detect_aws_credentials_from_env_vars():
    """Test AWS credential detection from environment variables."""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "AWS_DEFAULT_REGION": "us-west-2",
        },
    ):
        result = detect_aws_credentials()

        assert result["available"] is True
        assert result["source"] == "environment"
        assert result["region"] == "us-west-2"
        assert "profile" not in result


def test_detect_aws_credentials_from_profile():
    """Test AWS credential detection from AWS profile."""
    with patch.dict(os.environ, {"AWS_PROFILE": "my-profile"}):
        with patch("kirin.auth_helpers.Path") as mock_path:
            # Mock ~/.aws/credentials file exists
            mock_credentials_file = Mock()
            mock_credentials_file.exists.return_value = True
            mock_path.return_value = mock_credentials_file

            result = detect_aws_credentials()

            assert result["available"] is True
            assert result["source"] == "profile"
            assert result["profile"] == "my-profile"


def test_detect_aws_credentials_not_found():
    """Test AWS credential detection when no credentials found."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("kirin.auth_helpers.Path.home") as mock_home:
            # Mock the home directory and credentials file
            mock_aws_dir = Mock()
            mock_credentials_file = Mock()
            mock_credentials_file.exists.return_value = False

            # Set up the mock chain: Path.home() / ".aws" / "credentials"
            mock_home.return_value = Mock()
            mock_home.return_value.__truediv__ = Mock(return_value=mock_aws_dir)
            mock_aws_dir.__truediv__ = Mock(return_value=mock_credentials_file)

            result = detect_aws_credentials()

            assert result["available"] is False
            assert result["source"] is None


def test_detect_gcp_credentials_from_env():
    """Test GCP credential detection from environment variable."""
    with patch.dict(
        os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json"}
    ):
        with patch("kirin.auth_helpers.Path") as mock_path_class:
            # Mock the Path constructor to return a mock that exists
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path_class.return_value = mock_path

            result = detect_gcp_credentials()

            assert result["available"] is True
            assert result["source"] == "environment"
            assert result["credentials_file"] == "/path/to/service-account.json"


def test_detect_gcp_credentials_from_adc():
    """Test GCP credential detection from Application Default Credentials."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("kirin.auth_helpers.Path") as mock_path:
            # Mock ADC file exists
            mock_adc_file = Mock()
            mock_adc_file.exists.return_value = True
            mock_path.return_value = mock_adc_file

            result = detect_gcp_credentials()

            assert result["available"] is True
            assert result["source"] == "adc"


def test_detect_gcp_credentials_not_found():
    """Test GCP credential detection when no credentials found."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("kirin.auth_helpers.Path") as mock_path_class:
            # Create a mock path that doesn't exist and supports the / operator
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_path.__truediv__ = Mock(return_value=mock_path)  # Support / operator
            mock_path_class.return_value = mock_path
            mock_path_class.home.return_value = mock_path

            result = detect_gcp_credentials()

            assert result["available"] is False
            assert result["source"] is None


def test_detect_azure_credentials_from_env():
    """Test Azure credential detection from environment variable."""
    with patch.dict(
        os.environ,
        {
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test"
        },
    ):
        result = detect_azure_credentials()

        assert result["available"] is True
        assert result["source"] == "environment"


def test_detect_azure_credentials_from_cli():
    """Test Azure credential detection from az CLI."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("kirin.auth_helpers.subprocess.run") as mock_run:
            # Mock az account show returns success
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"name": "test-account"}'

            result = detect_azure_credentials()

            assert result["available"] is True
            assert result["source"] == "az_cli"


def test_detect_azure_credentials_not_found():
    """Test Azure credential detection when no credentials found."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("kirin.auth_helpers.subprocess.run") as mock_run:
            # Mock az account show returns failure
            mock_run.return_value.returncode = 1

            result = detect_azure_credentials()

            assert result["available"] is False
            assert result["source"] is None


def test_get_auth_status_aws():
    """Test getting auth status for AWS backend."""
    with patch("kirin.auth_helpers.detect_aws_credentials") as mock_detect:
        mock_detect.return_value = {
            "available": True,
            "source": "environment",
            "region": "us-west-2",
        }

        result = get_auth_status("s3")

        assert result["backend_type"] == "s3"
        assert result["available"] is True
        assert result["source"] == "environment"
        assert result["region"] == "us-west-2"


def test_get_auth_status_gcp():
    """Test getting auth status for GCP backend."""
    with patch("kirin.auth_helpers.detect_gcp_credentials") as mock_detect:
        mock_detect.return_value = {"available": True, "source": "adc"}

        result = get_auth_status("gcs")

        assert result["backend_type"] == "gcs"
        assert result["available"] is True
        assert result["source"] == "adc"


def test_get_auth_status_azure():
    """Test getting auth status for Azure backend."""
    with patch("kirin.auth_helpers.detect_azure_credentials") as mock_detect:
        mock_detect.return_value = {"available": True, "source": "az_cli"}

        result = get_auth_status("azure")

        assert result["backend_type"] == "azure"
        assert result["available"] is True
        assert result["source"] == "az_cli"


def test_get_auth_status_unknown_backend():
    """Test getting auth status for unknown backend type."""
    result = get_auth_status("unknown")

    assert result["backend_type"] == "unknown"
    assert result["available"] is False
    assert result["source"] is None


def test_get_setup_instructions_aws():
    """Test getting setup instructions for AWS."""
    instructions = get_setup_instructions("s3")

    assert "aws configure" in instructions
    assert "aws sso login" in instructions
    assert "AWS_ACCESS_KEY_ID" in instructions


def test_get_setup_instructions_gcp():
    """Test getting setup instructions for GCP."""
    instructions = get_setup_instructions("gcs")

    assert "gcloud auth application-default login" in instructions
    assert "GOOGLE_APPLICATION_CREDENTIALS" in instructions


def test_get_setup_instructions_azure():
    """Test getting setup instructions for Azure."""
    instructions = get_setup_instructions("azure")

    assert "az login" in instructions
    assert "AZURE_STORAGE_CONNECTION_STRING" in instructions


def test_get_setup_instructions_unknown():
    """Test getting setup instructions for unknown backend."""
    instructions = get_setup_instructions("unknown")

    assert "Unknown backend type" in instructions


def test_aws_credentials_with_region():
    """Test AWS credentials detection includes region information."""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    ):
        result = detect_aws_credentials()

        assert result["available"] is True
        assert result["region"] == "us-east-1"


def test_gcp_credentials_with_project():
    """Test GCP credentials detection includes project information."""
    with patch.dict(
        os.environ,
        {
            "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json",
            "GOOGLE_CLOUD_PROJECT": "my-project",
        },
    ):
        result = detect_gcp_credentials()

        assert result["available"] is True
        assert result["project"] == "my-project"
