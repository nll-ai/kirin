# ADR-001: HashFS Integration Evaluation

**Date**: 2024-12-19
**Status**: Rejected
**Decision Makers**: GitData Development Team

## Context

GitData requires a robust content-addressed storage (CAS) system to support
data versioning, deduplication, and multi-backend storage. During architecture
evaluation, we considered integrating [HashFS](https://github.com/dgilland/hashfs),
a Python library for content-addressable file management.

## Decision

**We will NOT integrate HashFS into GitData.**

Instead, we will enhance our existing custom content-addressed storage
implementation with HashFS-inspired optimizations while maintaining our current
fsspec-based architecture.

## Rationale

### Why Not HashFS?

1. **Architectural Incompatibility**
   - HashFS does not implement fsspec interface
   - Would require complete rewrite of storage layer
   - Loss of multi-backend support (S3, GCS, Azure, etc.)

2. **Feature Gaps**
   - No version control (commits, branches, merging)
   - No metadata tracking (commit messages, authors, timestamps)
   - No usage analytics or SQLite integration
   - Local filesystem only (no cloud scalability)

3. **Performance Limitations**
   - Memory-intensive (loads entire files)
   - No streaming support for large files
   - Single-threaded operations

4. **Maintenance Concerns**
   - Last commit 5 years ago (July 2019)
   - Appears unmaintained
   - No community support for fsspec integration

### Why Current Architecture is Better

1. **Multi-backend Support**
   - Native fsspec integration
   - Supports S3, GCS, Azure, local, HTTP, and more
   - Easy to add new backends

2. **Full Version Control**
   - Git-like commits, branches, merging
   - Complete metadata tracking
   - Usage analytics and lineage tracking

3. **Performance Optimized**
   - Streaming operations for large files
   - Memory-efficient file handling
   - Optimized for data science workflows

4. **Feature Complete**
   - SQLite usage tracking
   - Web UI for dataset management
   - CLI and programmatic API
   - Serverless architecture

## Alternatives Considered

### Option 1: Full HashFS Integration

- **Pros**: Proven CAS implementation, automatic deduplication
- **Cons**: Complete architectural rewrite, loss of critical features
- **Decision**: Rejected - too much risk and effort

### Option 2: Hybrid Architecture

- **Pros**: Best of both worlds, local deduplication
- **Cons**: Complex implementation, maintenance overhead
- **Decision**: Rejected - unnecessary complexity

### Option 3: Enhance Current System ✅

- **Pros**: Maintains all features, incremental improvement
- **Cons**: Requires custom implementation
- **Decision**: **Selected** - optimal balance of features and effort

## Implementation Plan

### Phase 1: Add Deduplication

```python
def commit_with_dedup(self, files: List[str]) -> str:
    """Commit files with automatic deduplication."""
    for file_path in files:
        hash_hex = self._hash_file(file_path)
        if not self._file_exists(hash_hex):
            self._store_file(file_path, hash_hex)
        self._add_to_commit(hash_hex)
```

### Phase 2: Optimize Directory Structure

```python
def _get_nested_path(self, hash_hex: str) -> str:
    """Get nested directory path for hash (HashFS-inspired)."""
    return f"{hash_hex[:2]}/{hash_hex[2:4]}/{hash_hex[4:]}"
```

### Phase 3: Add Repair Capabilities

```python
def repair_storage(self) -> Dict[str, Any]:
    """Repair and validate storage integrity."""
    # Implementation details...
```

## Consequences

### Positive

- **Maintains architecture**: No disruption to existing features
- **Adds optimizations**: Deduplication, directory nesting, repair
- **Preserves capabilities**: Multi-backend, versioning, metadata
- **Incremental improvement**: Low-risk enhancement

### Negative

- **Custom implementation**: Requires development effort
- **No community support**: HashFS has established patterns
- **Maintenance burden**: Need to maintain custom CAS system

### Risks

- **Performance**: Need to ensure optimizations don't impact performance
- **Compatibility**: Must maintain fsspec compatibility
- **Testing**: Need comprehensive testing of new features

## Monitoring

We will monitor:

- **Performance metrics**: File storage/retrieval times
- **Storage efficiency**: Deduplication effectiveness
- **User feedback**: Developer experience with new features
- **Ecosystem changes**: New CAS libraries with fsspec support

## References

- [HashFS Evaluation](./hashfs-evaluation.md) - Detailed technical analysis
- [Ecosystem Due Diligence](./ecosystem-diligence.md) - Broader ecosystem evaluation
- [GitData Design Document](./design.md) - Overall architecture
- [HashFS GitHub Repository](https://github.com/dgilland/hashfs) - Library documentation
