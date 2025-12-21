"""Commit widget for interactive HTML representation."""

from pathlib import Path

from .base import BaseWidget


class CommitWidget(BaseWidget):
    """Interactive commit widget with file list."""

    _esm = Path(__file__).parent / "assets" / "commit.js"

    @property
    def template_name(self) -> str:
        """Return the template filename for this widget."""
        return "commit.html"
