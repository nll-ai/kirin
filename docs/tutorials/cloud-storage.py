# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
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
    # Cloud Storage Overview

    This tutorial introduces you to using Kirin with cloud storage backends.
    You'll learn how Kirin works seamlessly with S3, GCS, Azure, and other
    cloud storage providers, and understand the key concepts for working with
    remote datasets.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What You'll Learn

    - Understanding cloud storage backends and how Kirin uses them
    - How to create catalogs and datasets with cloud storage
    - Authentication methods for different cloud providers
    - Working with remote files using the same API as local files
    - Key differences and considerations when using cloud storage
    - Best practices for cloud storage workflows
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prerequisites

    - Completed [Your First Dataset](first-dataset.md) tutorial
    - Basic understanding of datasets and commits
    - Familiarity with cloud storage concepts (S3, GCS, Azure)
    """)


@app.cell
def _():
    import tempfile
    from pathlib import Path

    from kirin import Catalog

    # For this tutorial, we'll use local storage to demonstrate concepts
    # In production, you would use: Catalog(root_dir="s3://my-bucket/data")
    temp_dir = Path(tempfile.mkdtemp(prefix="kirin_cloud_tutorial_"))
    catalog = Catalog(root_dir=temp_dir)

    print(f"✅ Created catalog with root: {catalog.root_dir}")
    print("   (In production, this would be a cloud URL like s3://bucket/data)")
    return Path, catalog, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Understanding Cloud Storage Backends

    Kirin supports multiple cloud storage backends through the **fsspec**
    library. This means you can use the same API whether you're working with
    local files or cloud storage.

    **Supported Backends:**

    - **AWS S3**: `s3://bucket/path`
    - **Google Cloud Storage**: `gs://bucket/path`
    - **Azure Blob Storage**: `az://container/path`
    - **And many more**: Dropbox, Google Drive, FTP, etc.

    The key insight is that Kirin treats all storage backends the same way -
    you use the same methods and patterns regardless of where your data is
    stored.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Creating Catalogs with Cloud Storage

    A **catalog** is a collection of datasets. When you create a catalog with
    a cloud storage URL, all datasets in that catalog will be stored in the
    cloud.

    The API is identical whether you're using local or cloud storage - you
    just change the `root_dir` parameter.
    """)


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # Local storage (what we're using in this tutorial)
    catalog = Catalog(root_dir="/path/to/local/data")

    # AWS S3
    catalog = Catalog(
        root_dir="s3://{{ bucket_name }}/data",
        aws_profile="{{ aws_profile }}"
    )

    # Google Cloud Storage
    catalog = Catalog(
        root_dir="gs://{{ bucket_name }}/data",
        gcs_token="/path/to/service-account.json",
        gcs_project="{{ project_id }}"
    )

    # Azure Blob Storage
    catalog = Catalog(
        root_dir="az://{{ container_name }}/data",
        azure_connection_string="{{ connection_string }}"
    )
    ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Key points:**

    - The URL scheme (`s3://`, `gs://`, `az://`) tells Kirin which backend to
      use
    - Authentication parameters are passed when creating the catalog
    - Once created, you use the catalog the same way regardless of backend
    """)


@app.cell
def _(catalog):
    # Create a dataset in the catalog (works the same for local or cloud)
    dataset = catalog.create_dataset(
        "cloud_demo", description="Demo dataset for cloud storage tutorial"
    )

    print(f"✅ Created dataset: {dataset.name}")
    print(f"   Dataset root: {dataset.root_dir}")
    print("   (This would be in cloud storage if using s3://, gs://, etc.)")
    return (dataset,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: The Same API for Local and Cloud

    One of Kirin's strengths is that the API is identical whether you're
    working with local files or cloud storage. This means:

    - You can develop locally and deploy to cloud without code changes
    - The same patterns work everywhere
    - You don't need to learn different APIs for different backends
    """)


@app.cell
def _(Path, dataset, temp_dir):
    # Create some sample files
    data_dir = temp_dir / "sample_data"
    data_dir.mkdir(exist_ok=True)

    # Create a CSV file
    csv_file = data_dir / "sales_data.csv"
    csv_file.write_text("""date,product,revenue
2024-01-01,Widget A,1000
2024-01-02,Widget B,1500
2024-01-03,Widget A,1200
""")

    # Create a JSON config file
    config_file = data_dir / "config.json"
    config_file.write_text("""{
    "version": "1.0",
    "region": "us-east-1",
    "currency": "USD"
}
""")

    print("✅ Created sample files:")
    print(f"   - {csv_file.name}")
    print(f"   - {config_file.name}")
    return config_file, csv_file, data_dir


