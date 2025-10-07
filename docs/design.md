# Kirin: Content-Addressed Storage for Data Versioning

## Design Document

## 1. Introduction

Kirin is a tool for version-controlling data using content-addressed storage. The primary goals are to enable file versioning and file set versioning in a way that is backend-agnostic, serverless, and supports the creation of data catalogs.

### 1.1 Problem Statement

Data versioning is a critical need in machine learning and data science workflows. Current solutions often:

- Are tied to specific storage backends
- Lack the flexibility of Git's content-addressed model
- Require server infrastructure
- Do not track data usage effectively
- Are difficult to integrate with existing workflows and tools
- Fail to maintain lineage between derived files and their sources
- Inefficiently copy data when performing operations, leading to excessive memory usage and slow performance

### 1.2 Design Goals

Kirin aims to provide a robust solution with the following properties:

1. **Backend-agnostic storage**: Support any storage backend (local filesystem, S3, Dropbox, Google Drive, SharePoint, etc.)
2. **Content-addressed storage**: Use hashing to ensure data integrity and deduplication
3. **Data catalog support**: Enable building data catalogs on top of the versioning system
4. **Serverless architecture**: No need for dedicated servers; all logic runs client-side
5. **Usage tracking**: Record all data access in a structured format (SQLite database -- stick with server-free philosophy)
6. **Data lineage**: Track the relationships between files, showing which files were derived from which source files
7. **Zero-copy operations**: Minimize data copying through memory mapping and streaming operations whenever possible
8. **Clean API**: Provide both a programmatic API and CLI for easy integration

### 1.3 Jobs to be Done

Using Clayton Christensen's "Jobs to be Done" framework, we can identify the key user personas and the specific jobs they need to accomplish with Kirin:

#### 1.3.1 Data Scientist / ML Engineer

**Jobs to be Done:**

1. **Track Experiment Data**: "I need to keep track of which datasets were used in which experiments so I can reproduce my results."
   - Kirin enables this through content-addressed storage and automatic lineage tracking.
   - Example: "When my model performed exceptionally well, I could trace back exactly which version of the dataset was used and recreate the conditions."

2. **Find and Use the Right Data Version**: "I need to identify and access specific versions of datasets for training models."
   - Kirin's versioning system with explicit commits makes this possible.
   - Example: "I needed to compare model performance on data from Q1 vs Q2, and Kirin let me checkout each version effortlessly."

3. **Collaborate with Team Members**: "I need to share datasets with colleagues in a way that ensures we're all using the same exact data."
   - The content-addressed storage ensures data integrity across team members.
   - Example: "My colleague in another country could reproduce my analysis because Kirin guaranteed we had identical datasets."

4. **Document Data Transformations**: "I need to track how raw data is transformed into model-ready data."
   - The lineage tracking captures the entire transformation pipeline.
   - Example: "When questioned about our preprocessing steps, I could show the exact sequence of transformations from raw to processed data."

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

The table below maps Kirin features to the specific jobs they help users accomplish:

| Kirin Feature | Primary Jobs Addressed | Key User Personas |
|----------------|------------------------|-------------------|
| **Content-Addressed Storage** | • Track Experiment Data<br>• Find and Use the Right Data Version<br>• Collaborate with Team Members<br>• Ensure Reproducibility<br>• Ensure Experimental Reproducibility | Data Scientist, ML Engineer, Team Lead, Laboratory Scientist |
| **Automatic Lineage Tracking** | • Document Data Transformations<br>• Manage Data Pipelines<br>• Track Sample Lineage<br>• Manage Technical Debt | Data Scientist, Data Engineer, Laboratory Scientist |
| **Backend-Agnostic Storage** | • Support Multiple Storage Solutions<br>• Optimize Storage Usage<br>• Manage Collaborative Research | Data Engineer, MLOps Engineer, Laboratory Scientist |
| **Dataset Versioning** | • Deploy Models with Data Dependencies<br>• Roll Back Data When Needed<br>• Monitor Data Drift<br>• Ensure Experimental Reproducibility | MLOps Engineer, Data Engineer, Laboratory Scientist |
| **Usage Tracking** | • Document Data Usage<br>• Ensure Data Governance<br>• Support Regulatory Compliance<br>• Document Methods and Parameters | Team Lead, Laboratory Scientist |
| **Zero-Copy Operations** | • Optimize Storage Usage<br>• Handle Large Datasets | Data Engineer, MLOps Engineer |
| **Data Catalog** | • Accelerate Onboarding<br>• Find the Right Data Version<br>• Manage Collaborative Research | Team Lead, Data Scientist, Laboratory Scientist |
| **Path-Based API** | • Implement Data-Centric CI/CD<br>• Manage Data Pipelines | MLOps Engineer, Data Engineer |

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

