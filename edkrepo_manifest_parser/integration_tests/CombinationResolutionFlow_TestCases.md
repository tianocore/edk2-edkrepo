# Test Cases for `CombinationResolutionFlow` Integration Tests

## Test Cases

### TestCombinationResolutionFlow
Integration tests for resolving and managing manifest combinations.

#### 1. Combination Contains Description Attribute
- **Test Name**: `test_combination_has_description`
- **Description**: When accessing the description attribute of a combination object.
- **Expected Outcome**: Combination object contains description attribute with value 'Main combination'.

#### 2. Minimal Manifest Default And Current Match
- **Test Name**: `test_minimal_manifest_default_and_current_same`
- **Description**: When querying default_combo and current_combo from a minimal manifest.
- **Expected Outcome**: Both properties return the same value 'main'.

#### 3. All Sources Have Required Fields
- **Test Name**: `test_combination_sources_have_required_fields`
- **Description**: When retrieving sources for a combination.
- **Expected Outcome**: All returned sources contain non-null root, remote_name, and branch attributes.


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
