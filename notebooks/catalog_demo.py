# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.1",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    # Kirin Catalog Demo - Managing Multiple Datasets with Content-Addressed Storage
    import marimo as mo
    import polars as pl
    from pathlib import Path
    import tempfile
    from kirin import Dataset, File, Commit, Catalog
    return Catalog, Path, mo, pl, tempfile


@app.cell
def _(Catalog, Path, tempfile):
    # Create a catalog to manage multiple datasets
    # Initialize catalog with local storage
    temp_dir = Path(tempfile.mkdtemp())
    catalog = Catalog(root_dir=temp_dir)
    return catalog, temp_dir


@app.cell
def _(mo):
    str_catalog_intro = ""
    str_catalog_intro += "**Kirin Catalog - Multi-Dataset Management:**\n\n"
    str_catalog_intro += "## 📚 **What is a Catalog?**\n"
    str_catalog_intro += (
        "A **Catalog** is a collection of **Datasets** that provides:\n"
    )
    str_catalog_intro += (
        "- **Centralized Management**: Organize multiple datasets in one place\n"
    )
    str_catalog_intro += (
        "- **Dataset Discovery**: List and explore all available datasets\n"
    )
    str_catalog_intro += "- **Unified Storage**: All datasets share the same content-addressed storage\n"
    str_catalog_intro += "- **Cross-Dataset Operations**: Work with multiple datasets efficiently\n\n"
    str_catalog_intro += "## 🏗️ **Catalog Architecture**\n"
    str_catalog_intro += "```\n"
    str_catalog_intro += "Catalog Root Directory\n"
    str_catalog_intro += "├── data/  # Shared content-addressed storage\n"
    str_catalog_intro += "│   ├── ab/  # hash[:2]\n"
    str_catalog_intro += "│   │   └── cdef1234...  # hash[2:]\n"
    str_catalog_intro += "│   └── ef/\n"
    str_catalog_intro += "│       └── 567890ab...\n"
    str_catalog_intro += "└── datasets/  # Individual dataset directories\n"
    str_catalog_intro += "    ├── sales_data/\n"
    str_catalog_intro += "    │   └── commits.json\n"
    str_catalog_intro += "    ├── customer_data/\n"
    str_catalog_intro += "    │   └── commits.json\n"
    str_catalog_intro += "    └── analytics/\n"
    str_catalog_intro += "        └── commits.json\n"
    str_catalog_intro += "```\n"

    mo.md(str_catalog_intro)
    return


@app.cell
def _(catalog):
    # Create multiple datasets in the catalog
    # Dataset 1: Sales Data
    sales_ds = catalog.create_dataset(
        "sales_data",
        "Quarterly sales data with product information and revenue tracking",
    )

    # Dataset 2: Customer Data
    customer_ds = catalog.create_dataset(
        "customer_data", "Customer profiles, demographics, and purchase history"
    )

    # Dataset 3: Analytics
    analytics_ds = catalog.create_dataset(
        "analytics", "Data analysis scripts, models, and derived insights"
    )
    return analytics_ds, customer_ds, sales_ds


@app.cell
def _(catalog, mo):
    str_catalog_info = ""
    str_catalog_info += "**Catalog Information:**\n"
    str_catalog_info += f"- **Total Datasets**: {len(catalog)}\n"
    str_catalog_info += f"- **Dataset Names**: {', '.join(catalog.datasets())}\n"
    str_catalog_info += f"- **Root Directory**: {catalog.root_dir}\n"

    mo.md(str_catalog_info)
    return


@app.cell
def _(temp_dir):
    # Create sample data for sales dataset
    sales_data_dir = temp_dir / "sales_data"
    sales_data_dir.mkdir(exist_ok=True)

    # Create quarterly sales data
    q1_sales = sales_data_dir / "q1_sales.csv"
    q1_sales.write_text("""product,price,quantity,revenue,date
    Widget A,29.99,100,2999.00,2024-01-15
    Widget B,19.99,150,2998.50,2024-01-16
    Widget C,39.99,75,2999.25,2024-01-17
    Widget A,29.99,120,3598.80,2024-01-18
    Widget B,19.99,200,3998.00,2024-01-19""")

    # Create product catalog
    products = sales_data_dir / "products.json"
    products.write_text("""{
    "products": [
        {"id": "A", "name": "Widget A", "category": "Electronics", "cost": 15.00},
        {"id": "B", "name": "Widget B", "category": "Accessories", "cost": 8.00},
        {"id": "C", "name": "Widget C", "category": "Premium", "cost": 25.00}
    ]
    }""")
    return (sales_data_dir,)