The Storage Layer is responsible for abstracting away the details of different storage backends. It provides a unified interface for:

- Reading/writing files
- Listing files
- Getting file metadata
- Managing file permissions (when applicable)
- Streaming data access
- Memory-mapped access where supported

**Key Abstractions:**
```python
class StorageBackend(Protocol):
    """Protocol defining the interface for storage backends."""

    def read(self, path: str) -> bytes: ...
    def write(self, path: str, data: bytes) -> None: ...
    def exists(self, path: str) -> bool: ...
    def list_dir(self, path: str) -> List[str]: ...
    def get_metadata(self, path: str) -> Dict[str, Any]: ...

    # Zero-copy operations
    def open_stream(self, path: str, mode: str = "rb") -> IO[bytes]: ...
    def get_mmap(self, path: str, access: str = "r") -> mmap.mmap: ...
    def stream_copy(self, source_path: str, target_path: str) -> None: ...
```

Built-in implementations:
- LocalStorageBackend
- S3StorageBackend
- DropboxStorageBackend
- GDriveStorageBackend
- SharePointStorageBackend

#### 2.1.2 Content Addressing Layer

This layer handles the content-addressed storage mechanism:

- Generates content hashes
- Manages the content store
- Handles deduplication
- Maps logical paths to content hashes
- Uses zero-copy operations for large files

**Key Abstractions:**

```python
class ContentStore:
    """Manages content-addressed storage."""

    def store(self, data: bytes) -> str: ...  # Returns content hash
    def store_file(self, file_path: Path) -> str: ...  # Zero-copy store from file
    def store_stream(self, stream: IO[bytes]) -> str: ...  # Stream-based store

    def retrieve(self, content_hash: str) -> bytes: ...
    def retrieve_to_file(self, content_hash: str, target_path: Path) -> None: ...  # Zero-copy retrieve
    def open_stream(self, content_hash: str) -> IO[bytes]: ...  # Stream-based retrieve

    def exists(self, content_hash: str) -> bool: ...
    def get_mmap(self, content_hash: str) -> mmap.mmap: ...  # Memory-mapped access
```

#### 2.1.3 Versioning Layer

The Versioning Layer manages the version history of files and file sets:

- Tracks changes to individual files
- Manages collections of files as atomic units
- Maintains a directed acyclic graph (DAG) of versions
- Supports branching and merging

**Key Abstractions:**

```python
@dataclass(frozen=True)
class FileVersion:
    """Represents a specific version of a file."""

    path: str
    content_hash: str
    metadata: Dict[str, Any]

@dataclass(frozen=True)
class Commit:
    """Represents a snapshot of files at a point in time."""

    commit_hash: str
    files: List[FileVersion]
    parent_commits: List[str]
    message: str
    timestamp: datetime
    author: str
```

#### 2.1.4 Usage Tracking Layer

This layer records all data access and operations:

- Records when data is pulled/accessed
- Tracks processing steps applied to data
- Maintains provenance information
- Stores all information in a SQLite database

**Key Abstractions:**

