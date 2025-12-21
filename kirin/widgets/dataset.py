"""Dataset widget for interactive HTML representation."""

from pathlib import Path

import traitlets

from .base import BaseWidget


class DatasetWidget(BaseWidget):
    """Interactive dataset widget with files and commit history."""

    _esm = Path(__file__).parent / "assets" / "dataset.js"

    # Python state synchronized with JavaScript
    expanded_files = traitlets.List(default_value=[]).tag(sync=True)

    @property
    def template_name(self) -> str:
        """Return the template filename for this widget."""
        return "dataset.html"
