"""Catalog widget for interactive HTML representation."""

from pathlib import Path

from .base import BaseWidget


class CatalogWidget(BaseWidget):
    """Interactive catalog widget with dataset list."""

    _esm = Path(__file__).parent / "assets" / "catalog.js"

    @property
    def template_name(self) -> str:
        """Return the template filename for this widget."""
        return "catalog.html"