```python
class UsageTracker:
    """Tracks usage of data files."""

    def record_access(self, file_version: FileVersion, user: str, purpose: str) -> None: ...
    def record_processing(self, input_files: List[FileVersion], output_files: List[FileVersion],
                          process_description: str, parameters: Dict[str, Any]) -> None: ...
    def get_access_history(self, file_version: FileVersion) -> List[Dict[str, Any]]: ...
```

#### 2.1.5 Lineage Tracking Layer

This layer is responsible for tracking the relationships between files, specifically which files were derived from which source files:

- Records parent-child relationships between files
- Maintains a directed acyclic graph (DAG) of file derivations
- Supports querying ancestry and descendants of files
- Integrates with the usage tracking layer to capture processing context

**Key Abstractions:**

```python
class LineageTracker:
    """Tracks lineage between files."""

    def record_derivation(
        self,
        source_files: List[FileVersion],
        derived_files: List[FileVersion],
        transformation_info: Dict[str, Any]
    ) -> None: ...

    def get_ancestors(self, file_version: FileVersion, depth: int = None) -> Dict[str, List[FileVersion]]: ...
    def get_descendants(self, file_version: FileVersion, depth: int = None) -> Dict[str, List[FileVersion]]: ...
    def get_derivation_info(self, source: FileVersion, target: FileVersion) -> List[Dict[str, Any]]: ...
    def visualize_lineage(self, file_version: FileVersion, include_ancestors: bool = True,
                        include_descendants: bool = True, depth: int = None) -> Any: ...
```

#### 2.1.6 Catalog Layer

The Catalog Layer provides high-level abstractions for managing datasets:

- Organizes files into logical datasets
- Maintains dataset metadata
- Supports searching and filtering datasets
- Enables dataset discovery

**Key Abstractions:**

```python
class Dataset:
    """Represents a logical collection of files."""

    def __init__(self, name: str, description: str = ""): ...
    def add_files(self, files: List[Path], message: str) -> str: ...  # Returns commit hash
    def remove_files(self, files: List[str], message: str) -> str: ...
    def checkout(self, commit_hash: str) -> None: ...
    def list_files(self) -> Dict[str, FileVersion]: ...
    def get_history(self) -> List[Commit]: ...

class Catalog:
    """Manages a collection of datasets."""

    def create_dataset(self, name: str, description: str = "") -> Dataset: ...
    def get_dataset(self, name: str) -> Dataset: ...
    def list_datasets(self) -> List[str]: ...
    def search_datasets(self, query: str) -> List[Dataset]: ...
```

### 2.2 System Flow

1. **Data Ingestion Flow**:
   - User provides files to be tracked
   - Files are hashed and stored in content store
   - File metadata is recorded
   - A commit is created with references to file versions
   - The commit is recorded in the version history

2. **Data Access Flow**:
   - User requests a specific version of a file or dataset
   - System resolves the logical path to a content hash
   - Content is retrieved from the storage backend
   - Access is recorded in the usage tracking database
   - Content is provided to the user

3. **Data Processing Flow**:
   - User accesses input data files
   - Processing is performed
   - Output files are stored in Kirin
   - Relationship between input and output files is recorded in the lineage tracker
   - Processing context and provenance information is maintained
   - Lineage graph is updated to reflect the new derivation relationships

## 3. Data Structures and Storage

### 3.1 Content Store Layout

The content store is organized as follows:

```
<root>/
  ├── objects/                  # Content-addressed storage
  │   ├── ab/                   # First two characters of hash
  │   │   └── cdef1234...       # Rest of the hash
  │   └── ...
  ├── refs/                     # Named references to commits
  │   ├── datasets/             # Dataset references
  │   │   ├── dataset1/HEAD     # Points to current commit
  │   │   └── ...
  │   └── ...
  ├── commits/                  # Commit objects
  │   ├── abcdef1234...         # Commit hash
  │   └── ...
  ├── metadata/                 # Metadata for files and datasets
  │   ├── datasets/             # Dataset metadata
  │   │   ├── dataset1.json
  │   │   └── ...
  │   └── files/                # File metadata
  │       ├── abcdef1234...     # Content hash
  │       └── ...
  └── usage.db                  # SQLite database for usage tracking
```

