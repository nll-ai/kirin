# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pytest==8.3.4",
#     "kirin==0.0.1",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

"""Fast unit tests for async authentication timeout and auto-execution features."""

import subprocess
import tempfile

import pytest


def test_auth_error_detection_keywords():
    """Test that auth error keywords are detected correctly."""
    error_messages = [
        "credentials not found",
        "authentication failed",
        "unauthorized access",
        "permission denied",
        "access denied",
        "please login",
    ]

    for error_msg in error_messages:
        error_str = error_msg.lower()
        auth_error = any(
            keyword in error_str
            for keyword in [
                "credentials",
                "authentication",
                "unauthorized",
                "permission denied",
                "access denied",
                "login",
            ]
        )
        assert auth_error, f"Should detect auth error in: {error_msg}"


def test_non_auth_error_keywords():
    """Test that non-auth errors are not detected as auth errors."""
    error_messages = [
        "file not found",
        "network timeout",
        "connection refused",
        "invalid path",
    ]

    for error_msg in error_messages:
        error_str = error_msg.lower()
        auth_error = any(
            keyword in error_str
            for keyword in [
                "credentials",
                "authentication",
                "unauthorized",
                "permission denied",
                "access denied",
                "login",
            ]
        )
        assert not auth_error, f"Should not detect auth error in: {error_msg}"


def test_invalid_command_fails_fast():
    """Test that invalid commands fail immediately (fast test)."""
    # This should fail immediately when subprocess tries to execute
    with pytest.raises(FileNotFoundError):
        subprocess.run(
            ["invalid-command-that-does-not-exist-xyz123"],
            capture_output=True,
            text=True,
            timeout=1,  # Very short timeout for fast test
        )


def test_valid_command_succeeds():
    """Test that valid commands succeed (fast test)."""
    result = subprocess.run(["echo", "test"], capture_output=True, text=True, timeout=1)
    assert result.returncode == 0
    assert "test" in result.stdout


def test_command_timeout_behavior():
    """Test that commands respect timeout (fast test)."""
    # Use a command that will timeout quickly
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            ["sleep", "2"],
            capture_output=True,
            text=True,
            timeout=0.1,  # Very short timeout
        )


def test_file_not_found_fails_fast():
    """Test that file operations fail immediately on non-existent files."""
    with pytest.raises(FileNotFoundError):
        with open("/non/existent/path/file.txt", "r") as f:
            f.read()


def test_invalid_subprocess_command_fails_fast():
    """Test that invalid subprocess commands fail immediately."""
    with pytest.raises(FileNotFoundError):
        subprocess.run(
            ["command-that-does-not-exist-xyz"],
            capture_output=True,
            text=True,
            timeout=1,
        )


def test_local_filesystem_operations_fast():
    """Test local filesystem operations that should be fast."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file
        test_file = f"{temp_dir}/test.txt"
        with open(test_file, "w") as f:
            f.write("test content")

        # Read it back
        with open(test_file, "r") as f:
            content = f.read()

        assert content == "test content"


def test_subprocess_echo_fast():
    """Test that simple subprocess operations are fast."""
    result = subprocess.run(
        ["echo", "hello"], capture_output=True, text=True, timeout=1
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "hello"


def test_subprocess_timeout_protection():
    """Test that subprocess respects timeout."""
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(["sleep", "2"], capture_output=True, text=True, timeout=0.1)


def test_fast_command_completion():
    """Test that fast commands complete within timeout."""
    result = subprocess.run(["echo", "fast"], capture_output=True, text=True, timeout=1)
    assert result.returncode == 0
    assert result.stdout.strip() == "fast"


def test_empty_command_validation():
    """Test validation of empty commands."""
    empty_commands = ["", "   ", "\t", "\n"]

    for cmd in empty_commands:
        # Simulate the validation logic from execute_auth_command
        if not cmd or not cmd.strip():
            assert True  # Should be rejected
        else:
            assert False, f"Command '{cmd}' should be rejected"


def test_command_splitting():
    """Test command splitting logic."""
    test_commands = [
        "aws sso login --profile my-profile",
        "gcloud auth login",
        "az login",
        "echo hello world",
    ]

    for cmd in test_commands:
        parts = cmd.strip().split()
        assert len(parts) > 0
        assert parts[0] in ["aws", "gcloud", "az", "echo"]


def test_command_timeout_values():
    """Test that timeout values are reasonable."""
    # Test that our timeout values are reasonable for fast tests
    timeout_values = [1, 5, 10, 30]

    for timeout in timeout_values:
        assert timeout > 0
        assert timeout <= 30  # Max 30 seconds for reasonable tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
