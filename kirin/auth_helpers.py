"""Authentication detection and setup instructions for cloud providers."""

import os
import subprocess
from pathlib import Path
from typing import Dict

from loguru import logger


def detect_aws_credentials() -> Dict[str, any]:
    """Detect AWS credentials from system using boto3.

    Returns:
        dict with 'available', 'source', 'profile', 'region', 'account_id', 'user_arn'
    """
    result = {
        "available": False,
        "source": None,
        "region": None,
        "profile": None,
        "account_id": None,
        "user_arn": None,
    }

    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ProfileNotFound
    except ImportError:
        logger.debug("boto3 not available for credential detection")
        return result

    # Try to get credentials using boto3's credential chain
    try:
        # Use the same profile logic as get_filesystem
        profile_name = os.getenv("AWS_PROFILE", "default")
        session = boto3.Session(profile_name=profile_name)
        credentials = session.get_credentials()

        if not credentials:
            logger.debug("No AWS credentials found via boto3")
            return result

        # Get additional info about the credentials
        sts_client = session.client("sts")
        try:
            identity = sts_client.get_caller_identity()
            result["account_id"] = identity.get("Account")
            result["user_arn"] = identity.get("Arn")
        except Exception as e:
            logger.debug(f"Could not get caller identity: {e}")

        result["available"] = True
        result["source"] = "boto3"
        result["profile"] = profile_name
        result["region"] = session.region_name or os.getenv(
            "AWS_DEFAULT_REGION", "us-east-1"
        )

        # Try to determine the credential source
        if hasattr(credentials, "method"):
            if "sso" in credentials.method.lower():
                result["source"] = "sso"
            elif "profile" in credentials.method.lower():
                result["source"] = "profile"
            elif "env" in credentials.method.lower():
                result["source"] = "environment"

        logger.debug(
            f"AWS credentials detected via boto3: {result['source']} profile={profile_name}"
        )
        return result

    except ProfileNotFound as e:
        logger.debug(f"AWS profile '{profile_name}' not found: {e}")
        return result
    except NoCredentialsError as e:
        logger.debug(f"No AWS credentials found: {e}")
        return result
    except Exception as e:
        logger.debug(f"Error detecting AWS credentials: {e}")
        return result


def detect_gcp_credentials() -> Dict[str, any]:
    """Detect GCP credentials from system.

    Returns:
        dict with 'available', 'source', 'credentials_file', 'project'
    """
    result = {
        "available": False,
        "source": None,
        "credentials_file": None,
        "project": None,
    }

    # Check GOOGLE_APPLICATION_CREDENTIALS environment variable
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_file and Path(creds_file).exists():
        result["available"] = True
        result["source"] = "environment"
        result["credentials_file"] = creds_file
        result["project"] = os.getenv("GOOGLE_CLOUD_PROJECT")
        logger.debug(f"GCP credentials detected from environment: {creds_file}")
        return result

    # Check Application Default Credentials
    adc_path = (
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    )
    if adc_path.exists():
        result["available"] = True
        result["source"] = "adc"
        result["project"] = os.getenv("GOOGLE_CLOUD_PROJECT")
        logger.debug("GCP credentials detected from Application Default Credentials")
        return result

    logger.debug("No GCP credentials detected")
    return result


def detect_azure_credentials() -> Dict[str, any]:
    """Detect Azure credentials from system.

    Returns:
        dict with 'available', 'source'
    """
    result = {
        "available": False,
        "source": None,
    }

    # Check AZURE_STORAGE_CONNECTION_STRING environment variable
    if os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
        result["available"] = True
        result["source"] = "environment"
        logger.debug("Azure credentials detected from environment variable")
        return result

    # Check az CLI authentication
    try:
        result_az = subprocess.run(
            ["az", "account", "show"], capture_output=True, text=True, timeout=5
        )
        if result_az.returncode == 0:
            result["available"] = True
            result["source"] = "az_cli"
            logger.debug("Azure credentials detected from az CLI")
            return result
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    logger.debug("No Azure credentials detected")
    return result


def get_auth_status(backend_type: str) -> Dict[str, any]:
    """Get authentication status for a backend type.

    Args:
        backend_type: Type of backend (s3, gcs, azure, etc.)

    Returns:
        dict with authentication status information
    """
    if backend_type == "s3":
        return {"backend_type": "s3", **detect_aws_credentials()}
    elif backend_type == "gcs":
        return {"backend_type": "gcs", **detect_gcp_credentials()}
    elif backend_type == "azure":
        return {"backend_type": "azure", **detect_azure_credentials()}
    else:
        return {"backend_type": backend_type, "available": False, "source": None}


def get_setup_instructions(backend_type: str) -> str:
    """Get setup instructions for a backend type.

    Args:
        backend_type: Type of backend (s3, gcs, azure, etc.)

    Returns:
        String with CLI commands and setup instructions
    """
    if backend_type == "s3":
        return """AWS Authentication Setup:

Option 1: AWS CLI Configuration (Recommended)
  aws configure

Option 2: AWS SSO
  aws configure sso
  aws sso login

Option 3: Environment Variables
  export AWS_ACCESS_KEY_ID="your-access-key"
  export AWS_SECRET_ACCESS_KEY="your-secret-key"
  export AWS_DEFAULT_REGION="us-west-2"

Option 4: AWS Profile
  export AWS_PROFILE="your-profile-name"
  aws configure --profile your-profile-name

After setup, refresh this page and test the connection."""

    elif backend_type == "gcs":
        return """Google Cloud Authentication Setup:

Option 1: Application Default Credentials (Recommended)
  gcloud auth application-default login

Option 2: Service Account Key File
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

Option 3: User Account
  gcloud auth login

Option 4: Set Project (Optional)
  export GOOGLE_CLOUD_PROJECT="your-project-id"

After setup, refresh this page and test the connection."""

    elif backend_type == "azure":
        return """Azure Authentication Setup:

Option 1: Azure CLI (Recommended)
  az login

Option 2: Connection String
  export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=your-account;AccountKey=your-key"

Option 3: Service Principal
  az login --service-principal --username <app-id> --password <password> --tenant <tenant-id>

After setup, refresh this page and test the connection."""

    else:
        return f"Unknown backend type: {backend_type}. Please check the backend configuration."