@app.cell
def _(temp_dir):
    # Create sample data for analytics dataset
    analytics_data_dir = temp_dir / "analytics_data"
    analytics_data_dir.mkdir(exist_ok=True)

    # Create analysis script
    analysis_script = analytics_data_dir / "sales_analysis.py"
    analysis_script.write_text("""# Sales Analysis Script
    import polars as pl

    def analyze_quarterly_sales(df):
    \"\"\"Analyze quarterly sales data and return insights.\"\"\"
    return df.group_by("product").agg([
        pl.col("quantity").sum().alias("total_quantity"),
        pl.col("revenue").sum().alias("total_revenue"),
        pl.col("price").first().alias("avg_price"),
        (pl.col("revenue") / pl.col("quantity")).mean().alias("avg_unit_price")
    ]).sort("total_revenue", descending=True)

    def calculate_margins(df, products):
    \"\"\"Calculate profit margins using product cost data.\"\"\"
    return df.join(products, left_on="product", right_on="id").with_columns([
        (pl.col("revenue") - (pl.col("quantity") * pl.col("cost"))).alias("profit"),
        ((pl.col("revenue") - (pl.col("quantity") * pl.col("cost"))) / pl.col("revenue") * 100).alias("margin_pct")
    ])

    if __name__ == "__main__":
    # Load and analyze data
    df = pl.read_csv("q1_sales.csv")
    products = pl.read_json("products.json").unnest("products")

    summary = analyze_quarterly_sales(df)
    margins = calculate_margins(df, products)

    print("Sales Summary:")
    print(summary)
    print("\\nProfit Margins:")
    print(margins)
    """)

    # Create model configuration
    model_config = analytics_data_dir / "model_config.yaml"
    model_config.write_text("""# Sales Forecasting Model Configuration
    model:
      name: "quarterly_sales_forecast"
      type: "time_series"
      parameters:
    window_size: 12
    seasonality: true
    trend: "additive"

    features:
      - "product"
      - "price"
      - "quantity"
      - "revenue"

    target: "quantity"

    preprocessing:
      - "normalize_prices"
      - "encode_products"
      - "create_lags"
    """)
    return (analytics_data_dir,)


@app.cell
def _(temp_dir):
    # Create sample data for customer dataset
    customer_data_dir = temp_dir / "customer_data"
    customer_data_dir.mkdir(exist_ok=True)

    # Create customer profiles
    customers = customer_data_dir / "customers.csv"
    customers.write_text("""customer_id,name,email,age,segment,registration_date
    C001,Alice Johnson,alice@email.com,28,Premium,2023-06-15
    C002,Bob Smith,bob@email.com,35,Standard,2023-08-22
    C003,Carol Davis,carol@email.com,42,Premium,2023-04-10
    C004,David Wilson,david@email.com,31,Standard,2023-09-05
    C005,Eve Brown,eve@email.com,26,Premium,2023-07-18""")

    # Create purchase history
    purchases = customer_data_dir / "purchases.json"
    purchases.write_text("""{
    "purchases": [
        {"customer_id": "C001", "product": "Widget A", "quantity": 2, "date": "2024-01-15"},
        {"customer_id": "C001", "product": "Widget C", "quantity": 1, "date": "2024-01-20"},
        {"customer_id": "C002", "product": "Widget B", "quantity": 3, "date": "2024-01-16"},
        {"customer_id": "C003", "product": "Widget A", "quantity": 1, "date": "2024-01-17"},
        {"customer_id": "C003", "product": "Widget B", "quantity": 2, "date": "2024-01-18"},
        {"customer_id": "C004", "product": "Widget B", "quantity": 1, "date": "2024-01-19"},
        {"customer_id": "C005", "product": "Widget C", "quantity": 2, "date": "2024-01-20"}
    ]
    }""")
    return (customer_data_dir,)