@app.cell
def _(config_file, csv_file, dataset):
    # Commit files - same API whether local or cloud!
    commit_hash = dataset.commit(
        message="Initial commit: Add sales data and configuration",
        add_files=[str(csv_file), str(config_file)],
    )

    print(f"✅ Created commit: {commit_hash[:8]}")
    print("   (Files are now stored in content-addressed storage)")
    print("   (If using cloud, files are uploaded to cloud storage)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What just happened?**

    - Files were committed to the dataset
    - If using cloud storage, files were uploaded to the cloud backend
    - Files are stored using content-addressed storage (by content hash)
    - The commit was created and stored in the dataset's history

    The process is identical whether you're using local or cloud storage!
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Working with Remote Files

    When you access files from a cloud storage dataset, Kirin handles the
    complexity of downloading files on-demand. You use the same `local_files()`
    context manager as with local storage.
    """)


@app.cell
def _(Path, dataset):
    # Access files - same API for local and cloud!
    with dataset.local_files() as local_files:
        print("📂 Files available locally:")
        for filename, local_path in local_files.items():
            print(f"   {filename} -> {local_path}")

        # Read file content (works the same for local or cloud)
        csv_path = local_files["sales_data.csv"]
        csv_content = Path(csv_path).read_text()
        print("\n📝 CSV content:")
        print(csv_content[:200] + "...")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How it works with cloud storage:**

    - When you access a file, Kirin downloads it from cloud storage
    - Files are cached locally in a temporary directory
    - When you exit the context manager, temporary files are cleaned up
    - This is called **lazy loading** - files are only downloaded when needed

    **Benefits:**

    - Efficient: Only download what you use
    - Automatic cleanup: Temporary files are managed for you
    - Same API: Works identically for local and cloud storage
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Understanding Authentication

    Different cloud providers use different authentication methods. Kirin
    supports the standard authentication patterns for each provider.

    **Key concept:** Authentication is configured when you create the catalog
    or dataset, not when you access files. Once authenticated, all operations
    use those credentials automatically.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### AWS S3 Authentication Methods

    **1. AWS Profile (Recommended for Development)**

    ```python
    catalog = Catalog(
        root_dir="s3://{{ bucket_name }}/data",
        aws_profile="{{ aws_profile }}"
    )
    ```

    **2. Environment Variables**

    ```bash
    export AWS_ACCESS_KEY_ID={{ access_key_id }}
    export AWS_SECRET_ACCESS_KEY={{ secret_access_key }}
    export AWS_DEFAULT_REGION={{ region }}
    ```

    Then use without explicit credentials:

    ```python
    catalog = Catalog(root_dir="s3://{{ bucket_name }}/data")
    ```

    **3. IAM Roles (Production)**

    When running on EC2, ECS, or Lambda, IAM roles are used automatically:

    ```python
    # No credentials needed - uses IAM role
    catalog = Catalog(root_dir="s3://{{ bucket_name }}/data")
    ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Google Cloud Storage Authentication Methods

    **1. Service Account Key File**

    ```python
    catalog = Catalog(
        root_dir="gs://{{ bucket_name }}/data",
        gcs_token="/path/to/service-account.json",
        gcs_project="{{ project_id }}"
    )
    ```

    **2. Application Default Credentials**

    ```bash
    # One-time setup
    gcloud auth application-default login
    ```

    Then use without explicit credentials:

    ```python
    catalog = Catalog(root_dir="gs://{{ bucket_name }}/data")
    ```

    **3. Workload Identity (GKE/Kubernetes)**

    When running on GKE with Workload Identity configured, Application Default
    Credentials automatically detect credentials from the metadata server (which
    is how Workload Identity works):

    ```python
    # No credentials needed - uses ADC (which includes Workload Identity on GKE)
    catalog = Catalog(root_dir="gs://{{ bucket_name }}/data")
    ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Azure Blob Storage Authentication Methods

    **1. Connection String**

    ```python
    import os
    catalog = Catalog(
        root_dir="az://{{ container_name }}/data",
        azure_connection_string=os.getenv("AZURE_CONNECTION_STRING")
    )
    ```

    **2. Account Name and Key**

    ```python
    catalog = Catalog(
        root_dir="az://{{ container_name }}/data",
        azure_account_name="{{ account_name }}",
        azure_account_key="{{ account_key }}"
    )
    ```

    **3. Azure CLI Authentication**

    ```bash
    # One-time setup
    az login
    ```

    Then use without explicit credentials:

    ```python
    catalog = Catalog(root_dir="az://{{ container_name }}/data")
    ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Key Differences from Local Storage

    While the API is the same, there are some important differences to
    understand when working with cloud storage.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Network Latency

    Cloud storage operations involve network requests, which adds latency:

    - **Local storage**: Instant file access
    - **Cloud storage**: Network round-trip time (typically 10-100ms)

    **Impact:** Operations like listing files or checking if a file exists
    take longer with cloud storage.

    **Mitigation:** Use batch operations when possible, and cache results when
    appropriate.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### File Download Behavior

    With cloud storage, files are downloaded on-demand:

    - **Local storage**: Files are already on disk
    - **Cloud storage**: Files are downloaded when accessed via
      `local_files()`

    **Impact:** First access to a file takes longer (download time).

    **Mitigation:** Files are cached during the `local_files()` context, so
    multiple accesses to the same file don't re-download.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Cost Considerations

    Cloud storage has usage-based costs:

    - **Storage costs**: Pay for data stored
    - **Request costs**: Pay for API requests (PUT, GET, LIST)
    - **Data transfer costs**: Pay for data downloaded (in some cases)

    **Best practices:**

    - Batch operations to reduce request counts
    - Use appropriate storage classes (S3 Standard, IA, Glacier)
    - Compress files before storing
    - Monitor usage through cloud provider dashboards
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Authentication Requirements

    Cloud storage requires authentication, while local storage does not:

    - **Local storage**: No authentication needed
    - **Cloud storage**: Must provide credentials (profile, keys, etc.)

    **Best practices:**

    - Use IAM roles/service accounts in production (not access keys)
    - Rotate credentials regularly
    - Use least privilege (only grant necessary permissions)
    - Never commit credentials to version control
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Best Practices for Cloud Storage

    Following best practices helps you build efficient, secure, and
    cost-effective cloud storage workflows.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Security Best Practices

    **1. Use IAM Roles/Service Accounts**

    In production, use managed identities instead of access keys:

    ```python
    # ✅ Good: Uses IAM role automatically (on EC2/ECS/Lambda)
    catalog = Catalog(root_dir="s3://{{ bucket_name }}/data")

    # ❌ Avoid: Hardcoded credentials
    catalog = Catalog(
        root_dir="s3://{{ bucket_name }}/data",
        aws_access_key_id="AKIA...",
        aws_secret_access_key="..."
    )
    ```

    **2. Least Privilege**

    Grant only the permissions needed:

    - Read-only access for datasets that won't be modified
    - Write access only where necessary
    - Use bucket policies to restrict access

    **3. Monitor Access**

    Enable audit logging in your cloud provider to track access patterns.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Performance Best Practices

    **1. Batch Operations**

    Group multiple file operations together:

    ```python
    # ✅ Good: Single commit with multiple files
    dataset.commit(
        message="Add multiple files",
        add_files=["file1.csv", "file2.csv", "file3.csv"]
    )

    # ❌ Avoid: Multiple separate commits
    dataset.commit(message="Add file1", add_files=["file1.csv"])
    dataset.commit(message="Add file2", add_files=["file2.csv"])
    dataset.commit(message="Add file3", add_files=["file3.csv"])
    ```

    **2. Use Appropriate Regions**

    Store data in the same region as your compute resources to minimize
    latency.

    **3. Process Files in Chunks**

    For large files, use chunked processing:

    ```python
    with dataset.local_files() as local_files:
        if "large_data.csv" in local_files:
            local_path = local_files["large_data.csv"]
            # Process in chunks
            for chunk in pd.read_csv(local_path, chunksize=10000):
                process_chunk(chunk)
    ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Cost Optimization Best Practices

    **1. Use Appropriate Storage Classes**

    Different storage classes have different costs:

    - **Standard**: Fast access, higher cost
    - **Infrequent Access (IA)**: Lower cost, slightly slower
    - **Glacier/Archive**: Lowest cost, slow retrieval

    **2. Enable Lifecycle Policies**

    Automatically move old data to cheaper storage classes:

    ```python
    # Example: Move files older than 90 days to IA
    # (Configured in cloud provider console, not in Kirin)
    ```

    **3. Compress Files**

    Compress text files before storing to reduce storage costs:

    ```python
    import gzip
    import shutil

    # Compress before committing
    with open("data.csv", "rb") as f_in:
        with gzip.open("data.csv.gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    dataset.commit(message="Add compressed data", add_files=["data.csv.gz"])
    ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6: Common Workflows

    Here are some common patterns for working with cloud storage in Kirin.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Development to Production Workflow

    **Pattern:** Develop locally, deploy to cloud

    ```python
    # Development (local)
    dev_catalog = Catalog(root_dir="./local_data")
    dev_dataset = dev_catalog.create_dataset("my_dataset")

    # Production (cloud)
    prod_catalog = Catalog(
        root_dir="s3://{{ bucket_name }}/data",
        aws_profile="{{ aws_profile }}"
    )
    prod_dataset = prod_catalog.create_dataset("my_dataset")

    # Same code works for both!
    commit_hash = dataset.commit(
        message="Add data",
        add_files=["data.csv"]
    )
    ```

    The API is identical, so you can develop locally and deploy to cloud
    without code changes.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Multi-Environment Workflow

    **Pattern:** Use different catalogs for different environments

    ```python
    # Environment-specific catalogs
    catalogs = {
        "dev": Catalog(root_dir="./local_data"),
        "staging": Catalog(root_dir="s3://staging-bucket/data"),
        "prod": Catalog(root_dir="s3://prod-bucket/data")
    }

    # Use appropriate catalog for environment
    env = os.getenv("ENVIRONMENT", "dev")
    catalog = catalogs[env]
    dataset = catalog.get_dataset("my_dataset")
    ```

    This pattern allows you to use the same code across environments while
    keeping data isolated.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Hybrid Workflow

    **Pattern:** Mix local and cloud storage

    ```python
    # Local catalog for development
    local_catalog = Catalog(root_dir="./local_data")

    # Cloud catalog for shared/production data
    cloud_catalog = Catalog(
        root_dir="s3://{{ bucket_name }}/data",
        aws_profile="{{ aws_profile }}"
    )

    # Use local for development, cloud for production
    if os.getenv("ENVIRONMENT") == "production":
        catalog = cloud_catalog
    else:
        catalog = local_catalog
    ```

    This allows you to develop locally while using cloud storage for
    production workloads.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7: Troubleshooting Common Issues

    Here are solutions to common problems when working with cloud storage.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### SSL Certificate Errors

    **Problem:** `SSLCertVerificationError` when connecting to cloud storage

    **Solution:** Set up SSL certificates for isolated Python environments:

    ```bash
    python -m kirin.setup_ssl
    ```

    This is especially important when using pixi, uv, or other isolated
    Python environments.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Authentication Failures

    **Problem:** "Access Denied" or "Anonymous caller" errors

    **Solutions:**

    1. **Check credentials are configured:**
       ```bash
       # AWS
       aws configure list

       # GCP
       gcloud auth list

       # Azure
       az account show
       ```

    2. **Verify credentials have correct permissions:**
       - Check IAM policies for your user/role
       - Ensure bucket/container permissions are correct

    3. **Test credentials directly:**
       ```python
       # AWS
       import boto3
       s3 = boto3.client('s3')
       s3.list_buckets()  # Should work without errors
       ```
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Performance Issues

    **Problem:** Slow operations with cloud storage

    **Solutions:**

    1. **Use same region:** Store data in the same region as compute
    2. **Batch operations:** Group multiple operations together
    3. **Cache results:** Cache file lists and metadata when appropriate
    4. **Use appropriate storage class:** Standard for frequently accessed data

    **Problem:** Large file downloads are slow

    **Solutions:**

    1. **Process in chunks:** Don't download entire large files at once
    2. **Use streaming:** For very large files, consider streaming approaches
    3. **Compress files:** Smaller files download faster
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    Congratulations! You've learned the fundamentals of using Kirin with
    cloud storage:

    - ✅ **Understanding cloud backends** - S3, GCS, Azure, and more
    - ✅ **Creating cloud catalogs** - Same API for local and cloud
    - ✅ **Authentication methods** - Different approaches for each provider
    - ✅ **Working with remote files** - Lazy loading and automatic cleanup
    - ✅ **Key differences** - Network latency, costs, authentication
    - ✅ **Best practices** - Security, performance, cost optimization
    - ✅ **Common workflows** - Development to production patterns
    - ✅ **Troubleshooting** - Solutions to common issues

    ## Key Concepts

    - **Unified API**: Same methods work for local and cloud storage
    - **Content-addressed storage**: Files stored by hash, works the same
      everywhere
    - **Lazy loading**: Files downloaded on-demand when accessed
    - **Authentication**: Configured at catalog/dataset creation, not per
      operation
    - **Backend-agnostic**: Switch between backends by changing the URL

    ## Next Steps

    - **[Setup Cloud Storage](../how-to/setup-cloud-storage.md)** - Complete
      guide for setting up AWS S3, Google Cloud Storage, and Azure Blob
      Storage
    - **[Track Model Training Data](../how-to/track-model-data.md)** - See
      cloud storage in action with ML workflows
    """)


if __name__ == "__main__":
    app.run()
