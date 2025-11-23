"""Thumbnail storage for Kirin image files.

This module provides thumbnail generation and storage for image files stored
in Kirin datasets. Thumbnails are stored in a separate directory structure
with content-addressed paths based on the original file's content hash.
"""

import io
from pathlib import Path
from typing import Optional, Union

import fsspec
from loguru import logger

from .utils import get_filesystem, strip_protocol

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class ThumbnailStore:
    """Manages thumbnail storage for image files.

    Thumbnails are stored at root_dir/thumbnails/{hash[:2]}/{hash[2:]}/thumbnail.webp
    with content-addressed paths based on the original file's content hash.

    Args:
        root_dir: Root directory for thumbnail storage
        fs: Filesystem to use (auto-detected from root_dir if None)
    """

    def __init__(
        self, root_dir: Union[str, Path], fs: Optional[fsspec.AbstractFileSystem] = None
    ):
        self.root_dir = str(root_dir)
        self.fs = fs or get_filesystem(self.root_dir)
        self.thumbnails_dir = f"{self.root_dir}/thumbnails"

        # Ensure thumbnails directory exists
        self.fs.makedirs(strip_protocol(self.thumbnails_dir), exist_ok=True)
        logger.info(f"Thumbnail store initialized at {self.thumbnails_dir}")

    def get_thumbnail_path(self, file_hash: str) -> str:
        """Get the storage path for a thumbnail based on file hash.

        Args:
            file_hash: Content hash of the original file

        Returns:
            Storage path for the thumbnail
        """
        # Create storage path: thumbnails/{hash[:2]}/{hash[2:]}/thumbnail.webp
        hash_dir = f"{self.thumbnails_dir}/{file_hash[:2]}"
        content_dir = f"{hash_dir}/{file_hash[2:]}"
        thumbnail_path = f"{content_dir}/thumbnail.webp"
        return thumbnail_path

    def store_thumbnail(self, file_hash: str, thumbnail_bytes: bytes) -> None:
        """Store thumbnail bytes at the appropriate location.

        Args:
            file_hash: Content hash of the original file
            thumbnail_bytes: Thumbnail image bytes (WebP format)
        """
        thumbnail_path = self.get_thumbnail_path(file_hash)

        # Ensure directory exists
        content_dir = f"{self.thumbnails_dir}/{file_hash[:2]}/{file_hash[2:]}"
        self.fs.makedirs(strip_protocol(content_dir), exist_ok=True)

        # Write thumbnail
        with self.fs.open(strip_protocol(thumbnail_path), "wb") as f:
            f.write(thumbnail_bytes)

        logger.info(f"Stored thumbnail for file hash {file_hash[:8]}")

    def retrieve_thumbnail(self, file_hash: str) -> bytes:
        """Retrieve thumbnail bytes by file hash.

        Args:
            file_hash: Content hash of the original file

        Returns:
            Thumbnail image bytes (WebP format)

        Raises:
            FileNotFoundError: If thumbnail doesn't exist
            IOError: If there's an error reading the thumbnail
        """
        if not self.thumbnail_exists(file_hash):
            raise FileNotFoundError(
                f"Thumbnail not found for file hash {file_hash[:8]}"
            )

        try:
            thumbnail_path = self.get_thumbnail_path(file_hash)
            with self.fs.open(strip_protocol(thumbnail_path), "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to retrieve thumbnail for {file_hash[:8]}: {e}")
            raise IOError(f"Failed to retrieve thumbnail: {e}") from e

    def thumbnail_exists(self, file_hash: str) -> bool:
        """Check if thumbnail exists for a file hash.

        Args:
            file_hash: Content hash of the original file

        Returns:
            True if thumbnail exists, False otherwise
        """
        try:
            thumbnail_path = self.get_thumbnail_path(file_hash)
            return self.fs.exists(strip_protocol(thumbnail_path))
        except Exception:
            return False

    def get_or_generate_thumbnail(
        self, file_hash: str, file_content: bytes
    ) -> bytes:
        """Get existing thumbnail or generate a new one.

        Args:
            file_hash: Content hash of the original file
            file_content: Original file content bytes

        Returns:
            Thumbnail image bytes (WebP format)

        Raises:
            ImportError: If Pillow is not available for thumbnail generation
            IOError: If there's an error generating the thumbnail
        """
        # Check if thumbnail already exists
        if self.thumbnail_exists(file_hash):
            logger.info(f"Using cached thumbnail for file hash {file_hash[:8]}")
            return self.retrieve_thumbnail(file_hash)

        # Generate new thumbnail
        if not HAS_PILLOW:
            raise ImportError(
                "Pillow is required for thumbnail generation. "
                "Install it with: pip install pillow"
            )

        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(file_content))

            # Calculate thumbnail size (max 150x150, maintain aspect ratio)
            max_size = 150
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Convert to WebP
            buffer = io.BytesIO()
            img.save(buffer, format="webp", quality=85)
            thumbnail_bytes = buffer.getvalue()

            # Store thumbnail
            self.store_thumbnail(file_hash, thumbnail_bytes)

            logger.info(f"Generated thumbnail for file hash {file_hash[:8]}")
            return thumbnail_bytes

        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {file_hash[:8]}: {e}")
            raise IOError(f"Failed to generate thumbnail: {e}") from e
