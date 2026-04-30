# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.40.1",
#     "kirin==0.0.15",
#     "anthropic",
#     "loguru",
#     "matplotlib==3.10.9",
#     "numpy==2.4.4",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///
#

import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Kirin Version Plots Demo

    This notebook demonstrates a plotting + versioning workflow with Kirin.

    We will:
    1. generate correlated synthetic data
    2. create a scatter plot and CSV artifact
    3. commit both artifacts to a local dataset
    4. simulate an auto-update commit with idempotent guard
    5. create and version multiple plot artifacts
    """)
    return


@app.cell
def _():
    from datetime import date
    from pathlib import Path
    import tempfile

    import kirin
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import polars as pl

    return Path, date, kirin, mo, np, pl, plt, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Generate correlated synthetic data

    Create `x` and `y` values with target correlation around 0.75.
    """)
    return


@app.cell
def _(np):
    np.random.seed(49)
    n_points = 100
    correlation = 0.75

    x = np.random.normal(0, 1, n_points)
    y = correlation * x + np.sqrt(1 - correlation**2) * np.random.normal(0, 1, n_points)
    actual_corr = float(np.corrcoef(x, y)[0, 1])

    actual_corr
    return actual_corr, correlation, x, y


@app.cell
def _(actual_corr, correlation, plt, x, y):
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.7, color="steelblue")
    plt.xlabel("X values")
    plt.ylabel("Y values")
    plt.title(f"Scatter Plot with Correlation ≈ {correlation}")
    plt.grid(True, alpha=0.3)
    plt.text(
        0.05,
        0.95,
        f"Actual correlation: {actual_corr:.3f}",
        transform=plt.gca().transAxes,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    fig = plt.gcf()
    fig
    return (fig,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Persist data artifact to CSV

    Write the generated data to `correlated_data.csv` for versioning.
    """)
    return


@app.cell
def _(Path, pl, x, y):
    df = pl.DataFrame({"x": x, "y": y})
    csv_path = Path("./correlated_data.csv")
    df.write_csv(csv_path)

    df
    return csv_path, df


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Commit CSV and plot to local Kirin dataset

    Both commits opt in to `skip_if_no_changes=True` so reruns avoid duplicate
    no-op commits in a reactive notebook.
    """)
    return


@app.cell
def _(Path, kirin, tempfile):
    analysis_root = Path(tempfile.mkdtemp(prefix="kirin_analysis_plot_"))
    catalog = kirin.Catalog(root_dir=str(analysis_root))
    dataset = catalog.get_dataset("plots")

    dataset
    return analysis_root, dataset


@app.cell
def _(csv_path, dataset):
    commit_csv_hash = dataset.commit(
        message="Commit of correlated data.",
        add_files=[str(csv_path)],
        skip_if_no_changes=True,
    )

    commit_csv_hash
    return


@app.cell
def _(dataset, fig):
    commit_plot_hash = dataset.commit(
        message="Add correlated scatter plot.",
        add_files=[fig],
        skip_if_no_changes=True,
    )

    commit_plot_hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we should see three commits.
    """)
    return


@app.cell
def _(dataset):
    dataset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Simulate an auto-updating dataset commit

    Append repeated tail rows, overwrite the CSV, and commit with metadata.
    """)
    return


@app.cell
def _(analysis_root, kirin):
    dataset_autodata = kirin.Dataset(
        root_dir=str(analysis_root),
        name="auto-updating-data",
    )

    if dataset_autodata.history(limit=1):
        dataset_autodata.checkout()

    dataset_autodata
    return (dataset_autodata,)


@app.cell
def _(csv_path, df, pl):
    last_rows = df.tail(2)
    new_rows = pl.concat([last_rows] * 10)
    df2 = pl.concat([df, new_rows])
    df2.write_csv(csv_path)

    df2.tail()
    return


@app.cell
def _(csv_path, dataset_autodata, date):
    autocommit_hash = dataset_autodata.commit(
        message=f"Auto-updated file on {date.today()}",
        add_files=[str(csv_path)],
        metadata={"operator": "Eric Name"},
        skip_if_no_changes=True,
    )

    autocommit_hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Checkout a prior local commit and read file contents
    """)
    return


@app.cell
def _(dataset_autodata, pl):
    autodata_history = dataset_autodata.history(limit=5)
    target_commit_hash = autodata_history[-1].hash if autodata_history else None

    if target_commit_hash is not None:
        dataset_autodata.checkout(target_commit_hash)
        with dataset_autodata.local_files() as autodata_local_files:
            df3 = pl.read_csv(autodata_local_files["correlated_data.csv"])
    else:
        df3 = pl.DataFrame()

    df3
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6) Showcase plot storage and versioning

    Create a second plot variant, commit it, and compare plot-related commits.
    This demonstrates Kirin storing plot artifacts as versioned files.
    """)
    return


@app.cell(hide_code=True)
def _(np, plt, x, y):
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.6, color="darkorange", label="observations")
    coeffs = np.polyfit(x, y, 1)
    trend = np.poly1d(coeffs)
    sorted_indices = np.argsort(x)
    plt.plot(x[sorted_indices], trend(x[sorted_indices]), color="black", linewidth=2, label="trendline")
    plt.xlabel("X values")
    plt.ylabel("Y values")
    plt.title("Scatter Plot v2 with Trendline")
    plt.grid(True, alpha=0.3)
    plt.legend()

    fig_v2 = plt.gcf()
    fig_v2
    return (fig_v2,)


@app.cell
def _(dataset, fig_v2):
    commit_plot_v2_hash = dataset.commit(
        message="Add correlated scatter plot v2 with trendline.",
        add_files=[fig_v2],
        skip_if_no_changes=True,
    )

    commit_plot_v2_hash
    return


@app.cell(hide_code=True)
def _(dataset, mo):
    plot_commits = [
        commit
        for commit in dataset.history(limit=20)
        if "plot" in commit.message.lower()
    ]

    current_commit_hash = dataset.current_commit.hash if dataset.current_commit else None
    comparison_lines = []

    for plot_commit in plot_commits:
        dataset.checkout(plot_commit.hash)
        commit_files = dataset.list_files()
        svg_files = sorted([name for name in commit_files if name.endswith(".svg")])
        comparison_lines.append(
            f"- `{plot_commit.short_hash}`: {plot_commit.message} (svg files: {', '.join(svg_files) if svg_files else 'none'})"
        )

    if current_commit_hash is not None:
        dataset.checkout(current_commit_hash)

    rendered_plot_summary = mo.md(
        "### Plot commit history\n\n" + "\n".join(comparison_lines)
    )

    rendered_plot_summary
    return


@app.cell
def _(dataset):
    dataset
    return


if __name__ == "__main__":
    app.run()
