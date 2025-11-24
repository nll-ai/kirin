# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "marimo",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.18.0"
app = marimo.App(width="medium")


@app.cell
def _():
    """Import detect_source_file."""
    from kirin.utils import detect_source_file
    return (detect_source_file,)


@app.cell
def _(detect_source_file):
    """Test source detection."""
    detected = detect_source_file()
    print(f"Detected source file: {detected}")
    return


if __name__ == "__main__":
    app.run()
