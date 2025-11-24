"""Plot saving functionality for Kirin.

This module provides functions to save plots from various plotting libraries
(matplotlib, plotly, seaborn, etc.) in optimal formats (SVG for vectors,
WebP for bitmaps) with automatic format detection.
"""

import io
import os
from typing import TYPE_CHECKING, Optional, Tuple, Union

from loguru import logger

from .utils import detect_source_file

if TYPE_CHECKING:
    from .storage import ContentStore

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    go = None
    HAS_PLOTLY = False

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    Image = None
    HAS_PILLOW = False


def save_plot(
    plot_object: Union[  # noqa: F821
        "matplotlib.figure.Figure", "plotly.graph_objects.Figure", object  # noqa: F821
    ],
    filename: str,
    storage: "ContentStore",
    format: Optional[str] = None,
) -> Tuple[str, str, Optional[str], Optional[str]]:
    """Save a plot to content-addressed storage with automatic format detection.

    Automatically detects the plot type (matplotlib, plotly, etc.) and chooses
    the optimal format (SVG for vector graphics, WebP for bitmap/raster plots).

    **Important: Strict Content Hashing for SVG Plots**

    Kirin uses **strict content-addressed hashing** - files are identified by
    their exact byte content. This means:

    - **SVG plots will produce different hashes** even when the plot content
      is identical, because matplotlib embeds creation timestamps in the SVG
      metadata (`<dc:date>` elements). This is the strictest form of hashing
      and ensures complete content integrity.

    - **Identical plots = different commits**: If you save the same plot twice
      (same data, same code), you'll get different hashes and thus different
      commits, because the SVG files differ by their timestamps.

    - **This is by design**: Content-addressed storage requires exact byte
      matching. The timestamp metadata is part of the file content, so it
      affects the hash.

    - **For deterministic hashing**: If you need identical plots to produce
      identical hashes, you would need to strip metadata before saving, but
      this is not currently implemented as it would modify the original file
      content.

    Args:
        plot_object: The plot object to save (matplotlib Figure, plotly Figure, etc.)
        filename: Desired filename for the plot (extension may be adjusted)
        storage: ContentStore instance to use for storage
        format: Optional format override ('svg' or 'webp'). If None, auto-detects.

    Returns:
        Tuple of (content_hash, actual_filename, source_file_path, source_file_hash)
        where:
        - content_hash: Hash of the stored plot file
        - actual_filename: Filename used (may have extension adjusted based on format)
        - source_file_path: Path to source notebook/script, or None if not detected
        - source_file_hash: Hash of stored source file, or None if not detected

    Raises:
        ValueError: If plot type is not supported or format detection fails
        ImportError: If required libraries are not available
    """
    # Detect source file
    source_file_path = detect_source_file()
    source_file_hash = None

    # If source file detected, read and store it
    if source_file_path and os.path.exists(source_file_path):
        try:
            with open(source_file_path, "rb") as f:
                source_content = f.read()

            # Get just the filename from the path for storage
            source_filename = os.path.basename(source_file_path)

            # Store source file in content-addressed storage
            source_file_hash = storage.store_content(source_content, source_filename)
            logger.info(
                f"Detected and stored source file: {source_filename} "
                f"(hash: {source_file_hash[:8]})"
            )
        except Exception as e:
            logger.warning(
                f"Failed to store source file {source_file_path}: {e}. "
                "Plot will be saved without source linking."
            )
            source_file_path = None
            source_file_hash = None

    # Detect plot type and determine format
    if format is None:
        format = _detect_plot_format(plot_object, filename)

    # Save based on plot type
    if HAS_MATPLOTLIB and plt is not None and isinstance(plot_object, plt.Figure):
        content_hash, actual_filename = _save_matplotlib_plot(
            plot_object, filename, storage, format
        )
    elif HAS_PLOTLY and go is not None and isinstance(plot_object, go.Figure):
        content_hash, actual_filename = _save_plotly_plot(
            plot_object, filename, storage, format
        )
    else:
        raise ValueError(
            f"Unsupported plot type: {type(plot_object)}. "
            "Supported types: matplotlib.Figure, plotly.graph_objects.Figure"
        )

    return (content_hash, actual_filename, source_file_path, source_file_hash)