### 3.2 Usage Database Schema

The usage tracking database will use SQLite with the following schema:

```sql
-- Files table
CREATE TABLE files (
    hash TEXT PRIMARY KEY,
    original_path TEXT,
    mime_type TEXT,
    size INTEGER,
    created_at TIMESTAMP
);

-- Commits table
CREATE TABLE commits (
    hash TEXT PRIMARY KEY,
    message TEXT,
    author TEXT,
    timestamp TIMESTAMP,
    parent_commits TEXT  -- Comma-separated list of parent commit hashes
);

-- Commit files relationship
CREATE TABLE commit_files (
    commit_hash TEXT,
    file_hash TEXT,
    logical_path TEXT,
    FOREIGN KEY (commit_hash) REFERENCES commits(hash),
    FOREIGN KEY (file_hash) REFERENCES files(hash),
    PRIMARY KEY (commit_hash, logical_path)
);

-- Access logs
CREATE TABLE access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash TEXT,
    user TEXT,
    timestamp TIMESTAMP,
    purpose TEXT,
    FOREIGN KEY (file_hash) REFERENCES files(hash)
);

-- Processing logs
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    parameters TEXT,  -- JSON string of parameters
    timestamp TIMESTAMP,
    user TEXT
);

-- Processing inputs
CREATE TABLE processing_inputs (
    processing_id INTEGER,
    file_hash TEXT,
    FOREIGN KEY (processing_id) REFERENCES processing_logs(id),
    FOREIGN KEY (file_hash) REFERENCES files(hash),
    PRIMARY KEY (processing_id, file_hash)
);

-- Processing outputs
CREATE TABLE processing_outputs (
    processing_id INTEGER,
    file_hash TEXT,
    FOREIGN KEY (processing_id) REFERENCES processing_logs(id),
    FOREIGN KEY (file_hash) REFERENCES files(hash),
    PRIMARY KEY (processing_id, file_hash)
);

-- File lineage relationships
CREATE TABLE file_lineage (
    source_file_hash TEXT,
    derived_file_hash TEXT,
    transformation_id INTEGER,
    FOREIGN KEY (source_file_hash) REFERENCES files(hash),
    FOREIGN KEY (derived_file_hash) REFERENCES files(hash),
    FOREIGN KEY (transformation_id) REFERENCES processing_logs(id),
    PRIMARY KEY (source_file_hash, derived_file_hash, transformation_id)
);

-- Transformations table for storing information about how files were derived
CREATE TABLE transformations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    transformation_type TEXT,
    parameters TEXT,  -- JSON string of transformation parameters
    code_reference TEXT,  -- Optional reference to code that performed the transformation
    timestamp TIMESTAMP,
    user TEXT
);
```

## 4. API Design

### 4.1 Python API

The Python API will be designed for ease of use while providing access to all features:

