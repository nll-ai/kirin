# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.15",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
#     "marimo>=0.23.4",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Kirin Catalog Demo

    This notebook demonstrates how to use a **Catalog** to manage multiple datasets.

    We will:
    1. Create a local catalog
    2. Create multiple datasets
    3. Add dataset-specific files
    4. Commit snapshots per dataset
    5. Run a simple cross-dataset analysis
    6. Add a second round of updates
    """)
    return


@app.cell
def _():
    import tempfile
    from pathlib import Path

    import marimo as mo
    import polars as pl

    from kirin import Catalog

    return Catalog, Path, mo, pl, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Initialize a local catalog

    A catalog is the top-level manager for multiple datasets that share the same
    content-addressed storage root.
    """)
    return


@app.cell
def _(Catalog, Path, tempfile):
    temp_dir = Path(tempfile.mkdtemp())
    catalog = Catalog(root_dir=temp_dir)

    temp_dir
    return catalog, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Create datasets inside the catalog

    Each dataset has independent commit history, but all datasets live under the
    same catalog root.
    """)
    return


@app.cell
def _(catalog):
    sales_ds = catalog.create_dataset(
        "sales_data",
        "Quarterly sales data and product catalog",
    )
    sales_ds.name
    return (sales_ds,)


@app.cell
def _(catalog):
    customer_ds = catalog.create_dataset(
        "customer_data",
        "Customer profiles and purchase history",
    )
    customer_ds.name
    return (customer_ds,)


@app.cell
def _(catalog):
    analytics_ds = catalog.create_dataset(
        "analytics",
        "Analysis scripts and model configs",
    )
    analytics_ds.name
    return (analytics_ds,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Create sample files for each dataset

    We keep file creation split into small cells so each step is easy to follow.
    """)
    return


@app.cell
def _(temp_dir):
    sales_data_dir = temp_dir / "sales_data"
    analytics_data_dir = temp_dir / "analytics_data"
    customer_data_dir = temp_dir / "customer_data"

    sales_data_dir.mkdir(exist_ok=True)
    analytics_data_dir.mkdir(exist_ok=True)
    customer_data_dir.mkdir(exist_ok=True)
    return analytics_data_dir, customer_data_dir, sales_data_dir


@app.cell
def _(sales_data_dir):
    q1_sales = sales_data_dir / "q1_sales.csv"
    q1_sales.write_text("""product,price,quantity,revenue,date
    Widget A,29.99,100,2999.00,2024-01-15
    Widget B,19.99,150,2998.50,2024-01-16
    Widget C,39.99,75,2999.25,2024-01-17
    Widget A,29.99,120,3598.80,2024-01-18
    Widget B,19.99,200,3998.00,2024-01-19""")
    return (q1_sales,)


@app.cell
def _(sales_data_dir):
    products = sales_data_dir / "products.json"
    products.write_text("""{
      "products": [
        {"id": "A", "name": "Widget A", "category": "Electronics", "cost": 15.00},
        {"id": "B", "name": "Widget B", "category": "Accessories", "cost": 8.00},
        {"id": "C", "name": "Widget C", "category": "Premium", "cost": 25.00}
      ]
    }""")
    return (products,)


@app.cell
def _(analytics_data_dir):
    analysis_script = analytics_data_dir / "sales_analysis.py"
    analysis_script.write_text("""import polars as pl

    def analyze_quarterly_sales(df: pl.DataFrame) -> pl.DataFrame:
        return (
            df.group_by("product")
            .agg([
                pl.col("quantity").sum().alias("total_quantity"),
                pl.col("revenue").sum().alias("total_revenue"),
            ])
            .sort("total_revenue", descending=True)
        )
    """)
    return (analysis_script,)


@app.cell
def _(analytics_data_dir):
    model_config = analytics_data_dir / "model_config.yaml"
    model_config.write_text("""model:
      name: quarterly_sales_forecast
      type: time_series
    features:
      - product
      - price
      - quantity
      - revenue
    target: quantity
    """)
    return (model_config,)


@app.cell
def _(customer_data_dir):
    customers = customer_data_dir / "customers.csv"
    customers.write_text("""customer_id,name,email,age,segment,registration_date
    C001,Alice Johnson,alice@email.com,28,Premium,2023-06-15
    C002,Bob Smith,bob@email.com,35,Standard,2023-08-22
    C003,Carol Davis,carol@email.com,42,Premium,2023-04-10
    C004,David Wilson,david@email.com,31,Standard,2023-09-05
    C005,Eve Brown,eve@email.com,26,Premium,2023-07-18""")
    return (customers,)


