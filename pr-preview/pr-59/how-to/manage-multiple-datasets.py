# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "polars",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../../", editable = true }
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Manage Multiple Datasets

    This guide shows you how to organize and manage multiple datasets using
    Kirin's Catalog feature. You'll learn to create catalogs, organize
    datasets, and perform cross-dataset operations.
    """)
    return


@app.cell
def _():
    import tempfile
    from pathlib import Path

    import polars as pl

    from kirin import Catalog

    temp_dir = Path(tempfile.mkdtemp())
    catalog = Catalog(root_dir=temp_dir)

    print(f"✅ Catalog created at: {temp_dir}")
    return catalog, pl, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Create Datasets

    Create datasets within your catalog. Each dataset can have its own purpose,
    but they all share the same content-addressed storage for automatic
    deduplication.

    **Note:** Datasets don't appear in `catalog.datasets()` until after the
    first commit. This is because directories aren't created until they contain
    objects (for S3/GCS/Azure compatibility).
    """)
    return


@app.cell
def _(catalog):
    sales_ds = catalog.create_dataset(
        "sales_data",
        "Quarterly sales data with product information and revenue tracking",
    )

    customer_ds = catalog.create_dataset(
        "customer_data",
        "Customer profiles, demographics, and purchase history",
    )

    analytics_ds = catalog.create_dataset(
        "analytics",
        "Data analysis scripts, models, and derived insights",
    )

    print("✅ Created 3 dataset instances")
    print("   Note: They won't appear in catalog.datasets() until first commit")
    return analytics_ds, customer_ds, sales_ds


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prepare Sample Data

    Create sample data files for demonstration purposes.
    """)
    return


@app.cell
def _(temp_dir):
    sales_data_dir = temp_dir / "sales_data"
    sales_data_dir.mkdir(exist_ok=True)

    q1_sales = sales_data_dir / "q1_sales.csv"
    q1_sales.write_text("""product,price,quantity,revenue,date
    Widget A,29.99,100,2999.00,2024-01-15
    Widget B,19.99,150,2998.50,2024-01-16
    Widget C,39.99,75,2999.25,2024-01-17
    Widget A,29.99,120,3598.80,2024-01-18
    Widget B,19.99,200,3998.00,2024-01-19""")

    products = sales_data_dir / "products.json"
    products.write_text("""{
    "products": [
        {"id": "A", "name": "Widget A", "category": "Electronics", "cost": 15.00},
        {"id": "B", "name": "Widget B", "category": "Accessories", "cost": 8.00},
        {"id": "C", "name": "Widget C", "category": "Premium", "cost": 25.00}
    ]
    }""")

    customer_data_dir = temp_dir / "customer_data"
    customer_data_dir.mkdir(exist_ok=True)

    customers = customer_data_dir / "customers.csv"
    customers.write_text("""customer_id,name,email,age,segment,registration_date
    C001,Alice Johnson,alice@email.com,28,Premium,2023-06-15
    C002,Bob Smith,bob@email.com,35,Standard,2023-08-22
    C003,Carol Davis,carol@email.com,42,Premium,2023-04-10
    C004,David Wilson,david@email.com,31,Standard,2023-09-05
    C005,Eve Brown,eve@email.com,26,Premium,2023-07-18""")

    analytics_data_dir = temp_dir / "analytics"
    analytics_data_dir.mkdir(exist_ok=True)

    analysis_results = analytics_data_dir / "analysis_results.json"
    analysis_results.write_text("""{
    "analysis_date": "2024-01-20",
    "total_revenue": 12595.55,
    "top_product": "Widget B",
    "customer_segments": {
        "Premium": 3,
        "Standard": 2
    }
    }""")

    print("✅ Created sample data files")
    return analytics_data_dir, customer_data_dir, sales_data_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Commit Files to Datasets

    Commit files to each dataset. After the first commit, datasets will appear
    in `catalog.datasets()`.
    """)
    return


@app.cell
def _(sales_data_dir, sales_ds):
    sales_commit = sales_ds.commit(
        message="Initial commit: Add Q1 sales data and product catalog",
        add_files=[
            str(sales_data_dir / "q1_sales.csv"),
            str(sales_data_dir / "products.json"),
        ],
    )

    print(f"✅ Committed to sales_data: {sales_commit[:8]}")
    return


@app.cell
def _(customer_data_dir, customer_ds):
    customer_commit = customer_ds.commit(
        message="Initial commit: Add customer profiles",
        add_files=[
            str(customer_data_dir / "customers.csv"),
        ],
    )

    print(f"✅ Committed to customer_data: {customer_commit[:8]}")
    return


