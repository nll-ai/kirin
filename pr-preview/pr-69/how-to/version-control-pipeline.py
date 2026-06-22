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
    # Version Control Your Data Pipeline

    This guide shows you how to version control your ETL/data pipeline outputs
    using Kirin. You'll learn to track pipeline runs, commit transformed data,
    store pipeline metadata, and compare outputs across different runs.

    **Key Benefit**: With Kirin, you don't need to organize files in directory
    hierarchies like `data/v1/`, `data/v2/`, or `runs/run_001/`. Instead, use
    the same filenames across runs and let Kirin's commit system handle
    versioning. Metadata is stored with commits, not in directory structures.
    """)
    return


@app.cell
def _():
    import json
    import tempfile
    from datetime import datetime
    from pathlib import Path

    import polars as pl

    from kirin import Dataset

    temp_dir = Path(tempfile.mkdtemp(prefix="kirin_pipeline_demo_"))
    pipeline_registry = Dataset(root_dir=temp_dir, name="etl_pipeline")

    print(f"✅ Pipeline registry created at: {temp_dir}")
    return Path, datetime, json, pipeline_registry, pl, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Why Not Use Directory Hierarchies?

    **Traditional approach** (what you might do without Kirin):

    ```
    data/
    ├── v1/
    │   ├── transformed_sales.csv
    │   ├── product_summary.csv
    │   └── pipeline_metadata.json
    ├── v2/
    │   ├── transformed_sales.csv
    │   ├── product_summary.csv
    │   └── pipeline_metadata.json
    └── runs/
        ├── run_001/
        │   └── transformed_sales.csv
        └── run_002/
            └── transformed_sales.csv
    ```

    **Problems with this approach:**
    - Complex directory structures to maintain
    - Version info scattered across directory paths
    - Hard to query or compare versions
    - Manual organization required

    **Kirin's approach** (what we'll demonstrate):

    ```
    dataset/
    ├── transformed_sales.csv  (versioned by commits)
    ├── product_summary.csv     (versioned by commits)
    └── pipeline_metadata.json  (versioned by commits)
    ```

    - Same filenames across all runs
    - Version info stored in commit metadata
    - Easy to query and compare
    - Automatic versioning via commits
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Set Up Pipeline Input Data

    Create sample input data that your pipeline will process. In production,
    this might come from external sources like databases or APIs.
    """)
    return