@app.cell
def _(customer_data_dir):
    purchases = customer_data_dir / "purchases.json"
    purchases.write_text("""{
      "purchases": [
        {"customer_id": "C001", "product": "Widget A", "quantity": 2, "date": "2024-01-15"},
        {"customer_id": "C002", "product": "Widget B", "quantity": 3, "date": "2024-01-16"},
        {"customer_id": "C003", "product": "Widget C", "quantity": 1, "date": "2024-01-17"}
      ]
    }""")
    return (purchases,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Commit initial snapshots per dataset

    Each dataset gets its own commit history entry.
    """)
    return


@app.cell
def _(products, q1_sales, sales_ds):
    sales_commit = sales_ds.commit(
        message="Initial commit: Add Q1 sales data and product catalog",
        add_files=[q1_sales, products],
        skip_if_no_changes=True,
    )
    sales_commit
    return


@app.cell
def _(analysis_script, analytics_ds, model_config):
    analytics_commit = analytics_ds.commit(
        message="Initial commit: Add analysis script and model config",
        add_files=[analysis_script, model_config],
        skip_if_no_changes=True,
    )
    analytics_commit
    return


@app.cell
def _(customer_ds, customers, purchases):
    customer_commit = customer_ds.commit(
        message="Initial commit: Add customer profiles and purchase history",
        add_files=[customers, purchases],
        skip_if_no_changes=True,
    )
    customer_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Inspect catalog status

    We summarize dataset-level commit and file counts.
    """)
    return


@app.cell
def _(catalog, mo):
    status_lines = []
    for status_dataset_name in catalog.datasets():
        status_dataset = catalog.get_dataset(status_dataset_name)
        status_info = status_dataset.get_info()
        status_lines.append(
            f"- **{status_dataset_name}**: commits={status_info['commit_count']}, files={len(status_dataset.files)}"
        )

    mo.md("## Catalog Status\n\n" + "\n".join(status_lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6) Cross-dataset analysis

    Use local materialization to load files from multiple datasets at once.
    """)
    return


@app.cell
def _(customer_ds, pl, sales_ds):
    cross_analysis_results = None

    with sales_ds.local_files() as sales_files, customer_ds.local_files() as customer_files:
        sales_df = pl.read_csv(sales_files["q1_sales.csv"])
        customers_df = pl.read_csv(customer_files["customers.csv"])
        cross_analysis_results = {
            "sales_summary": (
                sales_df.group_by("product")
                .agg([
                    pl.col("quantity").sum().alias("total_quantity"),
                    pl.col("revenue").sum().alias("total_revenue"),
                ])
                .sort("total_revenue", descending=True)
            ),
            "customer_count": customers_df.height,
            "premium_customers": customers_df.filter(pl.col("segment") == "Premium").height,
        }
    return (cross_analysis_results,)


@app.cell
def _(cross_analysis_results, mo):
    mo.md(f"""
    ### Cross-dataset results

    - **Total customers**: {cross_analysis_results['customer_count']}
    - **Premium customers**: {cross_analysis_results['premium_customers']}

    Sales summary:
    ```
    {cross_analysis_results['sales_summary']}
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7) Add a second update round

    We add Q2 data and an additional analysis script, then commit updates.
    """)
    return


@app.cell
def _(temp_dir):
    q2_sales = temp_dir / "q2_sales.csv"
    q2_sales.write_text("""product,price,quantity,revenue,date
    Widget A,29.99,120,3598.80,2024-04-15
    Widget B,19.99,180,3598.20,2024-04-16
    Widget C,39.99,90,3599.10,2024-04-17
    Widget D,49.99,60,2999.40,2024-04-20""")
    return (q2_sales,)


@app.cell
def _(temp_dir):
    q2_analysis = temp_dir / "q2_analysis.py"
    q2_analysis.write_text("""import polars as pl

    def compare_quarters(q1_df: pl.DataFrame, q2_df: pl.DataFrame) -> pl.DataFrame:
        q1_summary = q1_df.group_by("product").agg(pl.col("revenue").sum().alias("q1_revenue"))
        q2_summary = q2_df.group_by("product").agg(pl.col("revenue").sum().alias("q2_revenue"))
        return q1_summary.join(q2_summary, on="product")
    """)
    return (q2_analysis,)


@app.cell
def _(analytics_ds, q2_analysis, q2_sales, sales_ds):
    sales_commit2 = sales_ds.commit(
        message="Add Q2 sales data",
        add_files=[q2_sales],
        skip_if_no_changes=True,
    )
    analytics_commit2 = analytics_ds.commit(
        message="Add Q2 analysis script",
        add_files=[q2_analysis],
        skip_if_no_changes=True,
    )
    (sales_commit2, analytics_commit2)
    return


@app.cell(hide_code=True)
def _(catalog, mo):
    updated_lines = []
    for updated_dataset_name in catalog.datasets():
        updated_dataset = catalog.get_dataset(updated_dataset_name)
        updated_history = updated_dataset.history(limit=2)
        if updated_history:
            updated_lines.append(
                f"- **{updated_dataset_name}** latest: `{updated_history[0].short_hash}` {updated_history[0].message}"
            )

    mo.md("## Updated Catalog Status\n\n" + "\n".join(updated_lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8) Remote catalog patterns (usage examples)

    Use the same API with cloud-backed roots.

    ```python
    from kirin import Catalog

    # Local
    local_catalog = Catalog(root_dir="/path/to/local/data")

    # GCS
    gcs_catalog = Catalog(root_dir="gs://my-bucket")

    # S3 (with profile)
    s3_catalog = Catalog(root_dir="s3://my-bucket", aws_profile="my-profile")
    ```

    These patterns are identical to local usage; only the root URI and auth differ.
    """)
    return


@app.cell
def _(sales_ds):
    sales_ds
    return


if __name__ == "__main__":
    app.run()
