# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.1",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
#     "matplotlib==3.10.7",
#     "numpy==2.3.5",
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
    return


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
    np.random.seed(42)
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
    return (fig,)


@app.cell
def _():
    import kirin
    return (kirin,)


@app.cell
def _(kirin):
    catalog = kirin.Catalog(root_dir="/tmp/analysis_plot/")
    dataset = catalog.get_dataset("plots")
    dataset
    return (dataset,)


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
def _():
    return


if __name__ == "__main__":
    app.run()
