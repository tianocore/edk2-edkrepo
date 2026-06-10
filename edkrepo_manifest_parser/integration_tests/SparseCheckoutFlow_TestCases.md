# Test Cases for `SparseCheckoutFlow` Integration Tests

## Test Cases

### TestSparseCheckoutFlow
Integration tests for sparse checkout configuration and data retrieval from manifests.

#### 1. Returns Sparse Settings Object
- **Test Name**: `test_get_sparse_settings_from_manifest`
- **Description**: When accessing the sparse_settings property.
- **Expected Outcome**: Returns SparseSettings object.

#### 2. Settings Contains Sparse By Default Value
- **Test Name**: `test_sparse_settings_has_sparse_by_default_attribute`
- **Description**: When accessing the sparse_by_default attribute of sparse settings.
- **Expected Outcome**: Returns the configured boolean value.

#### 3. Returns List Of Sparse Data Objects
- **Test Name**: `test_get_sparse_data_from_manifest`
- **Description**: When accessing the sparse_data property.
- **Expected Outcome**: Returns list of SparseData objects with correct count.

#### 4. Sparse Data Attribute Has Correct Value
- **Test Name**: `test_sparse_data_has_attribute[combination]`
- **Description**: When accessing the combination attribute of sparse data (parametrized case).
- **Expected Outcome**: Returns the combination name matching the manifest configuration.

#### 5. Sparse Data Attribute Has Correct Value
- **Test Name**: `test_sparse_data_has_attribute[remote_name]`
- **Description**: When accessing the remote_name attribute of sparse data (parametrized case).
- **Expected Outcome**: Returns the remote name matching the manifest configuration.

#### 6. Sparse Data List Attribute Has Correct Count
- **Test Name**: `test_sparse_data_has_list_attribute[always_include]`
- **Description**: When accessing the always_include attribute of sparse data (parametrized case).
- **Expected Outcome**: Returns a list of paths with correct count.

#### 7. Sparse Data List Attribute Has Correct Count
- **Test Name**: `test_sparse_data_has_list_attribute[always_exclude]`
- **Description**: When accessing the always_exclude attribute of sparse data (parametrized case).
- **Expected Outcome**: Returns a list with correct count.

#### 8. Always Include Contains All Configured Paths
- **Test Name**: `test_sparse_data_always_include_contains_correct_paths`
- **Description**: When checking paths in the always_include list.
- **Expected Outcome**: List contains all paths specified in the manifest configuration.

#### 9. Returns Only Matching Combination Entries
- **Test Name**: `test_filter_sparse_data_by_combination`
- **Description**: When filtering sparse data entries by combination name.
- **Expected Outcome**: Returns only entries where combination matches the specified name.

#### 10. Returns Only Matching Remote Entries
- **Test Name**: `test_filter_sparse_data_by_remote`
- **Description**: When filtering sparse data entries by remote name.
- **Expected Outcome**: Returns only entries where remote_name matches the specified name.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\integration_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
