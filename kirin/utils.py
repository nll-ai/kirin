"""Utilities for kirin."""

import os
from pathlib import Path
from typing import Optional, Union

import fsspec
from loguru import logger


def strip_protocol(path: str) -> str:
    """Strip protocol prefix from a path for use with fsspec filesystems.

    fsspec filesystem objects already know their protocol, so paths should be
    passed without the protocol prefix (e.g., 'bucket/path' not 'gs://bucket/path').

    :param path: Path that may include protocol (e.g., 's3://bucket/path').
    :return: Path without protocol prefix.

    Examples:
        >>> strip_protocol('s3://bucket/path/file.txt')
        'bucket/path/file.txt'
        >>> strip_protocol('gs://bucket/path')
        'bucket/path'
        >>> strip_protocol('/local/path')
        '/local/path'
    """
    if "://" in path:
        return path.split("://", 1)[1]
    return path


def get_filesystem(
    path: str,
    aws_profile: Optional[str] = None,
    gcs_token: Optional[Union[str, Path]] = None,
    gcs_project: Optional[str] = None,
    azure_account_name: Optional[str] = None,
    azure_account_key: Optional[str] = None,
    azure_connection_string: Optional[str] = None,
) -> fsspec.AbstractFileSystem:
    """Get filesystem for the given path with cloud provider authentication.

    Args:
        path: Path to determine filesystem for
        aws_profile: Optional AWS profile name for S3 authentication
        gcs_token: Optional GCS token (service account JSON path, 'cloud', or None)
        gcs_project: Optional GCP project ID
        azure_account_name: Optional Azure storage account name
        azure_account_key: Optional Azure storage account key
        azure_connection_string: Optional Azure connection string

    Returns:
        fsspec filesystem instance
    """
    # If path has a protocol, use it directly
    if "://" in path:
        protocol = path.split("://")[0]

        # For S3, use boto3 to resolve credentials (supports SSO, profiles, etc.)
        if protocol == "s3":
            return _get_s3_filesystem_with_credentials(aws_profile)
        elif protocol == "gs":
            return _get_gcs_filesystem_with_credentials(
                token=gcs_token, project=gcs_project
            )
        elif protocol == "az":
            return _get_azure_filesystem_with_credentials(
                account_name=azure_account_name,
                account_key=azure_account_key,
                connection_string=azure_connection_string,
            )
        else:
            return fsspec.filesystem(protocol)
    else:
        # For local paths, use the file protocol
        return fsspec.filesystem("file")


def _get_s3_filesystem_with_credentials(
    aws_profile: Optional[str] = None,
) -> fsspec.AbstractFileSystem:
    """Create S3 filesystem with AWS credentials using boto3.

    This function uses boto3's credential chain to resolve credentials, which supports:
    - AWS SSO (aws sso login)
    - AWS profiles (~/.aws/credentials, ~/.aws/config)
    - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - Instance roles (EC2, ECS, Lambda)
    - Web identity tokens

    Args:
        aws_profile: Optional AWS profile name. If None, uses AWS_PROFILE env var
        or 'default'

    Returns:
        Authenticated S3 filesystem
    """
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ProfileNotFound
    except ImportError:
        raise ValueError("S3 support requires boto3. Install with: pip install boto3")

    # Determine which profile to use
    profile_name = aws_profile or os.getenv("AWS_PROFILE", "default")

    try:
        # Create boto3 session with the specified profile
        session = boto3.Session(profile_name=profile_name)

        # Get credentials from the session
        credentials = session.get_credentials()

        if not credentials:
            logger.warning(f"No credentials found for AWS profile: {profile_name}")
            # Fall back to anonymous access
            return fsspec.filesystem("s3")

        # Extract credential components
        access_key = credentials.access_key
        secret_key = credentials.secret_key
        session_token = getattr(credentials, "token", None)

        logger.info(f"Using AWS credentials for profile: {profile_name}")
        logger.debug(f"Access key: {access_key[:8]}...")

        # Create S3 filesystem with credentials
        s3_config = {
            "key": access_key,
            "secret": secret_key,
        }

        # Add session token if present (for SSO, STS, etc.)
        if session_token:
            s3_config["token"] = session_token
            logger.debug("Using session token for authentication")

        # Get region from session or environment
        region = session.region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        if region:
            s3_config["client_kwargs"] = {"region_name": region}

        return fsspec.filesystem("s3", **s3_config)

    except ProfileNotFound as e:
        logger.error(f"AWS profile '{profile_name}' not found: {e}")
        raise ValueError(
            f"AWS profile '{profile_name}' not found. "
            "Please check your AWS configuration."
        )
    except NoCredentialsError as e:
        logger.error(f"No AWS credentials found: {e}")
        raise ValueError(
            "No AWS credentials found. Please run 'aws sso login' or "
            "configure AWS credentials. See: "
            "https://docs.aws.amazon.com/cli/latest/userguide/"
            "cli-configure-files.html"
        )
    except Exception as e:
        logger.error(f"Failed to create S3 filesystem: {e}")
        raise ValueError(f"Failed to create S3 filesystem: {e}")


def _get_gcs_filesystem_with_credentials(
    token: Optional[Union[str, Path]] = None,
    project: Optional[str] = None,
) -> fsspec.AbstractFileSystem:
    """Create GCS filesystem with credentials.

    Args:
        token: Optional GCS token (service account JSON path, 'cloud', or None)
        project: Optional GCP project ID

    Returns:
        Authenticated GCS filesystem
    """
    from .cloud_auth import get_gcs_filesystem
    return get_gcs_filesystem(token=token, project=project)


def _get_azure_filesystem_with_credentials(
    account_name: Optional[str] = None,
    account_key: Optional[str] = None,
    connection_string: Optional[str] = None,
) -> fsspec.AbstractFileSystem:
    """Create Azure filesystem with credentials.

    Args:
        account_name: Optional Azure storage account name
        account_key: Optional Azure storage account key
        connection_string: Optional Azure connection string

    Returns:
        Authenticated Azure filesystem
    """
    from .cloud_auth import get_azure_filesystem
    return get_azure_filesystem(
        account_name=account_name,
        account_key=account_key,
        connection_string=connection_string,
    )