@app.cell
def _(analytics_data_dir, analytics_ds, sales_data_dir, sales_ds):
    # Commit data to datasets
    # Commit sales data
    sales_commit = sales_ds.commit(
        message="Initial commit: Add Q1 sales data and product catalog",
        add_files=[
            sales_data_dir / "q1_sales.csv",
            sales_data_dir / "products.json",
        ],
    )

    # Commit analytics data
    analytics_commit = analytics_ds.commit(
        message="Add sales analysis script and model configuration",
        add_files=[
            analytics_data_dir / "sales_analysis.py",
            analytics_data_dir / "model_config.yaml",
        ],
    )
    return


@app.cell
def _(customer_data_dir, customer_ds):
    # Commit customer data
    customer_commit = customer_ds.commit(
        message="Initial commit: Add customer profiles and purchase history",
        add_files=[
            customer_data_dir / "customers.csv",
            customer_data_dir / "purchases.json",
        ],
    )
    return


@app.cell
def _(catalog, mo):
    str_datasets_overview = ""
    str_datasets_overview += "**Catalog Datasets Overview:**\n\n"

    for dataset_name in catalog.datasets():
        dataset = catalog.get_dataset(dataset_name)
        info = dataset.get_info()
        str_datasets_overview += f"## 📊 **{dataset_name}**\n"
        str_datasets_overview += f"- **Description**: {info['description']}\n"
        str_datasets_overview += f"- **Files**: {len(dataset.files)}\n"
        str_datasets_overview += f"- **Commits**: {info['commit_count']}\n"
        str_datasets_overview += f"- **Current Commit**: {info['current_commit'][:8] if info['current_commit'] else 'None'}\n\n"

    mo.md(str_datasets_overview)
    return


@app.cell
def _(catalog, pl):
    # Demonstrate cross-dataset analysis
    # Access files from multiple datasets
    sales_ds_analysis = catalog.get_dataset("sales_data")
    customer_ds_analysis = catalog.get_dataset("customer_data")
    analytics_ds_analysis = catalog.get_dataset("analytics")

    # Perform cross-dataset analysis
    cross_analysis_results = None

    with (
        sales_ds_analysis.local_files() as sales_files,
        customer_ds_analysis.local_files() as customer_files,
    ):
        if "q1_sales.csv" in sales_files and "customers.csv" in customer_files:
            # Load sales data
            sales_df = pl.read_csv(sales_files["q1_sales.csv"])

            # Load customer data
            customers_df = pl.read_csv(customer_files["customers.csv"])

            # Perform cross-dataset analysis
            cross_analysis_results = {
                "sales_summary": sales_df.group_by("product")
                .agg(
                    [
                        pl.col("quantity").sum().alias("total_quantity"),
                        pl.col("revenue").sum().alias("total_revenue"),
                    ]
                )
                .sort("total_revenue", descending=True),
                "customer_count": customers_df.height,
                "premium_customers": customers_df.filter(
                    pl.col("segment") == "Premium"
                ).height,
            }
    return (cross_analysis_results,)


@app.cell
def _(cross_analysis_results, mo):
    str_cross_analysis = ""
    str_cross_analysis += "**Cross-Dataset Analysis Results:**\n\n"

    if cross_analysis_results:
        str_cross_analysis += "**Sales Summary by Product:**\n"
        str_cross_analysis += (
            f"```\n{cross_analysis_results['sales_summary']}\n```\n\n"
        )
        str_cross_analysis += f"**Customer Statistics:**\n"
        str_cross_analysis += (
            f"- **Total Customers**: {cross_analysis_results['customer_count']}\n"
        )
        str_cross_analysis += f"- **Premium Customers**: {cross_analysis_results['premium_customers']}\n"
    else:
        str_cross_analysis += "No cross-dataset analysis results available\n"

    mo.md(str_cross_analysis)
    return