@app.cell
def _(temp_dir):
    input_data_dir = temp_dir / "input_data"
    input_data_dir.mkdir(exist_ok=True)

    raw_data = input_data_dir / "raw_sales.csv"
    raw_data.write_text("""order_id,customer_id,product,quantity,price,order_date
    1001,C001,Widget A,2,29.99,2024-01-15
    1002,C002,Widget B,1,19.99,2024-01-16
    1003,C001,Widget C,3,39.99,2024-01-17
    1004,C003,Widget A,1,29.99,2024-01-18
    1005,C002,Widget B,2,19.99,2024-01-19""")

    print("✅ Created sample input data")
    return input_data_dir, raw_data


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Run Pipeline and Generate Outputs

    Simulate a pipeline run that processes input data and generates transformed
    outputs, logs, and metadata.

    **Note**: We use simple, consistent filenames (`transformed_sales.csv`,
    `product_summary.csv`, etc.) without version numbers or directory
    hierarchies. Versioning is handled by commits, not filenames.
    """)
    return


@app.cell
def _(datetime, input_data_dir, json, pl, temp_dir):
    def run_pipeline(run_id, input_file, output_dir):
        """Simulate a pipeline run that processes data."""
        df = pl.read_csv(input_file)

        transformed_data = df.with_columns(
            [
                (pl.col("quantity") * pl.col("price")).alias("total_amount"),
                pl.col("order_date").str.strptime(pl.Date, "%Y-%m-%d").alias("date"),
            ]
        )

        output_dir.mkdir(exist_ok=True, parents=True)

        # Use simple, consistent filenames - no version numbers, run IDs,
        # or directory hierarchies
        transformed_path = output_dir / "transformed_sales.csv"
        transformed_data.write_csv(transformed_path)

        summary = transformed_data.group_by("product").agg(
            [
                pl.col("total_amount").sum().alias("total_revenue"),
                pl.col("quantity").sum().alias("total_quantity"),
            ]
        )

        summary_path = output_dir / "product_summary.csv"
        summary.write_csv(summary_path)

        # Metadata stored separately, not in directory structure
        pipeline_metadata = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "input_file": str(input_file),
            "records_processed": len(transformed_data),
            "products_count": len(summary),
            "total_revenue": float(summary["total_revenue"].sum()),
            "execution_time_seconds": 2.5,
            "pipeline_version": "1.0.0",
        }

        metadata_path = output_dir / "pipeline_metadata.json"
        metadata_path.write_text(json.dumps(pipeline_metadata, indent=2))

        log_path = output_dir / "pipeline.log"
        log_path.write_text(
            f"""Pipeline Run {run_id}
    Started: {pipeline_metadata["timestamp"]}
    Processing {pipeline_metadata["records_processed"]} records
    Generated transformed data and summary
    Completed successfully in {pipeline_metadata["execution_time_seconds"]}s
    """
        )

        return (
            transformed_path,
            summary_path,
            metadata_path,
            log_path,
            pipeline_metadata,
        )

    # Simple output directory - no run-specific subdirectories
    output_dir = temp_dir / "outputs"
    (
        transformed1,
        summary1,
        metadata1_path,
        log1_path,
        metadata1,
    ) = run_pipeline("run_001", input_data_dir / "raw_sales.csv", output_dir)

    print("✅ Pipeline run 1 completed")
    print(f"   Records processed: {metadata1['records_processed']}")
    print(f"   Total revenue: ${metadata1['total_revenue']:.2f}")
    print(
        "   Files: transformed_sales.csv, product_summary.csv, "
        "pipeline_metadata.json, pipeline.log"
    )
    return (
        log1_path,
        metadata1,
        metadata1_path,
        output_dir,
        run_pipeline,
        summary1,
        transformed1,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Commit Pipeline Run Outputs

    Commit all pipeline outputs (transformed data, summaries, logs, metadata)
    together as a single commit. This creates a snapshot of the entire pipeline
    run.

    **Key Point**: Notice we're committing files with simple names like
    `transformed_sales.csv` - no version numbers in filenames. The version
    information (run ID, timestamp, metrics) is stored in commit metadata,
    not in directory structures or filenames.
    """)
    return


@app.cell
def _(
    log1_path,
    metadata1,
    metadata1_path,
    pipeline_registry,
    summary1,
    transformed1,
):
    commit1 = pipeline_registry.commit(
        message=f"Pipeline run {metadata1['run_id']} - {metadata1['pipeline_version']}",
        add_files=[
            str(transformed1),
            str(summary1),
            str(metadata1_path),
            str(log1_path),
        ],
        metadata={
            "pipeline_run_id": metadata1["run_id"],
            "pipeline_version": metadata1["pipeline_version"],
            "execution_time_seconds": metadata1["execution_time_seconds"],
            "records_processed": metadata1["records_processed"],
            "total_revenue": metadata1["total_revenue"],
            "products_count": metadata1["products_count"],
        },
        tags=["pipeline-run", "v1.0.0"],
    )

    print(f"✅ Committed pipeline run 1: {commit1[:8]}")
    print("   Files: 4 (transformed data, summary, metadata, log)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Run Pipeline with Updated Input Data

    Simulate a second pipeline run with updated input data. Notice we use the
    **same input filename** - the source file has been updated with new data,
    but we don't need to create `raw_sales_v2.csv` or organize it in versioned
    directories.
    """)
    return


@app.cell
def _(raw_data):
    # Update the same input file with new data (simulating source data refresh)
    raw_data.write_text("""order_id,customer_id,product,quantity,price,order_date
    1001,C001,Widget A,2,29.99,2024-01-15
    1002,C002,Widget B,1,19.99,2024-01-16
    1003,C001,Widget C,3,39.99,2024-01-17
    1004,C003,Widget A,1,29.99,2024-01-18
    1005,C002,Widget B,2,19.99,2024-01-19
    1006,C004,Widget A,5,29.99,2024-02-01
    1007,C005,Widget C,2,39.99,2024-02-02
    1008,C001,Widget B,3,19.99,2024-02-03""")

    print("✅ Updated input data (same filename, new content - 2 additional orders)")
    return


@app.cell
def _(output_dir, raw_data, run_pipeline):
    # Run pipeline again with updated input data
    # Output to the same directory - no run-specific subdirectories
    (
        transformed2,
        summary2,
        metadata2_path,
        log2_path,
        metadata2,
    ) = run_pipeline("run_002", raw_data, output_dir)

    print("✅ Pipeline run 2 completed")
    print(f"   Records processed: {metadata2['records_processed']}")
    print(f"   Total revenue: ${metadata2['total_revenue']:.2f}")
    print("   Same output filenames - versioning handled by commits")
    return log2_path, metadata2, metadata2_path, summary2, transformed2


@app.cell
def _(mo):
    mo.md(r"""
    ## Commit Second Pipeline Run

    Commit the second run outputs using the **same filenames** as the first run.
    Kirin's commit system handles versioning automatically.

    **Traditional approach** (not needed with Kirin):
    - `data/v1/transformed_sales.csv`
    - `data/v2/transformed_sales.csv`
    - `runs/run_001/transformed_sales.csv`
    - `runs/run_002/transformed_sales.csv`

    **Kirin approach** (simpler):
    - `transformed_sales.csv` (versioned by commits)
    - Metadata stored with commits, not in directory structure
    """)
    return


@app.cell
def _(
    log2_path,
    metadata1,
    metadata2,
    metadata2_path,
    pipeline_registry,
    summary2,
    transformed2,
):
    commit2 = pipeline_registry.commit(
        message=f"Pipeline run {metadata2['run_id']} - {metadata2['pipeline_version']}",
        add_files=[
            str(transformed2),
            str(summary2),
            str(metadata2_path),
            str(log2_path),
        ],
        metadata={
            "pipeline_run_id": metadata2["run_id"],
            "pipeline_version": metadata2["pipeline_version"],
            "execution_time_seconds": metadata2["execution_time_seconds"],
            "records_processed": metadata2["records_processed"],
            "total_revenue": metadata2["total_revenue"],
            "products_count": metadata2["products_count"],
        },
        tags=["pipeline-run", "v1.0.0"],
    )

    print(f"✅ Committed pipeline run 2: {commit2[:8]}")
    print(f"   Records: {metadata2['records_processed']} (↑ from 5)")
    print(
        f"   Revenue: ${metadata2['total_revenue']:.2f} "
        f"(↑ from ${metadata1['total_revenue']:.2f})"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Track Pipeline Runs Over Time

    View all pipeline runs in your registry and track how metrics change across
    runs.
    """)
    return