@app.cell
def _(analytics_data_dir, analytics_ds):
    analytics_commit = analytics_ds.commit(
        message="Initial commit: Add analysis results",
        add_files=[
            str(analytics_data_dir / "analysis_results.json"),
        ],
    )

    print(f"✅ Committed to analytics: {analytics_commit[:8]}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## List All Datasets

    Now that commits have been made, datasets appear in `catalog.datasets()`.
    Use this to discover and access all datasets in your catalog.
    """)
    return


@app.cell
def _(catalog, mo):
    dataset_info = []
    for listed_name in catalog.datasets():
        current_ds = catalog.get_dataset(listed_name)
        ds_info = current_ds.get_info()
        dataset_info.append(
            {
                "name": listed_name,
                "description": ds_info["description"],
                "files": len(current_ds.files),
                "commits": ds_info["commit_count"],
            }
        )

    info_content = f"**Total Datasets**: {len(catalog)}\n\n"
    info_content += "**Dataset Details:**\n\n"
    for info_item in dataset_info:
        info_content += f"- **{info_item['name']}**: {info_item['description']}\n"
        info_content += f"  - Files: {info_item['files']}\n"
        info_content += f"  - Commits: {info_item['commits']}\n"

    mo.md(info_content)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Access Dataset Files

    Access files from datasets using the dataset instances you created, or
    retrieve datasets from the catalog.
    """)
    return


@app.cell
def _(customer_ds, sales_ds):
    print("✅ Dataset files:")
    print(f"   - sales_data: {len(sales_ds.files)} files")
    print(f"   - customer_data: {len(customer_ds.files)} files")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Perform Cross-Dataset Analysis

    Access files from multiple datasets simultaneously to perform
    cross-dataset operations.
    """)
    return


@app.cell
def _(customer_ds, pl, sales_ds):
    with (
        sales_ds.local_files() as sales_files,
        customer_ds.local_files() as customer_files,
    ):
        sales_df = pl.read_csv(sales_files["q1_sales.csv"])
        customers_df = pl.read_csv(customer_files["customers.csv"])

        sales_summary = (
            sales_df.group_by("product")
            .agg(
                [
                    pl.col("quantity").sum().alias("total_quantity"),
                    pl.col("revenue").sum().alias("total_revenue"),
                ]
            )
            .sort("total_revenue", descending=True)
        )

        print("📊 Sales Summary by Product:")
        print(sales_summary)

        print("\n👥 Customer Statistics:")
        print(f"   Total customers: {customers_df.height}")
        premium_count = customers_df.filter(pl.col("segment") == "Premium").height
        print(f"   Premium customers: {premium_count}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Update Datasets

    Add new data to existing datasets by creating new commits. You can use
    `catalog.get_dataset()` to retrieve a dataset and commit to it.
    """)
    return


@app.cell
def _(catalog, temp_dir):
    q2_sales = temp_dir / "q2_sales.csv"
    q2_sales.write_text("""product,price,quantity,revenue,date
    Widget A,29.99,120,3598.80,2024-04-15
    Widget B,19.99,180,3598.20,2024-04-16
    Widget C,39.99,90,3599.10,2024-04-17
    Widget A,29.99,150,4498.50,2024-04-18
    Widget B,19.99,220,4397.80,2024-04-19""")

    sales_ds_update = catalog.get_dataset("sales_data")
    q2_commit = sales_ds_update.commit(
        message="Add Q2 sales data",
        add_files=[str(q2_sales)],
    )

    print(f"✅ Added Q2 data to sales_data: {q2_commit[:8]}")
    print(f"   Total commits in sales_data: {len(sales_ds_update.history())}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Iterate Over All Datasets

    Use `catalog.datasets()` to iterate over all datasets that have at least
    one commit and perform operations on each one.
    """)
    return


@app.cell
def _(catalog):
    print("📋 All Datasets Overview")
    print("=" * 40)

    for overview_name in catalog.datasets():
        iter_ds = catalog.get_dataset(overview_name)
        ds_files = iter_ds.list_files()
        ds_history = iter_ds.history(limit=1)

        print(f"\n📁 {overview_name}:")
        print(f"   Files: {', '.join(ds_files) if ds_files else 'None'}")
        if ds_history:
            latest_commit = ds_history[0]
            commit_msg = f"{latest_commit.short_hash} - {latest_commit.message}"
            print(f"   Latest commit: {commit_msg}")
        print(f"   Total commits: {len(iter_ds.history())}")
    return


@app.cell(hide_code=True)
def _(catalog, mo):
    summary_content = f"**Total Datasets**: {len(catalog)}\n\n"
    summary_content += f"**All Datasets**: {', '.join(catalog.datasets())}\n\n"
    summary_content += "**Key Benefits:**\n"
    summary_content += "- ✅ Centralized management of multiple datasets\n"
    summary_content += (
        "- ✅ Shared content-addressed storage (automatic deduplication)\n"
    )
    summary_content += "- ✅ Easy dataset discovery and listing\n"
    summary_content += "- ✅ Cross-dataset operations\n"
    summary_content += "- ✅ Cloud storage support (S3, GCS, Azure)\n"

    mo.md(summary_content)
    return


if __name__ == "__main__":
    app.run()
