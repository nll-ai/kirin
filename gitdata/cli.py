"""Custom CLI for gitdata.

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
    typer.echo("This project's name is gitdata")


@app.command()
def describe():
    """Describe the project."""
    typer.echo("Version controlled data storage.")


@app.command()
def ui(
    dataset_url: Optional[str] = typer.Option(
        None, "--url", "-u", help="Dataset URL to load on startup"
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
    """Launch the GitData web UI.

    The UI provides a git-like interface for browsing datasets with commit history,
    file listings, and text file previews.

    You can also access datasets directly via URL:
        http://localhost:PORT/d/DATASET_NAME?url=/path/to/data

    This allows you to bookmark and share direct links to specific datasets.

    Examples:
        # Launch UI and load a dataset on startup
        gitdata ui --url /path/to/data --name my-dataset

        # Launch UI on specific port
        gitdata ui --port 8080

        # Launch UI without auto-reload
        gitdata ui --no-reload

        # Direct URL access (after starting the server)
        # http://localhost:8080/d/my-dataset?url=/path/to/data
    """
    from gitdata.web_ui import run_server

    # Use auto_reload=True by default unless --no-reload is specified
    auto_reload = not no_reload

    typer.echo("🚀 Launching GitData UI...")
    if dataset_url and dataset_name:
        typer.echo(f"📦 Loading dataset: {dataset_name} from {dataset_url}")

    run_server(
        dataset_url=dataset_url,
        dataset_name=dataset_name,
        port=port,
        auto_reload=auto_reload,
    )


if __name__ == "__main__":
    app()