@app.cell
def _(pipeline_registry):
    all_runs = pipeline_registry.history()

    print("📊 Pipeline Run History")
    print("=" * 50)

    for run_commit in all_runs:
        run_meta = run_commit.metadata or {}
        print(f"\n🔹 {run_commit.short_hash}: {run_commit.message}")
        print(f"   Records: {run_meta.get('records_processed', 'N/A')}")
        print(f"   Revenue: ${run_meta.get('total_revenue', 0):.2f}")
        print(f"   Execution time: {run_meta.get('execution_time_seconds', 'N/A')}s")
        print(f"   Tags: {', '.join(run_commit.tags)}")
    return (all_runs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Compare Pipeline Runs

    Use `compare_commits()` to see what changed between pipeline runs including
    metadata differences and file changes.
    """)
    return


@app.cell
def _(all_runs, pipeline_registry):
    if len(all_runs) >= 2:
        print("🔄 Pipeline Run Comparison")
        print("=" * 40)

        run1_commit = all_runs[-1]
        run2_commit = all_runs[-2]

        comparison = pipeline_registry.compare_commits(
            run1_commit.hash, run2_commit.hash
        )

        print("Comparing:")
        print(f"  {comparison['commit1']['hash']}: {comparison['commit1']['message']}")
        print(f"  {comparison['commit2']['hash']}: {comparison['commit2']['message']}")

        print("\n📊 Metadata Changes:")
        metadata_diff = comparison["metadata_diff"]

        if metadata_diff["changed"]:
            for diff_key, change in metadata_diff["changed"].items():
                print(f"   {diff_key}: {change['old']} → {change['new']}")

        print("\n📁 File Changes:")
        files_diff = comparison["files_diff"]
        if files_diff["added"]:
            print(f"   ➕ Added: {files_diff['added']}")
        if files_diff["removed"]:
            print(f"   ➖ Removed: {files_diff['removed']}")
        if files_diff["modified"]:
            print(f"   🔄 Modified: {files_diff['modified']}")
    else:
        print("Not enough runs to compare")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Query Pipeline Runs by Metadata

    Use `find_commits()` to discover pipeline runs by metadata filters, such as
    finding runs with high revenue or specific pipeline versions.
    """)
    return