```python
# Basic usage
from kirin import Repository

# Initialize repository
repo = Repository("path/to/repo", backend="local")

# Create a dataset
dataset = repo.create_dataset("my_dataset", "Description of my dataset")

# Add files and commit in a single operation
commit_hash = dataset.commit(
    add_files=["file1.csv", "file2.json"],
    commit_message="Initial commit"
)

# Checkout a specific version
dataset.checkout(commit_hash)

# Get file paths for current version
files = dataset.list_files()

# Access a file (records access in usage db)
with repo.Path("file1.csv").open(purpose="data analysis") as f:
    data = f.read()

# Stream-based access for large files
with repo.Path("large_file.parquet").open_stream() as stream:
    # Process stream incrementally
    for chunk in iter(lambda: stream.read(1024*1024), b''):
        process_chunk(chunk)

# Memory-mapped access for efficient random access to large files
with repo.Path("large_array.npy").mmap() as mm:
    # Direct memory access without loading entire file
    array_view = np.frombuffer(mm, dtype=np.float32)
    result = array_view[1000:2000].sum()

# Track processing with automatic input/output detection
# No need to explicitly declare inputs and outputs
with repo.track_processing(
    description="Normalized data",
    parameters={"method": "min-max"}
) as ctx:
    # Read input data - automatically tracked as input
    input_path = repo.Path("my_dataset/file1.csv")
    input_data = pd.read_csv(input_path)

    # Process data - this is your actual transformation code
    processed_data = normalize(input_data, method="min-max")

    # Write output data - automatically tracked as output
    output_path = repo.Path("processed/output.csv")
    processed_data.to_csv(output_path, index=False)

    # Optionally record additional metadata about the transformation
    ctx.add_metadata("rows_processed", len(processed_data))
    ctx.add_metadata("columns", list(processed_data.columns))
    ctx.add_code_reference(__file__)

# Another example with multiple inputs and outputs
with repo.track_processing(
    description="Join customer and order data",
    parameters={"join_type": "inner"}
) as ctx:
    # Reading files automatically tracks them as inputs
    customers = pd.read_csv(repo.Path("customers.csv"))
    orders = pd.read_csv(repo.Path("orders.csv"))

    # Join data
    merged = customers.merge(orders, on="customer_id", how="inner")

    # Generate summary
    summary = merged.groupby("customer_id").agg({"order_amount": "sum"})

    # Writing files automatically tracks them as outputs
    merged.to_csv(repo.Path("customer_orders.csv"), index=False)
    summary.to_csv(repo.Path("summary.csv"))

    # Record the number of rows in each output
    ctx.add_metadata("customer_orders_rows", len(merged))
    ctx.add_metadata("summary_rows", len(summary))

# For convenience, you can also explicitly declare inputs/outputs if desired
# This is useful for cases where files are accessed outside the context manager
with repo.track_processing(
    inputs=["external/data.csv"],  # File accessed outside of context
    description="Process external data"
) as ctx:
    # Files accessed via Path are still automatically tracked
    output_path = repo.Path("results/output.csv")

    # Process external data that was accessed earlier
    # ...

    # Write results
    results.to_csv(output_path, index=False)

# Path objects support standard pathlib operations
data_dir = repo.Path("data")
for csv_file in data_dir.glob("*.csv"):
    # Processing each CSV file
    print(f"Processing {csv_file.name}")

    # Path objects can be used with pandas, numpy, etc. directly
    df = pd.read_csv(csv_file)
    # ...

# Query file lineage
ancestors = repo.get_file_ancestors("processed/result.csv")
descendants = repo.get_file_descendants("raw/input.csv")

# Visualize lineage
repo.visualize_lineage("processed/result.csv", depth=2)
```

### 4.1.1 Path-Based API with Automatic Tracking

Kirin provides a pathlib-compatible API that automatically tracks file accesses:

1. **Repository Path Objects**:
   - `repo.Path(path)` creates a Path-like object that behaves like `pathlib.Path`
   - These paths automatically track access patterns during data processing
   - The full pathlib API is supported: `.name`, `.suffix`, `.parent`, etc.

2. **Access Tracking Methods**:
   - `path.open(mode="r")` - Opens file and tracks as input (mode="r") or output (mode="w")
   - `path.read_text()`, `path.read_bytes()` - Read and track as input
   - `path.write_text()`, `path.write_bytes()` - Write and track as output
   - `path.open_stream()` - Stream-based access with tracking
   - `path.mmap()` - Memory-mapped access with tracking

3. **Access Intent Detection**:
   - The system automatically determines if a path is being used as input or output
   - Reading operations record the file as an input
   - Writing operations record the file as an output
   - Files opened in append mode are recorded as both input and output

