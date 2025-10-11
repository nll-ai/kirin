# Catalog Landing Page Commit Count Bug Fix

## Bug Description

**Issue**: Datasets on the catalog landing page (`/catalog/{catalog_id}`) displayed "0 commits" even when they had actual commits.

**Symptoms**:
- Catalog landing page showed "0 commits" for all datasets
- Individual dataset pages showed correct commit counts (e.g., "2 commits")
- Misleading user experience - users thought datasets were empty

**Root Cause**: The `list_datasets()` route handler in `kirin/web/app.py` was hardcoding commit counts to 0 instead of loading actual dataset data.

## Technical Details

### Problematic Code (Before Fix)

```python
# kirin/web/app.py lines 245-257
datasets = []
for dataset_name in dataset_names:
    datasets.append(
        {
            "name": dataset_name,
            "description": "",  # Will load when viewing
            "commit_count": 0,  # Will load when viewing ← HARDCODED TO 0
            "current_commit": None,  # Will load when viewing
            "total_size": 0,  # Will load when viewing
            "last_updated": None,  # Will load when viewing
        }
    )
```

### Root Cause Analysis

1. **Performance Optimization Gone Wrong**: Code was designed to avoid "expensive operations" by not loading dataset objects
2. **Incomplete Lazy Loading**: Comments suggested lazy loading was intended but never implemented
3. **Hardcoded Values**: All dataset metadata was hardcoded to default/empty values

### Fix Implementation

```python
# kirin/web/app.py lines 245-257 (After Fix)
datasets = []
for dataset_name in dataset_names:
    dataset = kirin_catalog.get_dataset(dataset_name)  # Load dataset object
    datasets.append(
        {
            "name": dataset_name,
            "description": dataset.description,
            "commit_count": len(dataset.history()),  # Calculate actual count
            "current_commit": dataset.current_commit.hash if dataset.current_commit else None,
            "total_size": 0,  # Can calculate if needed
            "last_updated": dataset.current_commit.timestamp.isoformat() if dataset.current_commit else None,
        }
    )
```

## Fix Benefits

- **Accurate Information**: Users see correct commit counts
- **Better UX**: Current commit hashes and timestamps displayed
- **Consistent Behavior**: Landing page matches individual dataset pages
- **Minimal Performance Impact**: Slight increase in page load time for accurate data

## Testing

### Test Coverage

The fix includes comprehensive tests in `tests/web_ui/test_catalog_commit_count_bug.py`:

1. **Basic Functionality**: Datasets with commits show correct counts
2. **Empty Datasets**: Datasets without commits show 0 correctly
3. **Mixed Scenarios**: Catalogs with both empty and populated datasets
4. **Performance**: Multiple datasets don't cause performance issues

### Test Execution

```bash
# Run the specific bug fix tests
pixi run -e tests python -m pytest tests/web_ui/test_catalog_commit_count_bug.py -v

# Run all web UI tests
pixi run -e tests python -m pytest tests/web_ui/ -v
```

## Prevention

### How to Avoid Similar Bugs

1. **Avoid Hardcoded Values**: Never hardcode data that should be calculated
2. **Complete Lazy Loading**: If implementing lazy loading, ensure it's actually implemented
3. **Test Data Accuracy**: Always test that displayed data matches actual data
4. **Performance vs Accuracy**: Balance performance optimizations with data accuracy

### Code Review Checklist

- [ ] Are displayed values calculated from actual data?
- [ ] Do performance optimizations maintain data accuracy?
- [ ] Are there tests that verify displayed data matches actual data?
- [ ] Are lazy loading features actually implemented?

## Related Files

- **Bug Location**: `kirin/web/app.py` lines 245-257
- **Tests**: `tests/web_ui/test_catalog_commit_count_bug.py`
- **Template**: `kirin/web/templates/datasets.html` (displays the data)
- **Individual Dataset View**: `kirin/web/app.py` lines 507-563 (shows correct implementation)

## Impact

- **User Experience**: Significantly improved - users see accurate information
- **Performance**: Minimal impact - slight increase in page load time
- **Maintenance**: Better code - no more hardcoded values
- **Testing**: Comprehensive test coverage prevents regression
