---
name: kirin
description: >-
  Uses Kirin (Python library) for versioned, content-addressed datasets with
  linear commit history. Covers Catalog and Dataset APIs, commit/checkout,
  file reads, lazy local paths, and cloud roots via fsspec. Use when the user
  asks for data versioning like git, Dataset/Catalog usage, kirin commits,
  checking out a snapshot, or storing ML artifacts (sklearn models, plots)
  in Kirin.
---

# Kirin for coding agents

Kirin is **simplified git for data**: linear commits only, no branches, files
stored by **content hash** (deduplicated), any **`fsspec`-compatible** backend
(local paths, `s3://`, `gs://`, Azure, etc.).

Primary docs in-repo: `AGENTS.md` (project conventions), `docs/design.md`
(architecture).

## Imports

```python
from kirin import Catalog, Dataset, File, Commit
from kirin import get_s3_filesystem, get_gcs_filesystem  # optional helpers
```

Use **`loguru`** if the task adds logging in this repo (`from loguru import
logger`), not `logging`.

## Mental model

- **`Dataset`**: one named dataset; **linear** history; **`commit()`** snapshots
  files; **`checkout()`** moves the working view to a commit.
- **`Catalog`**: many datasets under one `root_dir` (convention:
  `{root}/datasets/{name}/...`).
- **`File`**: immutable metadata + bytes in **`ContentStore`**; read via
  `read_bytes()`, `read_text()`, `open()`, or `download_to()`.
- **New commits only from latest**: if checked out to an older commit,
  `commit()` raises. Call `dataset.checkout()` (no args) to return to latest,
  then commit.

## Catalog workflow

```python
catalog = Catalog(root_dir="/path/to/store")  # or s3://bucket/prefix, etc.
names = catalog.datasets()
ds = catalog.create_dataset("my_dataset", description="optional")
# or open existing:
ds = catalog.get_dataset("my_dataset")
```

Pass **`aws_profile`**, **`gcs_project`**, **`gcs_token`**, or Azure fields on
`Catalog` when the URL needs explicit auth (see `kirin/catalog.py`).

## Dataset: commit and checkout

```python
commit_hash = ds.commit(
    message="Add batch A",
    add_files=["/local/a.csv", "/local/b.parquet"],  # str or Path
    remove_files=["old_name.csv"],  # optional; filenames in the commit
    metadata={"run_id": "..."},    # optional dict
    tags=["staging"],              # optional list
)
```

Rules:

- At least one of **`add_files`** or **`remove_files`** is required.
- **`add_files`** may also include **scikit-learn estimator instances** or
  **matplotlib/plotly figure objects**; Kirin serializes them. Those objects
  **must be bound to a variable** so Kirin can infer a filename (otherwise
  `commit()` raises).

```python
ds.checkout()                    # latest
ds.checkout("abc123f")          # partial hash ok
```

**History** (newest first):

```python
commits: list[Commit] = ds.history(limit=10)
```

Each **`Commit`** has `hash`, `message`, `timestamp`, `parent_hash`, `files`
(dict of name → `File`), and helpers like `get_file`, `list_files`, `has_file`.

## Reading files from the current commit

From **`Dataset`** (uses current checkout):

```python
text = ds.read_file("report.csv")           # default text mode
blob = ds.read_file("model.bin", mode="rb")
fobj = ds.get_file("x.txt")               # File | None
if fobj:
    data = fobj.read_text()
```

**Lazy local paths** (download on first key access; cleaned up on exit):

```python
with ds.local_files() as paths:
    # paths behaves like dict[str, str]: filename -> local path
    p = paths["bigfile.zst"]   # triggers download
```

Iterating **keys** does not download. Empty commits yield `{}`.

## Direct `Dataset` (no catalog)

```python
ds = Dataset(root_dir="/data/root", name="ds_name", description="")
```

Same methods as above; storage layout still uses `datasets/{name}` under
`root_dir` for commit metadata.

## Content-addressed storage (for debugging paths)

Under `root_dir`, blobs live at:

`data/{hash[:2]}/{hash[2:]}/{filename}`

Filenames are visible in storage; identical content shares one hash directory.

## Pitfalls agents should avoid

- Do not assume **branching** or merges; history is **strictly linear**.
- After **`checkout(old_hash)`**, remember **`checkout()`** before new
  **`commit()`**.
- **`dataset.files`**: mapping for **current commit** only; empty if no commit.
- Prefer **same logical filenames across commits** for demos; version info
  belongs in **commit messages / metadata**, not `file_v2.csv` patterns.
- In this repo, run Python via **`pixi run python`** and tests via
  **`pixi run -e tests python -m pytest`**.

## When to read more

- **Web UI / FastAPI**: `kirin/web/` and `AGENTS.md` "Web UI" sections.
- **SSL in isolated envs**: `python -m kirin.setup_ssl` (see `AGENTS.md`).
- **CLI**: `pixi run python -m kirin.cli` if installed entrypoints apply.