4. **File Operation Methods**:
   - `path.copy_to(target)` - Copy with automatic tracking of source (input) and target (output)
   - `path.move_to(target)` - Move with automatic tracking
   - `path.exists()`, `path.is_file()`, `path.is_dir()` - Standard path checks

5. **Directory Operations**:
   - `path.mkdir(parents=True, exist_ok=True)` - Create directories
   - `path.iterdir()` - List directory contents
   - `path.glob("*.csv")` - Pattern matching for files
   - `path.rglob("**/*.csv")` - Recursive pattern matching

### 4.1.2 Input/Output Detection Mechanisms

Kirin employs several complementary strategies to determine whether a Path is being used as input or output:

1. **Explicit Mode Declaration**:

   ```python
   # Explicitly mark as input
   input_path = repo.Path("data.csv", access_type="input")

   # Explicitly mark as output
   output_path = repo.Path("results.csv", access_type="output")

   # Mark as both input and output
   inout_path = repo.Path("modify.csv", access_type="both")
   ```

2. **Method-Based Detection**:

   ```python
   # These methods clearly indicate reading (input)
   data1 = path.read_text()
   data2 = path.read_bytes()

   # These methods clearly indicate writing (output)
   path.write_text("content")
   path.write_bytes(b"content")
   ```

3. **Context Detection via File Opening Mode**:

   ```python
   # Reading modes mark as input
   with path.open("r") as f:  # or "rb"
       data = f.read()

   # Writing modes mark as output
   with path.open("w") as f:  # or "wb"
       f.write("content")

   # Append modes mark as both input and output
   with path.open("a+") as f:
       f.read()
       f.write("more content")
   ```

4. **Library Function Inspection**:

   ```python
   # pandas.read_csv is known to read files (input)
   df = pd.read_csv(path)  # Automatically tracked as input

   # pandas.DataFrame.to_csv is known to write files (output)
   df.to_csv(path)  # Automatically tracked as output
   ```

5. **Code Execution Flow Analysis**:
   - If a path is only passed to a function but never created or modified, it's likely an input
   - If a path doesn't exist before an operation but exists after, it's likely an output
   - If a path's modification time changes, it's likely an output

6. **Explicit Context Override**:

   ```python
   # Manually register as input when automatic detection might fail
   with ctx.register_input(path):
       custom_read_function(str(path))

   # Manually register as output when automatic detection might fail
   with ctx.register_output(path):
       custom_write_function(str(path))
   ```

7. **Fallback Heuristics**:
   - Files that exist before processing are assumed to be inputs if accessed
   - New files created during processing are assumed to be outputs
   - File content hash changes indicate the file is an output

### 4.1.3 Implementation Example

Here's a detailed example demonstrating the input/output detection in practice:

```python
with repo.track_processing(
    description="Process customer data"
) as ctx:
    # Case 1: Direct reading method - detected as input
    config = repo.Path("config.json").read_text()

    # Case 2: Direct writing method - detected as output
    repo.Path("log.txt").write_text("Processing started")

    # Case 3: Opening with mode - detected as input
    with repo.Path("customers.csv").open("r") as f:
        customers_csv = f.read()

    # Case 4: Library function detection - detected as input
    customers_df = pd.read_csv(repo.Path("customers.csv"))

    # Case 5: Library function detection - detected as output
    processed = customers_df.query("status == 'active'")
    processed.to_csv(repo.Path("active_customers.csv"))

    # Case 6: File doesn't exist before - detected as output
    summary_path = repo.Path("summary.json")
    with summary_path.open("w") as f:
        json.dump({"count": len(processed)}, f)

    # Case 7: Explicit override when automatic detection might fail
    external_path = repo.Path("external_data.dat")
    with ctx.register_input(external_path):
        custom_reader(str(external_path))

    # Case 8: Access type specified directly
    template = repo.Path("report_template.html", access_type="input")
    report = repo.Path("final_report.html", access_type="output")

    # The system now knows:
    # - Inputs: config.json, customers.csv, external_data.dat, report_template.html
    # - Outputs: log.txt, active_customers.csv, summary.json, final_report.html
```

