"""Catalog configuration manager for Kirin Web UI."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from loguru import logger

from ..utils import get_filesystem


@dataclass
class CatalogConfig:
    """Configuration for a data catalog."""

    id: str
    name: str
    root_dir: str
    aws_profile: Optional[str] = None


class CatalogManager:
    """Manages data catalog configurations."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize catalog manager.

        Args:
            config_dir: Directory to store config files (defaults to ~/.kirin)
        """
        if config_dir is None:
            config_dir = Path.home() / ".kirin"
        else:
            config_dir = Path(config_dir)

        self.config_dir = config_dir
        self.config_file = config_dir / "catalogs.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize empty config if file doesn't exist
        if not self.config_file.exists():
            self._save_catalogs([])

    def _load_catalogs(self) -> List[dict]:
        """Load catalogs from config file."""
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                return data.get("catalogs", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load catalogs config: {e}")
            return []

    def _save_catalogs(self, catalogs: List[dict]) -> None:
        """Save catalogs to config file."""
        try:
            data = {"catalogs": catalogs}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(catalogs)} catalogs to config")
        except Exception as e:
            logger.error(f"Failed to save catalogs config: {e}")
            raise

    def list_catalogs(self) -> List[CatalogConfig]:
        """List all configured catalogs."""
        catalogs_data = self._load_catalogs()
        return [CatalogConfig(**catalog) for catalog in catalogs_data]

    def get_catalog(self, catalog_id: str) -> Optional[CatalogConfig]:
        """Get a specific catalog by ID."""
        catalogs = self.list_catalogs()
        for catalog in catalogs:
            if catalog.id == catalog_id:
                return catalog
        return None

    def add_catalog(self, catalog: CatalogConfig) -> None:
        """Add a new catalog configuration."""
        catalogs = self._load_catalogs()

        # Check if catalog ID already exists
        for existing in catalogs:
            if existing["id"] == catalog.id:
                raise ValueError(f"Catalog with ID '{catalog.id}' already exists")

        # Add new catalog
        catalogs.append(asdict(catalog))
        self._save_catalogs(catalogs)
        logger.info(f"Added catalog: {catalog.name} ({catalog.id})")

    def update_catalog(self, catalog: CatalogConfig) -> None:
        """Update an existing catalog configuration."""
        catalogs = self._load_catalogs()

        # Find and update catalog
        for i, existing in enumerate(catalogs):
            if existing["id"] == catalog.id:
                catalogs[i] = asdict(catalog)
                self._save_catalogs(catalogs)
                logger.info(f"Updated catalog: {catalog.name} ({catalog.id})")
                return

        raise ValueError(f"Catalog with ID '{catalog.id}' not found")

    def delete_catalog(self, catalog_id: str) -> None:
        """Delete a catalog configuration."""
        catalogs = self._load_catalogs()

        # Find and remove catalog
        for i, catalog in enumerate(catalogs):
            if catalog["id"] == catalog_id:
                del catalogs[i]
                self._save_catalogs(catalogs)
                logger.info(f"Deleted catalog: {catalog_id}")
                return

        raise ValueError(f"Catalog with ID '{catalog_id}' not found")

    def clear_all_catalogs(self) -> None:
        """Clear all catalog configurations (for testing)."""
        self._save_catalogs([])
        logger.info("Cleared all catalogs")

    def create_filesystem(self, catalog: CatalogConfig):
        """Create a filesystem instance for a catalog.

        Args:
            catalog: Catalog configuration

        Returns:
            fsspec filesystem instance
        """
        logger.info(f"Creating filesystem for catalog: {catalog.id}")
        logger.info(f"Root dir: {catalog.root_dir}")
        if catalog.aws_profile:
            logger.info(f"Using AWS profile: {catalog.aws_profile}")

        try:
            # Use Kirin's get_filesystem utility which handles all the complexity
            fs = get_filesystem(catalog.root_dir, aws_profile=catalog.aws_profile)
            logger.info(f"Filesystem created successfully: {type(fs)}")
            return fs
        except Exception as e:
            logger.error(f"Failed to create filesystem for {catalog.root_dir}: {e}")
            raise