def _detect_plot_format(plot_object: object, filename: str) -> str:
    """Detect optimal format for a plot.

    Args:
        plot_object: The plot object
        filename: Original filename (for extension hints)

    Returns:
        Format string: 'svg' or 'webp'
    """
    # Default format detection based on plot type (prioritize plot type over filename)
    if HAS_MATPLOTLIB and plt is not None and isinstance(plot_object, plt.Figure):
        # For matplotlib, default to SVG (most plots are vector-based)
        # Could be enhanced to check if plot contains raster elements
        return "svg"
    elif HAS_PLOTLY and go is not None and isinstance(plot_object, go.Figure):
        # Plotly figures are inherently vector-based
        return "svg"
    else:
        # Check filename extension for hints if plot type unknown
        filename_lower = filename.lower()
        if filename_lower.endswith(".svg"):
            return "svg"
        if filename_lower.endswith((".webp", ".png", ".jpg", ".jpeg")):
            return "webp"
        # Default to SVG for unknown types
        return "svg"


def _save_matplotlib_plot(
    fig: "matplotlib.figure.Figure",  # noqa: F821
    filename: str,
    storage: "ContentStore",
    format: str,
) -> tuple[str, str]:
    """Save a matplotlib figure to storage.

    Args:
        fig: Matplotlib figure object
        filename: Desired filename
        storage: ContentStore instance
        format: Format to use ('svg' or 'webp')

    Returns:
        Content hash of stored file
    """
    # Adjust filename extension based on format
    if format == "svg":
        if not filename.lower().endswith(".svg"):
            filename = filename.rsplit(".", 1)[0] + ".svg"
    elif format == "webp":
        if not filename.lower().endswith(".webp"):
            filename = filename.rsplit(".", 1)[0] + ".webp"
    else:
        raise ValueError(f"Unsupported format for matplotlib: {format}")

    # Save to bytes buffer
    buffer = io.BytesIO()
    if format == "svg":
        fig.savefig(buffer, format="svg", bbox_inches="tight")
    elif format == "webp":
        if not HAS_PILLOW:
            logger.warning(
                "Pillow not available, falling back to PNG for matplotlib WebP export"
            )
            fig.savefig(buffer, format="png", bbox_inches="tight")
            # Convert PNG to WebP if Pillow is available
            if HAS_PILLOW and Image is not None:
                buffer.seek(0)
                img = Image.open(buffer)
                buffer = io.BytesIO()
                img.save(buffer, format="webp")
        else:
            fig.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)
            if Image is not None:
                img = Image.open(buffer)
                buffer = io.BytesIO()
                img.save(buffer, format="webp")
    else:
        raise ValueError(f"Unsupported format: {format}")

    buffer.seek(0)
    content = buffer.read()
    buffer.close()

    # Store in content-addressed storage
    content_hash = storage.store_content(content, filename)

    logger.info(
        f"Saved matplotlib plot as {format.upper()} with hash {content_hash[:8]}"
    )

    return (content_hash, filename)


def _save_plotly_plot(
    fig: "plotly.graph_objects.Figure",  # noqa: F821
    filename: str,
    storage: "ContentStore",
    format: str,
) -> tuple[str, str]:
    """Save a plotly figure to storage.

    Args:
        fig: Plotly figure object
        filename: Desired filename
        storage: ContentStore instance
        format: Format to use ('svg' or 'webp')

    Returns:
        Content hash of stored file
    """
    # Adjust filename extension based on format
    if format == "svg":
        if not filename.lower().endswith(".svg"):
            filename = filename.rsplit(".", 1)[0] + ".svg"
        # Plotly's to_image returns bytes for SVG
        content_bytes = fig.to_image(format="svg")
    elif format == "webp":
        if not filename.lower().endswith(".webp"):
            filename = filename.rsplit(".", 1)[0] + ".webp"
        # Plotly can export to PNG, then convert to WebP
        png_bytes = fig.to_image(format="png")
        if HAS_PILLOW and Image is not None:
            img = Image.open(io.BytesIO(png_bytes))
            buffer = io.BytesIO()
            img.save(buffer, format="webp")
            content_bytes = buffer.getvalue()
        else:
            logger.warning(
                "Pillow not available, using PNG instead of WebP for plotly export"
            )
            content_bytes = png_bytes
            filename = filename.rsplit(".", 1)[0] + ".png"
    else:
        raise ValueError(f"Unsupported format for plotly: {format}")

    # Store in content-addressed storage
    content_hash = storage.store_content(content_bytes, filename)

    logger.info(f"Saved plotly plot as {format.upper()} with hash {content_hash[:8]}")

    return (content_hash, filename)
