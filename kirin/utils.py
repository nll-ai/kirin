"""Utilities for gitdata."""

import fsspec
from pathlib import Path


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


def get_filesystem(path: str) -> fsspec.AbstractFileSystem:
    """Get filesystem for the given path.

    Args:
        path: Path to determine filesystem for

    Returns:
        fsspec filesystem instance
    """
    # If path has a protocol, use it directly
    if "://" in path:
        protocol = path.split("://")[0]
        return fsspec.filesystem(protocol)
    else:
        # For local paths, use the file protocol
        return fsspec.filesystem("file")