@app.cell
def _(catalog, mo):
    # Demonstrate dataset operations
    str_dataset_operations = ""
    str_dataset_operations += "**Dataset Operations:**\n\n"

    # Show how to work with individual datasets
    for dataset_name_ops in catalog.datasets():
        dataset_ops = catalog.get_dataset(dataset_name_ops)
        files_ops = dataset_ops.list_files()
        history_ops = dataset_ops.history(limit=3)

        str_dataset_operations += f"## 📁 **{dataset_name_ops}**\n"
        str_dataset_operations += f"- **Files**: {', '.join(files_ops)}\n"
        str_dataset_operations += f"- **Recent Commits**: {len(history_ops)}\n"

        if history_ops:
            latest_commit_ops = history_ops[0]
            str_dataset_operations += f"- **Latest**: {latest_commit_ops.short_hash} - {latest_commit_ops.message}\n"

        str_dataset_operations += "\n"

    mo.md(str_dataset_operations)
    return


@app.cell
def _(analytics_ds, sales_ds, temp_dir):
    # Demonstrate adding new data to existing datasets
    # Add Q2 sales data to sales dataset
    q2_sales = temp_dir / "q2_sales.csv"
    q2_sales.write_text("""product,price,quantity,revenue,date
    Widget A,29.99,120,3598.80,2024-04-15
    Widget B,19.99,180,3598.20,2024-04-16
    Widget C,39.99,90,3599.10,2024-04-17
    Widget A,29.99,150,4498.50,2024-04-18
    Widget B,19.99,220,4397.80,2024-04-19
    Widget D,49.99,60,2999.40,2024-04-20""")

    # Add new analysis to analytics dataset
    q2_analysis = temp_dir / "q2_analysis.py"
    q2_analysis.write_text("""# Q2 Sales Analysis
    import polars as pl

    def compare_quarters(q1_df, q2_df):
    \"\"\"Compare Q1 and Q2 sales performance.\"\"\"
    q1_summary = q1_df.group_by("product").agg([
        pl.col("quantity").sum().alias("q1_quantity"),
        pl.col("revenue").sum().alias("q1_revenue")
    ])

    q2_summary = q2_df.group_by("product").agg([
        pl.col("quantity").sum().alias("q2_quantity"),
        pl.col("revenue").sum().alias("q2_revenue")
    ])

    comparison = q1_summary.join(q2_summary, on="product").with_columns([
        (pl.col("q2_quantity") - pl.col("q1_quantity")).alias("quantity_change"),
        (pl.col("q2_revenue") - pl.col("q1_revenue")).alias("revenue_change"),
        ((pl.col("q2_revenue") - pl.col("q1_revenue")) / pl.col("q1_revenue") * 100).alias("revenue_growth_pct")
    ])

    return comparison.sort("revenue_growth_pct", descending=True)

    if __name__ == "__main__":
    q1_df = pl.read_csv("q1_sales.csv")
    q2_df = pl.read_csv("q2_sales.csv")

    comparison = compare_quarters(q1_df, q2_df)
    print("Quarter-over-Quarter Comparison:")
    print(comparison)
    """)

    # Commit new data to both datasets
    sales_commit2 = sales_ds.commit(
        message="Add Q2 sales data with new product Widget D", add_files=[q2_sales]
    )

    analytics_commit2 = analytics_ds.commit(
        message="Add Q2 analysis script for quarter-over-quarter comparison",
        add_files=[q2_analysis],
    )
    return


@app.cell
def _(catalog, mo):
    str_updated_catalog = ""
    str_updated_catalog += "**Updated Catalog Status:**\n\n"

    for dataset_name_status in catalog.datasets():
        dataset_status = catalog.get_dataset(dataset_name_status)
        info_status = dataset_status.get_info()
        history_status = dataset_status.history(limit=2)

        str_updated_catalog += f"## 📊 **{dataset_name_status}**\n"
        str_updated_catalog += (
            f"- **Total Commits**: {info_status['commit_count']}\n"
        )
        str_updated_catalog += f"- **Files**: {len(dataset_status.files)}\n"

        if len(history_status) >= 2:
            str_updated_catalog += f"- **Latest**: {history_status[0].short_hash} - {history_status[0].message}\n"
            str_updated_catalog += f"- **Previous**: {history_status[1].short_hash} - {history_status[1].message}\n"

        str_updated_catalog += "\n"

    mo.md(str_updated_catalog)
    return


