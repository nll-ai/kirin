# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars",
#     "kirin",
#     "anthropic",
#     "loguru",
#     "matplotlib",
#     "numpy",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///
#

import marimo

__generated_with = "0.18.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import matplotlib.pyplot as plt
    return (plt,)


@app.cell
def _():
    import numpy as np
    return (np,)


@app.cell(hide_code=True)
def _(np, plt):
    # Generate correlated data with correlation ~0.75
    np.random.seed(49)  # Set random seed for reproducibility
    n_points = 100

    # Generate x values
    x = np.random.normal(0, 1, n_points)

    # Generate y values with desired correlation
    correlation = 0.75
    y = correlation * x + np.sqrt(1 - correlation**2) * np.random.normal(
        0, 1, n_points
    )

    # Create scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.7, color="steelblue")
    plt.xlabel("X values")
    plt.ylabel("Y values")
    plt.title(f"Scatter Plot with Correlation ≈ {correlation}")
    plt.grid(True, alpha=0.3)

    # Calculate and display actual correlation
    actual_corr = np.corrcoef(x, y)[0, 1]
    plt.text(
        0.05,
        0.95,
        f"Actual correlation: {actual_corr:.3f}",
        transform=plt.gca().transAxes,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    fig = plt.gcf()
    fig
    return fig, x, y


@app.cell
def _():
    import kirin
    return (kirin,)


@app.cell
def _(x, y):
    import polars as pl

    df = pl.DataFrame({'x': x, 'y': y})
    df.write_csv("./correlated_data.csv")
    df
    return df, pl


@app.cell
def _(kirin):
    catalog = kirin.Catalog(root_dir="/tmp/analysis_plot/")
    catalog
    return (catalog,)


@app.cell
def _(catalog):
    dataset = catalog.get_dataset("plots")
    dataset
    return (dataset,)


@app.cell
def _(dataset):
    dataset.commit(message="Commit of correlated data.", add_files=["./correlated_data.csv"])
    return


@app.cell
def _(dataset, fig):
    dataset.save_plot(
        fig,
        filename="correlated_scatter_plot.png",
        auto_commit=True,
        message="Add correlated scatter plot.",
    )
    return


@app.cell
def _(kirin):
    dataset_autodata = kirin.Dataset(
        root_dir="/tmp/analysis_plot/",
        name="auto-updating-data"
    )


    # Checkout to latest commit (HEAD)
    dataset_autodata.checkout()

    return (dataset_autodata,)


@app.cell
def _():
    from datetime import date
    return (date,)


@app.cell
def _(df, pl):
    # Add 5 more rows to the dataframe previously defined, overwrite correlated_data.csv
    # Assume df is defined previously (in a previous cell)
    last_row = df.tail(2)
    # Repeat last row 5 times
    new_rows = pl.concat([last_row] * 10)

    # Append new rows to df
    df2 = pl.concat([df, new_rows])

    # Overwrite CSV
    df2.write_csv("correlated_data.csv")

    return


@app.cell
def _(dataset_autodata, date):
    dataset_autodata.commit(message=f"Auto-updated file on {date.today()}", add_files=["./correlated_data.csv"], metadata={"operator": "Eric Name"})
    return


@app.cell
def _(dataset_autodata, pl):
    dataset_autodata.checkout("ace7ad2c950d72813d3")
    with dataset_autodata.local_files() as dataset_autodata_files:
        df3 = pl.read_csv(dataset_autodata_files["correlated_data.csv"])

    df3
    return


@app.cell
def _(kirin):
    dataset_gcp = kirin.Dataset(
        root_dir="gs://kirin-test-bucket",
        name="test-checkout"
    )


    # Checkout to latest commit (HEAD)
    dataset_gcp.checkout("16e52c01f893d3bd395d891f7dcb91ecaee5485ab03c23d308cee72f8b267a6b")
    dataset_gcp
    return (dataset_gcp,)


@app.cell
def _(dataset_gcp, mo):
    from pathlib import Path

    with dataset_gcp.local_files() as local_files:
        file_path = local_files["tmp55y4l46r.txt"]
        contents = Path(file_path).read_text()

    mo.md(contents)
    return


if __name__ == "__main__":
    app.run()