@app.cell
def _(pipeline_registry):
    print("🔍 Pipeline Run Discovery")
    print("=" * 40)

    high_revenue_runs = pipeline_registry.find_commits(
        metadata_filter=lambda m: m.get("total_revenue", 0) > 1000
    )
    print(f"\n💰 High revenue runs (>$1000): {len(high_revenue_runs)}")
    for high_rev_commit in high_revenue_runs:
        print(
            f"   {high_rev_commit.short_hash}: "
            f"${high_rev_commit.metadata.get('total_revenue', 0):.2f}"
        )

    v1_runs = pipeline_registry.find_commits(tags=["v1.0.0"])
    print(f"\n🏷️  v1.0.0 runs: {len(v1_runs)}")
    for v1_commit in v1_runs:
        print(f"   {v1_commit.short_hash}: {v1_commit.message}")
    return (v1_runs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Access Pipeline Outputs from Specific Runs

    Checkout a specific pipeline run commit to access its outputs. Files are
    lazily downloaded when accessed.
    """)
    return


@app.cell
def _(Path, pipeline_registry, pl, v1_runs):
    if v1_runs:
        latest_run = v1_runs[0]
        print(f"📦 Accessing pipeline run: {latest_run.short_hash}")
        print("=" * 40)

        pipeline_registry.checkout(latest_run.hash)

        print("\n📁 Files in this run:")
        for filename in pipeline_registry.list_files():
            file_obj = pipeline_registry.get_file(filename)
            print(f"   {filename}: {file_obj.size} bytes")

        print("\n💾 Accessing transformed data (lazy loading):")
        with pipeline_registry.local_files() as local_files:
            if "transformed_sales.csv" in local_files:
                transformed_path = local_files["transformed_sales.csv"]
                print(f"   transformed_sales.csv → {transformed_path}")
                print(f"   File exists: {Path(transformed_path).exists()}")

                df = pl.read_csv(transformed_path)
                print("\n📊 Data preview:")
                print(df.head(3))
    else:
        print("No runs found")
        latest_run = None
        transformed_path = None
        df = None
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Track Pipeline Performance Metrics

    Analyze pipeline performance over time by extracting metrics from commit
    history.
    """)
    return


@app.cell
def _(all_runs, pl):
    print("📈 Pipeline Performance Analysis")
    print("=" * 40)

    performance_data = []
    for perf_commit in all_runs:
        if perf_commit.metadata:
            performance_data.append(
                {
                    "run_id": perf_commit.metadata.get("pipeline_run_id", "unknown"),
                    "commit": perf_commit.short_hash,
                    "records": perf_commit.metadata.get("records_processed", 0),
                    "revenue": perf_commit.metadata.get("total_revenue", 0),
                    "execution_time": perf_commit.metadata.get(
                        "execution_time_seconds", 0
                    ),
                }
            )

    if performance_data:
        perf_df = pl.DataFrame(performance_data)

        print("\nPerformance Summary:")
        print(perf_df)

        print("\n📊 Statistics:")
        print(f"   Average records per run: {perf_df['records'].mean():.1f}")
        print(f"   Total revenue across runs: ${perf_df['revenue'].sum():.2f}")
        print(f"   Average execution time: {perf_df['execution_time'].mean():.2f}s")
    else:
        print("No performance data found")
        perf_df = None
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    Your pipeline registry now tracks:

    - ✅ Complete pipeline run snapshots (data, logs, metadata)
    - ✅ Pipeline run history with linear commits
    - ✅ Metadata tracking (execution time, records processed, revenue)
    - ✅ Run comparison and diffing
    - ✅ Query runs by metadata filters
    - ✅ Lazy loading of pipeline outputs
    - ✅ Content-addressed storage (automatic deduplication)
    - ✅ Cloud storage support (works with S3, GCS, Azure)

    **Key Benefits Over Traditional Approaches:**

    - **No directory hierarchies**: Use simple filenames, no need for
      `data/v1/`, `runs/run_001/` structures
    - **Metadata with commits**: Version info stored with commits, not in
      directory paths
    - **Same filenames**: Use consistent names like `transformed_sales.csv`
      across all runs
    - **Automatic versioning**: Commits handle versioning automatically

    **Use Cases:**
    - ETL pipeline versioning
    - Data transformation tracking
    - Pipeline output auditing
    - Reproducible data processing workflows
    - Pipeline performance monitoring
    """)
    return


if __name__ == "__main__":
    app.run()