### 4.1.4 Handling Edge Cases

The system includes mechanisms to handle complex scenarios:

1. **External Library Calls**:
   - The system maintains an extensible registry of known library functions and their access patterns
   - For example, it knows that `pandas.read_csv()` reads files and `to_csv()` writes files

2. **Cases with Unclear Intent**:
   - If intent cannot be determined automatically, a warning is logged
   - Files with undetermined access are not included in lineage tracking
   - Developers can use explicit registration to clarify intent in these cases

3. **Files Used Both as Input and Output**:
   - When a file is read and then modified, it's treated as two distinct entities in the lineage graph
   - The input version (original content hash) is recorded as a source
   - The output version (new content hash) is recorded as a derived file
   - This maintains a clean directed acyclic graph with no self-references
   - Each file modification results in a new content hash and explicit commit
   - If a file is modified without changing its content (same hash), no lineage connection is created

4. **Content-Based Versioning Example**:

   ```python
   with repo.track_processing(
       description="Update metadata in CSV"
   ) as ctx:
       # Read from version A of the file (hash1)
       data_path = repo.Path("data.csv")  # Automatically tracked as input
       df = pd.read_csv(data_path)

       # Modify the data
       df['processed'] = True

       # Write back to the same logical path
       # This creates version B of the file (hash2)
       df.to_csv(data_path, index=False)  # Automatically tracked as output

       # Behind the scenes:
       # 1. Original file (hash1) is recorded as input
       # 2. Modified file (hash2) is recorded as output
       # 3. A lineage link is created from hash1 to hash2
       # 4. The logical path "data.csv" now points to hash2
   ```

5. **Temporary Files**:
   - Files created and deleted within the same processing context are not tracked in the permanent lineage graph
   - They can optionally be included in detailed processing logs if desired

### 4.2 CLI Design

The command-line interface will mirror Git's familiar commands but with some streamlining:

```bash
# Initialize
gitdata init --backend=s3 --config=s3://bucket/config.json

# Create dataset
gitdata dataset create my_dataset "Description of my dataset"

# Add files and commit in a single command
gitdata commit my_dataset -a file1.csv file2.json -m "Initial commit"

# Add and remove files in a single commit
gitdata commit my_dataset -a new_file.csv -r old_file.csv -m "Replace old file with new"

# To remove files only
gitdata commit my_dataset -r obsolete_file.csv -m "Remove obsolete file"

# List datasets
gitdata list-datasets

# Show dataset info
gitdata show my_dataset

# Checkout version
gitdata checkout my_dataset <commit-hash>

# Get file (records access)
gitdata get my_dataset/file1.csv --purpose="data analysis"

# Show history
gitdata log my_dataset

# Show usage
gitdata usage my_dataset/file1.csv

# Execute transformation scripts with lineage tracking
gitdata run transform.py -m "Transform data" --params '{"method": "normalize"}'

# Query lineage
gitdata lineage ancestors processed/result.csv
gitdata lineage descendants raw/data.csv

# Visualize lineage (outputs a DOT file or renders directly if graphviz is installed)
gitdata lineage visualize processed/result.csv --depth 3 --output lineage.svg
```

## 5. Backend Support

### 5.1 Local Filesystem Backend

The local filesystem backend will store files directly on disk, making it ideal for development and small-scale projects.

### 5.2 S3 Backend

The S3 backend will store data in an Amazon S3 bucket, providing scalable and durable storage for larger projects.

### 5.3 Cloud Storage Backends

Additional backends will be implemented for:

- Google Drive
- Dropbox
- Microsoft SharePoint
- Azure Blob Storage

### 5.4 Custom Backend Implementation

Users can implement custom storage backends by implementing the `StorageBackend` protocol.

## 6. Security and Access Control

