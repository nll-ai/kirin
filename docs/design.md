# Kirin: Simplified Content-Addressed Storage for Data Versioning

## Design Document

## 1. Introduction

Kirin is a simplified tool for version-controlling data using content-addressed
storage.
The primary goals are to enable file versioning and file set versioning with a
linear
commit history that is backend-agnostic, serverless, and focuses on ergonomic
Python API.

### 1.1 Problem Statement

Data versioning is a critical need in machine learning and data science
workflows. Current solutions often:

- Are tied to specific storage backends
- Lack the flexibility of Git's content-addressed model
- Require server infrastructure
- Do not track data usage effectively
- Are difficult to integrate with existing workflows and tools
- Fail to maintain lineage between derived files and their sources
- Inefficiently copy data when performing operations, leading to excessive
  memory usage and slow performance

### 1.2 Design Goals

Kirin aims to provide a simplified, robust solution with the following
properties:

1. **Backend-agnostic storage**: Support any storage backend (local filesystem,
   S3, Dropbox, Google Drive, SharePoint, etc.)
2. **Content-addressed storage**: Use hashing to ensure data integrity and
   deduplication
3. **Linear commit history**: Simple, linear versioning without branching
   complexity
4. **Serverless architecture**: No need for dedicated servers; all logic
   runs client-side
5. **Ergonomic Python API**: Focus on ease of use and developer experience
6. **File versioning**: Track changes to individual files over time
7. **Zero-copy operations**: Minimize data copying through memory mapping and
   streaming operations whenever possible
8. **Clean API**: Provide a programmatic API optimized for Python workflows

### 1.3 Jobs to be Done

Using Clayton Christensen's "Jobs to be Done" framework, we can identify the key
user personas and the specific jobs they need to accomplish with Kirin:

#### 1.3.1 Data Scientist / ML Engineer

**Jobs to be Done:**

1. **Track Experiment Data**: "I need to keep track of which datasets were used
   in which experiments so I can reproduce my results."
   - Kirin enables this through content-addressed storage and automatic lineage
   tracking.
   - Example: "When my model performed exceptionally well, I could trace back
   exactly which version of the dataset was used and recreate the conditions."

2. **Find and Use the Right Data Version**: "I need to identify and access
   specific versions of datasets for training models."
   - Kirin's versioning system with explicit commits makes this possible.
   - Example: "I needed to compare model performance on data from Q1 vs Q2, and
   Kirin let me checkout each version effortlessly."

3. **Collaborate with Team Members**: "I need to share datasets with colleagues
   in a way that ensures we're all using the same exact data."
   - The content-addressed storage ensures data integrity across team members.
   - Example: "My colleague in another country could reproduce my analysis
   because Kirin guaranteed we had identical datasets."

4. **Document Data Transformations**: "I need to track how raw data is
   transformed into model-ready data."
   - The lineage tracking captures the entire transformation pipeline.
   - Example: "When questioned about our preprocessing steps, I could show the
   exact sequence of transformations from raw to processed data."

#### 1.3.2 Data Engineer

**Jobs to be Done:**

1. **Manage Data Pipelines**: "I need to ensure data pipelines produce consistent, traceable outputs."
   - Kirin's automatic tracking of inputs and outputs creates a clear audit trail.
   - Example: "When a downstream process broke, I could trace back through the pipeline to identify which transformation introduced the issue."

2. **Optimize Storage Usage**: "I need to handle large datasets efficiently without wasting storage."
   - Content-addressed storage with deduplication and zero-copy operations reduces storage overhead.
   - Example: "Despite having multiple versions of our 500GB dataset, we only used 600GB of storage because Kirin only stored the changed portions."

3. **Support Multiple Storage Solutions**: "I need to work with data across various storage systems our organization uses."
   - The backend-agnostic design allows seamless work across storage solutions.
   - Example: "We migrated from local storage to S3 without changing our workflows because Kirin abstracted away the storage layer."

4. **Ensure Data Governance**: "I need to track who accesses what data and how it's used."
   - Usage tracking provides comprehensive audit logs.
   - Example: "For compliance reporting, I could generate a complete report of which teams accessed sensitive datasets."

#### 1.3.3 Data Team Manager / Lead

**Jobs to be Done:**

