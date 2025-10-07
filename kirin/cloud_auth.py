"""Helper utilities for authenticating with cloud storage providers."""

from pathlib import Path
from typing import Any, Dict, Optional

import fsspec


def get_gcs_filesystem(
    token: Optional[str | Path] = None, project: Optional[str] = None, **kwargs
) -> fsspec.AbstractFileSystem:
    """Create an authenticated Google Cloud Storage filesystem.

    :param token: Path to service account JSON file, 'cloud' for gcloud credentials,
        'anon' for anonymous, or None for auto-detection.
    :param project: GCP project ID (optional).
    :param kwargs: Additional arguments to pass to gcsfs.
    :return: An authenticated GCS filesystem.

    Examples:
        >>> # Use gcloud credentials
        >>> fs = get_gcs_filesystem(token='cloud')

        >>> # Use service account key file
        >>> fs = get_gcs_filesystem(token='/path/to/key.json')

        >>> # Auto-detect from environment
        >>> fs = get_gcs_filesystem()
    """
    config: Dict[str, Any] = {}

    if token is not None:
        config["token"] = str(token) if isinstance(token, Path) else token

    if project is not None:
        config["project"] = project

    config.update(kwargs)

    try:
        return fsspec.filesystem("gs", **config)
    except ImportError as e:
        raise ValueError(
            "Google Cloud Storage support requires gcsfs. "
            "Install with: pip install gcsfs"
        ) from e


def get_s3_filesystem(
    key: Optional[str] = None,
    secret: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    **kwargs,
) -> fsspec.AbstractFileSystem:
    """Create an authenticated S3 (or S3-compatible) filesystem.

    :param key: AWS access key ID.
    :param secret: AWS secret access key.
    :param endpoint_url: Custom endpoint URL for S3-compatible services
        (Minio, Backblaze B2, DigitalOcean Spaces, etc.).
    :param region: AWS region name.
    :param profile: AWS profile name from ~/.aws/credentials.
    :param kwargs: Additional arguments to pass to s3fs.
    :return: An authenticated S3 filesystem.

    Examples:
        >>> # Use default AWS credentials
        >>> fs = get_s3_filesystem()

        >>> # Use specific credentials
        >>> fs = get_s3_filesystem(key='AKIAIOSFODNN7EXAMPLE',
        ...                        secret='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

        >>> # Use Minio
        >>> fs = get_s3_filesystem(key='minioadmin', secret='minioadmin',
        ...                        endpoint_url='http://localhost:9000')

        >>> # Use Backblaze B2
        >>> fs = get_s3_filesystem(
        ...     key='your-key-id',
        ...     secret='your-key',
        ...     endpoint_url='https://s3.us-west-002.backblazeb2.com'
        ... )
    """
    config: Dict[str, Any] = {}

    if key is not None:
        config["key"] = key

    if secret is not None:
        config["secret"] = secret

    if profile is not None:
        config["profile"] = profile

    # Handle endpoint_url and region through client_kwargs
    client_kwargs = kwargs.pop("client_kwargs", {})

    if endpoint_url is not None:
        client_kwargs["endpoint_url"] = endpoint_url

    if region is not None:
        client_kwargs["region_name"] = region

    if client_kwargs:
        config["client_kwargs"] = client_kwargs

    config.update(kwargs)

    try:
        return fsspec.filesystem("s3", **config)
    except ImportError as e:
        raise ValueError(
            "S3 support requires s3fs. Install with: pip install s3fs"
        ) from e


def get_azure_filesystem(
    account_name: Optional[str] = None,
    account_key: Optional[str] = None,
    connection_string: Optional[str] = None,
    **kwargs,
) -> fsspec.AbstractFileSystem:
    """Create an authenticated Azure Blob Storage filesystem.

    :param account_name: Azure storage account name.
    :param account_key: Azure storage account key.
    :param connection_string: Azure storage connection string.
    :param kwargs: Additional arguments to pass to adlfs.
    :return: An authenticated Azure filesystem.

    Examples:
        >>> # Use connection string
        >>> fs = get_azure_filesystem(
        ...     connection_string='DefaultEndpointsProtocol=https;...'
        ... )

        >>> # Use account name and key
        >>> fs = get_azure_filesystem(
        ...     account_name='myaccount',
        ...     account_key='mykey'
        ... )
    """
    config: Dict[str, Any] = {}

    if connection_string is not None:
        config["connection_string"] = connection_string
    elif account_name is not None and account_key is not None:
        config["account_name"] = account_name
        config["account_key"] = account_key

    config.update(kwargs)

    try:
        return fsspec.filesystem("az", **config)
    except ImportError as e:
        raise ValueError(
            "Azure Blob Storage support requires adlfs. Install with: pip install adlfs"
        ) from e


# Convenience dictionary for common S3-compatible service endpoints
S3_COMPATIBLE_ENDPOINTS = {
    "minio": "http://localhost:9000",
    "backblaze_us_west": "https://s3.us-west-002.backblazeb2.com",
    "backblaze_us_east": "https://s3.us-east-005.backblazeb2.com",
    "backblaze_eu_central": "https://s3.eu-central-003.backblazeb2.com",
    "digitalocean_nyc3": "https://nyc3.digitaloceanspaces.com",
    "digitalocean_sfo3": "https://sfo3.digitaloceanspaces.com",
    "digitalocean_sgp1": "https://sgp1.digitaloceanspaces.com",
    "wasabi_us_east_1": "https://s3.wasabisys.com",
    "wasabi_us_west_1": "https://s3.us-west-1.wasabisys.com",
}


def get_s3_compatible_filesystem(
    service: str, key: str, secret: str, custom_endpoint: Optional[str] = None, **kwargs
) -> fsspec.AbstractFileSystem:
    """Create a filesystem for S3-compatible services with preset endpoints.

    :param service: Service name (e.g., 'minio', 'backblaze_us_west',
        'digitalocean_nyc3').
    :param key: Access key ID.
    :param secret: Secret access key.
    :param custom_endpoint: Custom endpoint URL (overrides service preset).
    :param kwargs: Additional arguments to pass to s3fs.
    :return: An authenticated S3-compatible filesystem.

    Examples:
        >>> # Minio
        >>> fs = get_s3_compatible_filesystem(
        ...     service='minio',
        ...     key='minioadmin',
        ...     secret='minioadmin'
        ... )

        >>> # Backblaze B2
        >>> fs = get_s3_compatible_filesystem(
        ...     service='backblaze_us_west',
        ...     key='your-key-id',
        ...     secret='your-key'
        ... )
    """
    endpoint = custom_endpoint or S3_COMPATIBLE_ENDPOINTS.get(service)

    if endpoint is None:
        available = ", ".join(S3_COMPATIBLE_ENDPOINTS.keys())
        raise ValueError(
            f"Unknown S3-compatible service: {service}. "
            f"Available services: {available}. "
            f"Or provide custom_endpoint parameter."
        )

    return get_s3_filesystem(key=key, secret=secret, endpoint_url=endpoint, **kwargs)
