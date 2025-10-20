"""CLI interface for Kirin."""

import socket
from pathlib import Path
from typing import List

import typer
import uvicorn
from loguru import logger

from .web.config import CatalogManager

app = typer.Typer()


def find_free_port() -> int:
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@app.command()
def ui() -> None:
    """Launch the Kirin web interface."""
    port = find_free_port()
    logger.info(f"Using random port: {port}")

    logger.info(f"Starting Kirin web interface on 127.0.0.1:{port}")
    logger.info("PERF: Web interface starting with auto-reload enabled")

    uvicorn.run(
        "kirin.web.app:app",
        host="127.0.0.1",
        port=port,
        reload=True,  # Auto-reload enabled per user preference
        log_level="info",
    )


@app.command()
def upload(
    catalog: str = typer.Option(..., "--catalog", "-c", help="Catalog ID"),
    dataset: str = typer.Option(..., "--dataset", "-d", help="Dataset name"),
    commit_message: str = typer.Option(
        ..., "--commit-message", "-m", help="Commit message"
    ),
    files: List[str] = typer.Argument(..., help="Files to upload"),
) -> None:
    """Upload files to a dataset in a catalog."""
    if not files:
        typer.echo("Error: No files provided", err=True)
        raise typer.Exit(1)

    # Load catalog configuration
    catalog_manager = CatalogManager()
    catalog_config = catalog_manager.get_catalog(catalog)

    if catalog_config is None:
        typer.echo(f"Error: Catalog not found: {catalog}", err=True)
        raise typer.Exit(1)

    # Convert strings to Path objects and validate files exist
    file_paths = [Path(f) for f in files]
    missing_files = []
    for file_path in file_paths:
        if not file_path.exists():
            missing_files.append(str(file_path))

    if missing_files:
        for file_path in missing_files:
            typer.echo(f"Error: File not found: {file_path}", err=True)
        raise typer.Exit(1)

    try:
        # Convert config to Catalog instance with authentication
        catalog_instance = catalog_config.to_catalog()

        # Get or create dataset
        dataset_instance = catalog_instance.get_dataset(dataset)

        # Upload files in single commit
        commit_hash = dataset_instance.commit(
            message=commit_message, add_files=file_paths
        )

        # Report success
        typer.echo(f"✓ Uploaded {len(files)} file(s) to {dataset}")
        typer.echo(f"  Commit: {commit_hash[:8]}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
