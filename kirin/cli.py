"""Custom CLI for kirin.

This is totally optional;
if you want to use it, though,
follow the skeleton to flesh out the CLI to your liking!
Finally, familiarize yourself with Typer,
which is the package that we use to enable this magic.
Typer's docs can be found at:

    https://typer.tiangolo.com
"""

from typing import Optional

import typer

app = typer.Typer()


@app.command()
def hello():
    """Echo the project's name."""
    typer.echo("This project's name is kirin")


@app.command()
def describe():
    """Describe the project."""
    typer.echo("Version controlled data storage.")


@app.command()
def ui(
    root_dir: Optional[str] = typer.Option(
        None, "--root-dir", "-r", help="Dataset root directory to load on startup"
    ),
    dataset_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Dataset name to load on startup"
    ),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Port to run the server on (default: random port)"
    ),
    no_reload: bool = typer.Option(
        False, "--no-reload", help="Disable auto-reload mode"
    ),
):
    """Launch the Kirin web UI.

    The UI provides a git-like interface for browsing datasets with commit history,
    file listings, and text file previews.

    You can also access datasets directly via URL:
        http://localhost:PORT/d/DATASET_NAME?root_dir=/path/to/data

    This allows you to bookmark and share direct links to specific datasets.

    The root_dir parameter specifies the root directory of your data storage,
    which can be a local path or a cloud storage URL (S3, GCS, Azure, etc.).

    Examples:
        # Launch UI and load a dataset on startup
        kirin ui --root-dir /path/to/data --name my-dataset

        # Launch UI with cloud storage
        kirin ui --root-dir s3://my-bucket/data --name my-dataset

        # Launch UI on specific port
        kirin ui --port 8080

        # Launch UI without auto-reload
        kirin ui --no-reload

        # Direct URL access (after starting the server)
        # http://localhost:8080/d/my-dataset?root_dir=/path/to/data
    """
    from kirin.web_ui import run_server

    # Use auto_reload=True by default unless --no-reload is specified
    auto_reload = not no_reload

    typer.echo("🚀 Launching Kirin UI...")
    if root_dir and dataset_name:
        typer.echo(f"📦 Loading dataset: {dataset_name} from {root_dir}")

    run_server(
        dataset_url=root_dir,
        dataset_name=dataset_name,
        port=port,
        auto_reload=auto_reload,
    )


if __name__ == "__main__":
    app()
