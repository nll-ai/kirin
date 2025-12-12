"""Convert Marimo notebooks to Markdown with Molab shield injection."""

import subprocess
from pathlib import Path


def convert_marimo_to_markdown():
    """Convert all Marimo notebooks in docs/how-to/ and docs/tutorials/ to Markdown.

    This script:
    - Finds all .py files in docs/how-to/ and docs/tutorials/
    - Converts them to .md using marimo export (via uvx)
    - Injects Molab shield badge at the top
    - Preserves any existing frontmatter
    """
    # Process both how-to and tutorials directories
    directories = [
        Path("docs/how-to"),
        Path("docs/tutorials"),
    ]

    for directory in directories:
        if not directory.exists():
            print(f"Directory {directory} does not exist. Skipping conversion.")
            continue

        for notebook in directory.glob("*.py"):
            if notebook.stem.startswith("_"):
                continue  # Skip private files

            md_file = notebook.with_suffix(".md")
            print(f"Converting {notebook.name} to {md_file.name}...")

            try:
                # Run marimo export using uvx (no need to install marimo separately)
                subprocess.run(
                    [
                        "uvx",
                        "marimo",
                        "export",
                        "md",
                        str(notebook),
                        "--output",
                        str(md_file),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Read generated markdown
                content = md_file.read_text()

                # Check if Molab shield and command already exist
                if (
                    "[![Open in molab]" in content
                    and "uvx marimo edit --sandbox --mcp --no-token --watch" in content
                ):
                    print(
                        f"  Molab shield and command already exist in {md_file.name}, skipping injection."
                    )
                    continue

                # Generate Molab link (use relative path from repo root)
                # notebook is in docs/how-to/ or docs/tutorials/, so relative to repo root
                repo_path = str(notebook).replace("\\", "/")  # Normalize path separators
                molab_shield = (
                    f"[![Open in molab](https://marimo.io/molab-shield.svg)]"
                    f"(https://molab.marimo.io/github/nll-ai/kirin/blob/main/{repo_path})"
                )

                # Generate command for local execution
                github_url = f"https://github.com/nll-ai/kirin/blob/main/{repo_path}"
                command = f"uvx marimo edit --sandbox --mcp --no-token --watch {github_url}"

                # Create instruction text with shield and command
                instruction_text = (
                    f"{molab_shield}\n\n"
                    f"To run this notebook, click on the molab shield above or run the following command at the terminal:\n\n"
                    f"```bash\n{command}\n```\n\n"
                )

                # Prepend shield (preserve frontmatter if present)
                if content.startswith("---"):
                    # Has frontmatter - find where it ends (second ---)
                    frontmatter_end = content.find("---", 3)
                    if frontmatter_end != -1:
                        # Insert shield after frontmatter (after the closing --- and newline)
                        frontmatter_end += 3
                        # Skip any whitespace/newlines after frontmatter
                        while (
                            frontmatter_end < len(content)
                            and content[frontmatter_end] in "\n\r"
                        ):
                            frontmatter_end += 1
                        content = (
                            content[:frontmatter_end]
                            + instruction_text
                            + content[frontmatter_end:]
                        )
                    else:
                        # Malformed frontmatter, just prepend
                        content = instruction_text + content
                else:
                    # No frontmatter, just prepend
                    content = instruction_text + content

                # Ensure file ends with a single newline
                if not content.endswith("\n"):
                    content += "\n"
                elif content.endswith("\n\n"):
                    # Remove extra newlines, keep only one
                    content = content.rstrip("\n") + "\n"

                md_file.write_text(content)
                print(f"  Successfully converted {notebook.name}")

            except subprocess.CalledProcessError as e:
                print(f"  Error converting {notebook.name}: {e}")
                print(f"  stdout: {e.stdout}")
                print(f"  stderr: {e.stderr}")
            except Exception as e:
                print(f"  Unexpected error converting {notebook.name}: {e}")


if __name__ == "__main__":
    convert_marimo_to_markdown()