1. **Ensure Reproducibility**: "I need to guarantee that our team's work is reproducible for scientific integrity and audit purposes."
   - End-to-end versioning and lineage tracking supports full reproducibility.
   - Example: "When preparing a paper for submission, we could include Kirin references that allowed reviewers to verify our results."

2. **Manage Technical Debt**: "I need to understand data dependencies to prevent cascading failures when data changes."
   - Lineage visualization helps identify dependencies.
   - Example: "Before making a major change to our core dataset, I could see all downstream analyses that would be affected."

3. **Accelerate Onboarding**: "I need new team members to quickly understand our data ecosystem."
   - Data catalogs and lineage visualization provide a map of available data and relationships.
   - Example: "New hires could browse our data catalog to understand available datasets and how they relate to each other."

4. **Support Regulatory Compliance**: "I need to demonstrate data provenance for regulatory compliance."
   - Complete tracking of data origins and transformations provides necessary documentation.
   - Example: "During an audit, we could show the complete history of how customer data was processed and anonymized."

#### 1.3.4 MLOps Engineer

**Jobs to be Done:**

1. **Deploy Models with Data Dependencies**: "I need to package models with their exact data dependencies."
   - Content-addressed references ensure exact data versions are specified.
   - Example: "When deploying to production, our CI/CD pipeline could pull the exact data version used in validation."

2. **Monitor Data Drift**: "I need to compare production data against training data to detect drift."
   - Versioned datasets make it easy to compare current data with historical versions.
   - Example: "Our monitoring system could compare daily production inputs against the original training data to detect shifts."

3. **Implement Data-Centric CI/CD**: "I need automated tests that verify data quality across pipeline stages."
   - Lineage tracking enables validation at each transformation step.
   - Example: "Our CI pipeline ran tests against each version of the data to ensure transformations preserved key statistical properties."

4. **Roll Back Data When Needed**: "I need to quickly revert to previous data versions if issues arise."
   - Version control provides the ability to checkout any previous state.
   - Example: "When we discovered an issue with the latest data processing, we could roll back to the previous version in minutes while debugging."

#### 1.3.5 Laboratory Scientist

**Jobs to be Done:**

1. **Ensure Experimental Reproducibility**: "I need to document and version all data associated with my laboratory experiments."
   - Content-addressed storage ensures data integrity and versioning for all experimental outputs.
   - Example: "Six months after publication, we could precisely reconstruct our experimental dataset when responding to reviewer questions."

2. **Track Sample Lineage**: "I need to track how samples and their derivatives are processed through multiple analyses."
   - File lineage features provide a complete chain of custody for samples through the analytical pipeline.
   - Example: "When an unusual pattern appeared in our final results, we could trace it back to the original sample and specific processing steps."

3. **Manage Collaborative Research**: "I need to share experimental data with collaborators while maintaining version control."
   - Dataset versioning and backend-agnostic storage facilitate secure collaboration.
   - Example: "Our collaborators at another institution could access the exact data versions we used, ensuring consistent analysis across research groups."

4. **Document Methods and Parameters**: "I need to record the exact parameters used for each instrument and analysis."
   - Transformation tracking records all processing parameters alongside the data.
   - Example: "Years later, we could verify the exact instrument settings and analysis parameters used to generate each data file."

### 1.4 Feature-to-Job Mapping

The table below maps Kirin features to the specific jobs they help users
accomplish:

| Kirin Feature | Primary Jobs Addressed | Key User Personas |
|----------------|------------------------|-------------------|
| **Content-Addressed Storage** | • Track Experiment Data<br/>• Find and Use the Right Data Version<br/>• Collaborate with Team Members<br/>• Ensure Reproducibility<br/>• Ensure Experimental Reproducibility | Data Scientist, ML Engineer, Team Lead, Laboratory Scientist |
| **Automatic Lineage Tracking** | • Document Data Transformations<br/>• Manage Data Pipelines<br/>• Track Sample Lineage<br/>• Manage Technical Debt | Data Scientist, Data Engineer, Laboratory Scientist |
| **Backend-Agnostic Storage** | • Support Multiple Storage Solutions<br/>• Optimize Storage Usage<br/>• Manage Collaborative Research | Data Engineer, MLOps Engineer, Laboratory Scientist |
| **Dataset Versioning** | • Deploy Models with Data Dependencies<br/>• Roll Back Data When Needed<br/>• Monitor Data Drift<br/>• Ensure Experimental Reproducibility | MLOps Engineer, Data Engineer, Laboratory Scientist |
| **Usage Tracking** | • Document Data Usage<br/>• Ensure Data Governance<br/>• Support Regulatory Compliance<br/>• Document Methods and Parameters | Team Lead, Laboratory Scientist |
| **Zero-Copy Operations** | • Optimize Storage Usage<br/>• Handle Large Datasets | Data Engineer, MLOps Engineer |
| **Data Catalog** | • Accelerate Onboarding<br/>• Find the Right Data Version<br/>• Manage Collaborative Research | Team Lead, Data Scientist, Laboratory Scientist |
| **Path-Based API** | • Implement Data-Centric CI/CD<br/>• Manage Data Pipelines | MLOps Engineer, Data Engineer |

