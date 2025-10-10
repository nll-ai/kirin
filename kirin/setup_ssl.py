#!/usr/bin/env python3
"""
Automatic SSL certificate setup for Kirin UI.

This script automatically copies system SSL certificates to the pixi environment
to enable HTTPS connections to cloud storage providers.
"""

import os
import subprocess
import sys
from pathlib import Path
from loguru import logger


def get_ssl_path():
    """Get the SSL certificate path for the current Python executable."""
    import sys
    from pathlib import Path

    # Get the Python executable path
    python_exe = Path(sys.executable)
    python_dir = python_exe.parent

    # For isolated environments, create ssl directory next to Python executable
    ssl_dir = python_dir / "ssl"

    return ssl_dir


def copy_system_certificates(ssl_dir: Path):
    """Copy system SSL certificates to Python environment."""
    ssl_dir.mkdir(parents=True, exist_ok=True)
    cert_file = ssl_dir / "cert.pem"

    try:
        # Copy certificates from macOS system keychain
        with open(cert_file, "w") as f:
            result = subprocess.run(
                [
                    "security",
                    "find-certificate",
                    "-a",
                    "-p",
                    "/System/Library/Keychains/SystemRootCertificates.keychain",
                ],
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"Failed to copy certificates: {result.stderr}")
                return False

        logger.info(f"✅ SSL certificates copied to {cert_file}")
        return True

    except FileNotFoundError:
        logger.error("❌ 'security' command not found. This script requires macOS.")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to copy certificates: {e}")
        return False


def verify_ssl_setup(ssl_dir: Path):
    """Verify that SSL certificates are working."""
    try:
        import ssl
        import requests

        # Check if SSL paths are configured
        ssl_paths = ssl.get_default_verify_paths()
        logger.info(f"SSL paths: {ssl_paths}")

        # Test HTTPS connection
        response = requests.get("https://storage.googleapis.com", timeout=5)
        logger.info(f"✅ HTTPS connection successful: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"❌ SSL verification failed: {e}")
        return False


def detect_environment():
    """Detect if we're using system Python or an isolated environment."""
    import sys

    # Check if we're in an isolated environment
    if (
        os.environ.get("VIRTUAL_ENV")
        or os.environ.get("CONDA_PREFIX")
        or os.environ.get("PIXI_ENV_PATH")
        or os.environ.get("UV_ENV_PATH")
        or "site-packages" in sys.executable
    ):
        return "isolated"
    else:
        return "system"


def setup_ssl_certificates():
    """Main function to set up SSL certificates for Kirin UI."""
    logger.info("🔧 Setting up SSL certificates for Kirin UI...")

    # Detect environment type
    env_type = detect_environment()
    logger.info(f"Detected environment: {env_type}")

    # Get SSL directory path
    ssl_dir = get_ssl_path()
    logger.info(f"SSL directory: {ssl_dir}")

    # Copy system certificates
    if not copy_system_certificates(ssl_dir):
        logger.error("❌ Failed to copy SSL certificates")
        return False

    # Verify setup
    if not verify_ssl_setup(ssl_dir):
        logger.error("❌ SSL setup verification failed")
        return False

    logger.info("🎉 SSL certificates set up successfully!")
    logger.info("You can now use Kirin UI with cloud storage providers.")

    # Provide environment-specific guidance
    if env_type == "system":
        logger.info(
            "ℹ️  Using system Python - SSL certificates should work automatically"
        )
    else:
        logger.info(f"ℹ️  SSL certificates configured for isolated Python environment")

    return True


if __name__ == "__main__":
    success = setup_ssl_certificates()
    sys.exit(0 if success else 1)