### 6.1 Data Encryption

Data can be encrypted at rest and in transit using industry-standard encryption algorithms.

### 6.2 Access Control

Access control will leverage the underlying storage backend's mechanisms where available.

### 6.3 Audit Logging

All access to data will be recorded in the usage tracking database, providing a complete audit trail.

## 7. Performance Considerations

### 7.1 Zero-Copy Architecture

Kirin is designed with a zero-copy philosophy wherever possible:

- **Memory-mapped files**: When working with local files, memory mapping is used to avoid loading entire files into memory
- **Streaming operations**: For operations on large files, streaming interfaces are provided to process data incrementally
- **Direct transfers**: When copying between storage backends, data is streamed directly without loading into application memory
- **In-place transformations**: Where possible, files are modified in-place rather than creating full copies
- **Reference-based operations**: Operations like checkouts use references instead of copying file content

### 7.2 Caching

Local caching of frequently accessed files will improve performance when working with remote storage backends.

### 7.3 Lazy Loading

Content will be loaded only when needed, reducing unnecessary network traffic.

### 7.4 Batch Operations

Operations will be batched where possible to reduce overhead when working with remote storage backends.

### 7.5 Optimized Hashing

To improve performance when hashing large files:

- Incremental hashing is used for streaming data
- Parallel chunk processing for multi-core systems
- Optional content-based chunking for improved deduplication

## 8. Future Extensions

### 8.1 Web Interface

A lightweight web interface could be developed to browse datasets and view usage statistics.

### 8.2 Integration with ML Frameworks

Direct integration with popular ML frameworks like PyTorch and TensorFlow can streamline data loading.

### 8.3 Distributed Processing

Support for distributed processing frameworks like Apache Spark could be added to handle large-scale data processing.

### 8.4 Advanced Lineage Visualization

Enhanced visualization tools could be developed to explore complex lineage graphs, including interactive web-based visualizations and notebook integrations.

### 8.5 Automated Lineage Inference

Machine learning techniques could be applied to automatically infer lineage relationships between files based on content similarity and access patterns.

### 8.6 Native Format Handlers

Format-specific handlers could be developed to enable operations directly on file contents without full deserialization:

- Parquet/Arrow operations for columnar data
- HDF5/Zarr for array data
- SQLite for tabular data

These handlers would leverage the zero-copy architecture to perform operations like filtering, projection, and aggregation directly on the storage format.

### 8.7 Zero-copy Data Processing Pipelines

Specialized data processing pipelines could be implemented to leverage the zero-copy architecture for common data transformations:

- Filtering and transformation operations
- Joining and merging datasets
- Aggregation and grouping

## 9. Implementation Plan

### 9.1 Phase 1: Core Architecture

- Implement storage layer with local filesystem backend
- Implement content addressing and versioning
- Create basic Python API

### 9.2 Phase 2: Usage and Lineage Tracking

- Implement SQLite database schema
- Add usage tracking functionality
- Implement lineage tracking and querying capabilities
- Create basic reporting and visualization tools

### 9.3 Phase 3: Additional Backends

- Implement S3 backend
- Add support for other cloud storage providers
- Create backend selection and configuration system

### 9.4 Phase 4: CLI and Documentation

- Implement command-line interface
- Create comprehensive documentation
- Develop tutorials and examples

### 9.5 Phase 5: Testing and Optimization

- Comprehensive testing across all backends
- Performance optimization
- Security auditing

## 10. Conclusion

Kirin's redesigned architecture provides a robust, flexible system for data versioning that meets all the specified requirements:

1. It supports multiple storage backends
2. It uses content-addressed storage for integrity and deduplication
3. It enables building data catalogs
4. It operates in a serverless manner
5. It tracks all data usage in a structured format
6. It employs zero-copy operations wherever possible, optimizing for performance and resource efficiency

This design document outlines a path forward to implementing a system that will address the shortcomings of the current implementation while maintaining its strengths.