### 1.5 User Workflows

To illustrate how Kirin supports common workflows, here are examples of how different users accomplish their tasks:

#### Model Development Workflow

A data scientist developing a new model:

1. **Discover and Access Data**:

   ```python
   # Browse the catalog to find relevant datasets
   datasets = repo.list_datasets(tags=["customer", "transactions"])

   # Checkout a specific version for reproducibility
   transactions = repo.get_dataset("transactions").checkout("2023-q2")
   ```

2. **Prepare and Transform Data**:

   ```python
   # All transformations are automatically tracked
   with repo.track_processing(description="Preprocess transactions"):
       # Read input data
       df = pd.read_csv(repo.Path("transactions/daily.csv"))

       # Transform data
       df_clean = clean_transactions(df)

       # Save processed version
       df_clean.to_csv(repo.Path("transactions/clean.csv"))
   ```

3. **Train Model with Version Awareness**:

   ```python
   # Train using specific data versions, capturing exact data dependencies
   model = train_model(repo.Path("transactions/clean.csv"))

   # Record model with data lineage
   with repo.track_processing(description="Train transaction model"):
       model.save(repo.Path("models/transaction_classifier.pkl"))
   ```

4. **Document and Share Results**:

   ```python
   # Get full lineage information for reporting
   data_lineage = repo.get_file_ancestors("models/transaction_classifier.pkl")

   # Generate visualizations of data flow
   repo.visualize_lineage("models/transaction_classifier.pkl", output="report.svg")
   ```

#### Data Pipeline Workflow

A data engineer building an ETL pipeline:

1. **Set Up Extract Stage**:

   ```python
   # Extract from source and track provenance
   with repo.track_processing(description="Extract from OLTP"):
       extract_data_from_source(
           source_db="production_db",
           output_path=repo.Path("raw/daily_extract.parquet")
       )
   ```

2. **Implement Transform Stage**:

   ```python
   # Transform with full tracking
   with repo.track_processing(description="Transform daily data"):
       # Use zero-copy operations for large files
       with repo.Path("raw/daily_extract.parquet").open_stream() as stream:
           # Process incrementally
           result = transform_stream(stream)
           result.to_parquet(repo.Path("transformed/daily.parquet"))
   ```

3. **Execute Load Stage**:

   ```python
   # Load with tracking
   with repo.track_processing(description="Load to data warehouse"):
       load_to_warehouse(
           source=repo.Path("transformed/daily.parquet"),
           target="warehouse.daily_facts"
       )
   ```

4. **Verify Pipeline Integrity**:

   ```python
   # Verify the complete lineage from source to destination
   lineage = repo.get_file_ancestors("transformed/daily.parquet")

   # Check for data quality at each stage
   for stage in lineage:
       validate_data_quality(stage)
   ```

#### Laboratory Research Workflow

A laboratory scientist conducting experimental research:

1. **Capture Experimental Data**:

   ```python
   # Create a dataset for the experiment with metadata
   experiment = repo.create_dataset(
       "experiment_2023_06",
       description="Protein binding kinetics experiment",
       metadata={
           "researcher": "Dr. Smith",
           "equipment": "Mass Spectrometer Model XYZ",
           "temperature": "22C",
           "protocol_version": "v2.3"
       }
   )

   # Commit raw instrument output files
   experiment.commit(
       add_files=[
           "spectrometer/run_001.raw",
           "spectrometer/run_002.raw"
       ],
       commit_message="Initial spectrometer runs"
   )
   ```