@app.cell
def _(mo):
    str_catalog_benefits = ""
    str_catalog_benefits += "**Kirin Catalog Benefits:**\n\n"
    str_catalog_benefits += "## 🏗️ **Organized Data Management**\n"
    str_catalog_benefits += (
        "- **Multiple Datasets**: Manage related datasets in one catalog\n"
    )
    str_catalog_benefits += (
        "- **Shared Storage**: Content-addressed storage across all datasets\n"
    )
    str_catalog_benefits += (
        "- **Deduplication**: Identical files shared between datasets\n"
    )
    str_catalog_benefits += (
        "- **Version Control**: Linear commit history for each dataset\n\n"
    )
    str_catalog_benefits += "## 🔄 **Cross-Dataset Operations**\n"
    str_catalog_benefits += "```python\n"
    str_catalog_benefits += "# Create catalog\n"
    str_catalog_benefits += 'catalog = Catalog(root_dir="/path/to/data")\n\n'
    str_catalog_benefits += "# Create datasets\n"
    str_catalog_benefits += (
        'sales_ds = catalog.create_dataset("sales", "Sales data")\n'
    )
    str_catalog_benefits += 'analytics_ds = catalog.create_dataset("analytics", "Analysis scripts")\n\n'
    str_catalog_benefits += "# Cross-dataset analysis\n"
    str_catalog_benefits += "with sales_ds.local_files() as sales_files, \\\n"
    str_catalog_benefits += "     analytics_ds.local_files() as analysis_files:\n"
    str_catalog_benefits += "    # Process data from multiple datasets\n"
    str_catalog_benefits += '    df = pl.read_csv(sales_files["data.csv"])\n'
    str_catalog_benefits += '    script = analysis_files["analysis.py"]\n'
    str_catalog_benefits += "```\n\n"
    str_catalog_benefits += "## 📊 **Perfect for Data Science Workflows**\n"
    str_catalog_benefits += "- **Related Datasets**: Keep sales, customer, and analytics data together\n"
    str_catalog_benefits += (
        "- **Shared Resources**: Common files (configs, scripts) across datasets\n"
    )
    str_catalog_benefits += (
        "- **Incremental Updates**: Add new data to existing datasets\n"
    )
    str_catalog_benefits += (
        "- **Version Tracking**: Track changes across all datasets\n"
    )
    str_catalog_benefits += "- **Collaborative Work**: Multiple team members can work on different datasets\n"

    mo.md(str_catalog_benefits)
    return


@app.cell
def _(mo):
    str_architecture_diagram = ""
    str_architecture_diagram += "**Kirin Catalog Architecture:**\n\n"
    str_architecture_diagram += "```\n"
    str_architecture_diagram += "Catalog Root Directory\n"
    str_architecture_diagram += "├── data/  # Shared content-addressed storage\n"
    str_architecture_diagram += "│   ├── ab/  # hash[:2]\n"
    str_architecture_diagram += "│   │   ├── cdef1234...  # sales_data.csv\n"
    str_architecture_diagram += "│   │   └── 567890ab...  # customers.csv\n"
    str_architecture_diagram += "│   └── ef/\n"
    str_architecture_diagram += "│       ├── 12345678...  # analysis.py\n"
    str_architecture_diagram += "│       └── 9abcdef0...  # model_config.yaml\n"
    str_architecture_diagram += "└── datasets/  # Individual dataset metadata\n"
    str_architecture_diagram += "    ├── sales_data/\n"
    str_architecture_diagram += (
        "    │   └── commits.json  # Linear commit history\n"
    )
    str_architecture_diagram += "    ├── customer_data/\n"
    str_architecture_diagram += "    │   └── commits.json\n"
    str_architecture_diagram += "    └── analytics/\n"
    str_architecture_diagram += "        └── commits.json\n"
    str_architecture_diagram += "```\n\n"
    str_architecture_diagram += "**Key Benefits:**\n"
    str_architecture_diagram += (
        "- **Shared Storage**: Files with identical content are stored once\n"
    )
    str_architecture_diagram += (
        "- **Independent History**: Each dataset has its own commit history\n"
    )
    str_architecture_diagram += (
        "- **Cross-Dataset Access**: Files can be accessed from any dataset\n"
    )
    str_architecture_diagram += (
        "- **Efficient Storage**: Deduplication saves space across datasets\n"
    )

    mo.md(str_architecture_diagram)
    return


