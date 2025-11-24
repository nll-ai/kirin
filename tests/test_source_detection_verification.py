"""Verification test to ensure source detection actually works."""

import os
import subprocess
import tempfile
from pathlib import Path


def test_detect_source_file_actually_works():
    """Test that detect_source_file() actually detects the calling script."""
    # Create a temporary script that calls detect_source_file and writes result
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        script_path = f.name
        f.write("""import sys
from pathlib import Path

# Add parent directory to path to import kirin
sys.path.insert(0, str(Path(__file__).parent.parent))

from kirin.utils import detect_source_file

# Detect source file
detected = detect_source_file()

# Write result to output file
output_file = Path(__file__).parent / "detection_result.txt"
with open(output_file, "w") as out:
    if detected:
        out.write(f"SUCCESS:{detected}")
    else:
        out.write("FAILED:None")
""")

    try:
        # Run the script
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(script_path),
        )

        # Check the output file
        output_file = Path(os.path.dirname(script_path)) / "detection_result.txt"
        if output_file.exists():
            with open(output_file) as f:
                content = f.read().strip()

            if content.startswith("SUCCESS:"):
                detected_path = content.split(":", 1)[1]
                print(f"\n✅ Source detection WORKED! Detected: {detected_path}")
                assert detected_path == script_path, (
                    f"Expected {script_path}, got {detected_path}"
                )
                # Clean up
                output_file.unlink()
            else:
                print(f"\n❌ Source detection FAILED: {content}")
                assert False, f"Source detection failed: {content}"
        else:
            print(f"\n❌ Output file not created. Script output: {result.stdout}")
            print(f"Script error: {result.stderr}")
            assert False, "Output file was not created"

    finally:
        # Clean up
        if os.path.exists(script_path):
            os.unlink(script_path)
        output_file = Path(os.path.dirname(script_path)) / "detection_result.txt"
        if output_file.exists():
            output_file.unlink()