2. **Process and Analyze Experimental Data**:

   ```python
   # All analysis steps are automatically tracked
   with repo.track_processing(
       description="Mass spec data processing",
       parameters={"baseline_correction": "adaptive", "peak_detection": "centroid"}
   ):
       # Read raw data
       raw_data = read_spectrometer_data(repo.Path("spectrometer/run_001.raw"))

       # Process data with analysis software
       processed_data = process_spectrometer_data(raw_data)

       # Save processed results
       processed_data.to_csv(repo.Path("processed/peaks_001.csv"))

       # Generate visualization
       plot_spectrum(processed_data).savefig(repo.Path("figures/spectrum_001.png"))
   ```

3. **Generate Publication-Ready Results**:

   ```python
   # Combine and analyze processed data
   with repo.track_processing(description="Binding kinetics analysis"):
       # Load all processed runs
       runs = []
       for file_path in repo.Path("processed").glob("peaks_*.csv"):
           runs.append(pd.read_csv(file_path))

       # Calculate binding kinetics
       kinetics = calculate_binding_parameters(runs)

       # Save final results
       kinetics.to_csv(repo.Path("results/binding_kinetics.csv"))

       # Generate publication figure
       create_publication_figure(kinetics).savefig(
           repo.Path("figures/figure_3_binding_curve.png"), dpi=300
       )
   ```

4. **Document and Share Research**:

   ```python
   # Generate complete provenance for publication
   lineage = repo.get_file_ancestors("results/binding_kinetics.csv")

   # Create research package for collaborators
   package = repo.create_snapshot(
       files=["results/*", "figures/*", "processed/*"],
       include_lineage=True,
       output="research_package.zip"
   )

   # Generate methods section with exact parameters
   methods_text = repo.generate_methods_text(
       "results/binding_kinetics.csv",
       template="templates/methods_section.md"
   )
   ```

#### Laboratory Comparative Analysis Workflow

A laboratory scientist comparing results across multiple experiments:

1. **Identify Relevant Experiments**:

   ```python
   # Find all experiments with a specific characteristic
   experiments = repo.search_datasets(
       metadata={"protocol_version": "v2.*"},
       tags=["protein-binding"]
   )

   # Create a collection of related experiments
   collection = repo.create_collection(
       "binding_kinetics_comparison",
       datasets=[exp.name for exp in experiments]
   )
   ```

2. **Standardize and Compare Results**:

   ```python
   # Process data from multiple experiments with standard methods
   with repo.track_processing(description="Comparative analysis"):
       # Collect results from each experiment
       all_results = []
       for experiment in collection.datasets:
           # Access the specific version used in the experiment
           kinetics_file = experiment.get_file("results/binding_kinetics.csv")
           all_results.append(pd.read_csv(kinetics_file))

       # Perform comparative analysis
       comparison = compare_experimental_results(all_results)

       # Save comparative results
       comparison.to_csv(repo.Path("comparative/binding_comparison.csv"))

       # Generate comparison visualization
       plot_comparison(comparison).savefig(
           repo.Path("comparative/binding_comparison.png")
       )
   ```

3. **Validate Protocol Improvements**:

   ```python
   # Analyze protocol version impact
   protocol_impact = repo.analyze_metadata_impact(
       collection=collection,
       target_file="results/binding_kinetics.csv",
       groupby="protocol_version",
       metrics=["affinity", "specificity"]
   )

   # Generate protocol evolution report
   generate_protocol_report(
       protocol_impact,
       output=repo.Path("reports/protocol_evolution.pdf")
   )
   ```

## 2. System Architecture

### 2.1 Core Components

#### 2.1.1 Storage Layer

The Storage Layer uses fsspec for backend-agnostic storage. It provides a unified interface for:

- Reading/writing files
- Listing files
- Getting file metadata
- Streaming data access
- Memory-mapped access where supported

**Key Abstractions:**

```python
class ContentStore:
    """Manages content-addressed storage."""

    def store_file(self, file_path: Path) -> str: ...  # Returns content hash
    def store_content(self, content: bytes) -> str: ...  # Store content bytes
    def retrieve(self, content_hash: str) -> bytes: ...  # Retrieve by hash
    def exists(self, content_hash: str) -> bool: ...  # Check existence
    def open_stream(self, content_hash: str, mode: str = "rb") -> IO[bytes]: ...
```

Built-in fsspec backends:

- Local filesystem
- S3
- GCS
- Azure Blob Storage
- Dropbox
- Google Drive