@app.cell
def _(mo):
    str_use_cases = ""
    str_use_cases += "**Common Catalog Use Cases:**\n\n"
    str_use_cases += "## 🏢 **Enterprise Data Management**\n"
    str_use_cases += "- **Department Datasets**: Sales, Marketing, Finance datasets in one catalog\n"
    str_use_cases += "- **Shared Resources**: Common configuration files, schemas, and scripts\n"
    str_use_cases += "- **Cross-Department Analysis**: Combine data from multiple departments\n\n"
    str_use_cases += "## 🔬 **Research Projects**\n"
    str_use_cases += "- **Experiment Tracking**: Raw data, processed data, and analysis scripts\n"
    str_use_cases += "- **Model Development**: Training data, validation data, and model artifacts\n"
    str_use_cases += "- **Collaborative Research**: Multiple researchers working on related datasets\n\n"
    str_use_cases += "## 📊 **Data Science Workflows**\n"
    str_use_cases += (
        "- **ETL Pipelines**: Source data, transformed data, and output datasets\n"
    )
    str_use_cases += "- **Feature Engineering**: Raw features, derived features, and model inputs\n"
    str_use_cases += "- **Model Deployment**: Training data, model artifacts, and deployment configs\n\n"
    str_use_cases += "## 🌐 **Multi-Environment Management**\n"
    str_use_cases += (
        "- **Environment Datasets**: Dev, staging, and production datasets\n"
    )
    str_use_cases += "- **Configuration Management**: Environment-specific configs and secrets\n"
    str_use_cases += (
        "- **Deployment Tracking**: Track data changes across environments\n"
    )

    mo.md(str_use_cases)
    return


@app.cell
def _(mo):
    # Demonstrate Catalog with remote storage (GCS example)
    str_remote_catalog = ""
    str_remote_catalog += "**Remote Storage with Catalog:**\n\n"
    str_remote_catalog += "## ☁️ **Cloud-Native Catalogs**\n"
    str_remote_catalog += (
        "Catalogs work seamlessly with remote storage backends:\n\n"
    )
    str_remote_catalog += "```python\n"
    str_remote_catalog += "# Local catalog\n"
    str_remote_catalog += (
        'local_catalog = Catalog(root_dir="/path/to/local/data")\n\n'
    )
    str_remote_catalog += "# GCS catalog\n"
    str_remote_catalog += 'gcs_catalog = Catalog(root_dir="gs://my-bucket")\n\n'
    str_remote_catalog += "# S3 catalog\n"
    str_remote_catalog += 's3_catalog = Catalog(root_dir="s3://my-bucket")\n\n'
    str_remote_catalog += "# Azure catalog\n"
    str_remote_catalog += 'azure_catalog = Catalog(root_dir="az://my-container")\n'
    str_remote_catalog += "```\n\n"
    str_remote_catalog += "## 🔧 **fsspec Integration**\n"
    str_remote_catalog += (
        "- **Backend Agnostic**: Works with any fsspec-compatible storage\n"
    )
    str_remote_catalog += (
        "- **Authentication**: Supports all fsspec authentication methods\n"
    )
    str_remote_catalog += (
        "- **Performance**: Optimized for cloud storage patterns\n"
    )
    str_remote_catalog += (
        "- **Scalability**: Handle petabytes of data across multiple datasets\n"
    )

    mo.md(str_remote_catalog)
    return


@app.cell
def _(Catalog, Path):
    gcs_catalog = Catalog(root_dir="gs://kirin-test-bucket")
    ds = gcs_catalog.get_dataset("test-dataset")
    ds.checkout()
    # ds.files["notes.txt"].download_to("notes.txt")
    with ds.local_files() as local_files:
        notes = Path(local_files["notes.txt"]).read_text()
    notes
    return


if __name__ == "__main__":
    app.run()
