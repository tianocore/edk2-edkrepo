# Test Cases for the `_SparseSettings` Class

## Test Cases

### TestSparseSettingsInit
Tests `_SparseSettings.__init__` which parses the optional `sparseByDefault` attribute from a `<SparseSettings>` element, defaulting to `False` when absent.

#### 1. Sets sparse_by_default to False When sparseByDefault Absent
- **Description**: When the `sparseByDefault` attribute is absent.
- **Expected Outcome**: `self.sparse_by_default` is `False`.

#### 2. Sets sparse_by_default to True When sparseByDefault is "true"
- **Description**: When the `sparseByDefault` attribute is `"true"`.
- **Expected Outcome**: `self.sparse_by_default` is `True`.

#### 3. Sets sparse_by_default to False When sparseByDefault is "false"
- **Description**: When the `sparseByDefault` attribute is `"false"`.
- **Expected Outcome**: `self.sparse_by_default` is `False`.

### TestSparseSettingsTuple
Tests `_SparseSettings.tuple` which returns a `SparseSettings` namedtuple.

#### 1. Returns Correct SparseSettings Namedtuple
- **Description**: When `sparseByDefault` is `"true"`.
- **Expected Outcome**: `tuple` returns `SparseSettings(sparse_by_default=True)`.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