#### 2.1.2 Versioning Layer

The Versioning Layer manages the linear version history of files and file sets:

- Tracks changes to individual files
- Manages collections of files as atomic units
- Maintains a linear commit history (no branching)
- Simple parent-child relationships between commits

**Key Abstractions:**

```python
@dataclass(frozen=True)
class File:
    """Represents a versioned file with content-addressed storage."""

    hash: str
    name: str
    size: int
    content_type: Optional[str] = None

    def read_bytes(self) -> bytes: ...
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def open(self, mode: str = "rb") -> Union[BinaryIO, TextIO]: ...
    def download_to(self, path: Union[str, Path]) -> str: ...

@dataclass(frozen=True)
class Commit:
    """Represents an immutable snapshot of files at a point in time."""

    hash: str
    message: str
    timestamp: datetime
    parent_hash: Optional[str]  # Linear history - single parent
    files: Dict[str, File]  # filename -> File mapping
```

#### 2.1.3 Dataset Layer

The Dataset Layer provides high-level abstractions for managing datasets:

- Organizes files into logical datasets
- Maintains linear commit history
- Provides simple file operations
- Enables dataset discovery

**Key Abstractions:**

```python
class Dataset:
    """Represents a logical collection of files with linear history."""

    def __init__(self, root_dir: Union[str, Path], name: str, description: str = ""): ...
    def commit(self, message: str, add_files: List[Union[str, Path]] = None,
               remove_files: List[str] = None) -> str: ...  # Returns commit hash
    def checkout(self, commit_hash: str) -> None: ...
    def get_file(self, name: str) -> Optional[File]: ...
    def list_files(self) -> List[str]: ...
    def read_file(self, name: str, mode: str = "r") -> Union[str, bytes]: ...
    def history(self, limit: Optional[int] = None) -> List[Commit]: ...
    def get_info(self) -> dict: ...
```

### 2.2 System Flow

1. **Data Ingestion Flow**:
   - User provides files to be tracked
   - Files are hashed and stored in content store
   - A commit is created with references to file versions
   - The commit is recorded in the linear history

2. **Data Access Flow**:
   - User requests a specific version of a file or dataset
   - System resolves the logical path to a content hash
   - Content is retrieved from the storage backend
   - Content is provided to the user

3. **Data Processing Flow**:
   - User accesses input data files
   - Processing is performed
   - Output files are stored in Kirin
   - New commit is created with updated files

## 3. Data Structures and Storage

### 3.1 Content Store Layout

The content store is organized as follows:

```text
<root>/
  ├── data/                     # Content-addressed storage
  │   ├── ab/                  # First two characters of hash
  │   │   └── cdef1234...       # Rest of the hash
  │   └── ...
  └── datasets/                 # Dataset storage
      ├── dataset1/             # Dataset directory
      │   └── commits.json       # Linear commit history
      └── ...
```

### 3.2 Commit History Format

Each dataset maintains a single JSON file with linear commit history:

```json
{
  "dataset_name": "my_dataset",
  "commits": [
    {
      "hash": "abc123...",
      "message": "Initial commit",
      "timestamp": "2024-01-01T12:00:00",
      "parent_hash": null,
      "files": {
        "data.csv": {
          "hash": "def456...",
          "name": "data.csv",
          "size": 1024,
          "content_type": "text/csv"
        }
      }
    },
    {
      "hash": "ghi789...",
      "message": "Add processed data",
      "timestamp": "2024-01-01T13:00:00",
      "parent_hash": "abc123...",
      "files": {
        "data.csv": {
          "hash": "def456...",
          "name": "data.csv",
          "size": 1024,
          "content_type": "text/csv"
        },
        "processed.csv": {
          "hash": "jkl012...",
          "name": "processed.csv",
          "size": 2048,
          "content_type": "text/csv"
        }
      }
    }
  ]
}
```

## 4. API Design

### 4.1 Python API

The Python API is designed for simplicity and ease of use:

```python
# Basic usage
from kirin import Dataset, File, Commit

# Initialize dataset
dataset = Dataset(root_dir="/path/to/data", name="my_dataset")

# Commit files
commit_hash = dataset.commit(
    message="Initial commit",
    add_files=["file1.csv", "file2.json"]
)

# Access files from current commit
files = dataset.files
print(f"Files: {list(files.keys())}")

# Read a file
content = dataset.read_file("file1.csv", mode="r")  # text mode
binary_content = dataset.read_file("file1.csv", mode="rb")  # binary mode

# Get a specific file object
file_obj = dataset.get_file("file1.csv")
if file_obj:
    print(f"File size: {file_obj.size} bytes")
    print(f"Content hash: {file_obj.short_hash}")

    # Read file content
    content = file_obj.read_text()

    # Download to local path
    file_obj.download_to("/tmp/file1.csv")

    # Open as file handle
    with file_obj.open("r") as f:
        data = f.read()

# Checkout a specific commit
dataset.checkout(commit_hash)

# Get commit history
history = dataset.history(limit=10)
for commit in history:
    print(f"{commit.short_hash}: {commit.message}")

# Get specific commit
commit = dataset.get_commit(commit_hash)
if commit:
    print(f"Commit: {commit.short_hash}")
    print(f"Message: {commit.message}")
    print(f"Files: {commit.list_files()}")
    print(f"Total size: {commit.get_total_size()} bytes")

# Local file access for processing
with dataset.local_files() as local_files:
    for filename, local_path in local_files.items():
        print(f"{filename} -> {local_path}")
        # Process files locally
        df = pd.read_csv(local_path)

# Remove files in a commit
dataset.commit(
    message="Remove old file",
    remove_files=["old_file.csv"]
)

# Add and remove files in same commit
dataset.commit(
    message="Update dataset",
    add_files=["new_file.csv"],
    remove_files=["old_file.csv"]
)
```

### 4.2 Cloud Storage Support

Kirin supports multiple cloud storage backends through fsspec:

```python
# S3
dataset = Dataset(root_dir="s3://my-bucket/datasets", name="my_dataset")

# Google Cloud Storage
dataset = Dataset(root_dir="gs://my-bucket/datasets", name="my_dataset")

# Azure Blob Storage
dataset = Dataset(root_dir="az://my-container/datasets", name="my_dataset")

# With custom filesystem
from kirin import get_s3_filesystem
fs = get_s3_filesystem(profile="my-profile")
dataset = Dataset(root_dir="s3://my-bucket/datasets", name="my_dataset", fs=fs)
```

## 5. Performance Considerations

### 5.1 Zero-Copy Architecture

Kirin is designed with a zero-copy philosophy wherever possible:

- **Memory-mapped files**: When working with local files, memory mapping is used to avoid loading entire files into memory
- **Streaming operations**: For operations on large files, streaming interfaces are provided to process data incrementally
- **Direct transfers**: When copying between storage backends, data is streamed directly without loading into application memory
- **Reference-based operations**: Operations like checkouts use references instead of copying file content

### 5.2 Caching

Local caching of frequently accessed files will improve performance when working with remote storage backends.

### 5.3 Lazy Loading

Content will be loaded only when needed, reducing unnecessary network traffic.

### 5.4 Optimized Hashing

To improve performance when hashing large files:

- Incremental hashing is used for streaming data
- Parallel chunk processing for multi-core systems
- Optional content-based chunking for improved deduplication

## 6. Future Extensions

### 6.1 CLI Interface

A command-line interface could be developed to mirror Git's familiar commands:

```bash
# Initialize dataset
kirin init my_dataset

# Add files and commit
kirin commit my_dataset -a file1.csv file2.json -m "Initial commit"

# Show history
kirin log my_dataset

# Checkout version
kirin checkout my_dataset <commit-hash>
```

### 6.2 Integration with ML Frameworks

Direct integration with popular ML frameworks like PyTorch and TensorFlow can streamline data loading.

### 6.3 Native Format Handlers

Format-specific handlers could be developed to enable operations directly on file contents:

- Parquet/Arrow operations for columnar data
- HDF5/Zarr for array data
- SQLite for tabular data

## 7. Conclusion

Kirin's simplified architecture provides a robust, flexible system for data versioning that meets the specified requirements:

1. It supports multiple storage backends through fsspec
2. It uses content-addressed storage for integrity and deduplication
3. It provides linear commit history without branching complexity
4. It operates in a serverless manner
5. It focuses on ergonomic Python API design
6. It employs zero-copy operations wherever possible, optimizing for performance and resource efficiency

This design document outlines a simplified path forward that prioritizes ease of use and maintainability while providing the core functionality needed for data versioning.
