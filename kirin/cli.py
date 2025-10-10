"""CLI interface for Kirin."""

import socket
import sys

import typer
import uvicorn
from loguru import logger

app = typer.Typer()


def find_free_port() -> int:
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


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


def main() -> None:
    """Main entry point for the CLI."""
    if len(sys.argv) > 1 and sys.argv[1] == "ui":
        ui()
    else:
        print("Usage: kirin ui")
        print("Launch the Kirin web interface.")
        sys.exit(1)


if __name__ == "__main__":
    main()
