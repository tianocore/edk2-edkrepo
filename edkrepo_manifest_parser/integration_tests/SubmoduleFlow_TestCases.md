# Test Cases for `SubmoduleFlow` Integration Tests

## Test Cases

### TestSubmoduleFlow
Integration tests for submodule handling and configuration.

#### 1. Returns Submodule Paths For Combination
- **Test Name**: `test_get_submodule_init_paths_for_combo`
- **Description**: When requesting submodule init paths for a specific combination.
- **Expected Outcome**: Returns list of submodules configured for that combination; paths match expected values.

#### 2. Returns Only Submodules For Remote
- **Test Name**: `test_filter_submodules_by_remote`
- **Description**: When requesting submodule init paths filtered by remote name.
- **Expected Outcome**: Returns only submodules where remote_name matches the specified remote.

#### 3. Returns Submodules Matching Both Filters
- **Test Name**: `test_filter_submodules_by_remote_and_combo`
- **Description**: When requesting submodule init paths with both remote and combo filters.
- **Expected Outcome**: Returns only submodules matching both the remote and combination criteria.

#### 4. Returns Alternate Remote Configurations
- **Test Name**: `test_get_submodule_alternate_remotes`
- **Description**: When accessing submodule_alternate_remotes property.
- **Expected Outcome**: Returns list of alternate remote configurations; can query by remote name.

#### 5. Submodule Recursive Flag Correctly Parsed
- **Test Name**: `test_submodule_has_recursive_config[submodules/core]`
- **Description**: When accessing the recursive flag for the core submodule (parametrized case).
- **Expected Outcome**: Returns True as configured in the manifest.

#### 6. Submodule Recursive Flag Correctly Parsed
- **Test Name**: `test_submodule_has_recursive_config[submodules/utils]`
- **Description**: When accessing the recursive flag for the utils submodule (parametrized case).
- **Expected Outcome**: Returns False as configured in the manifest.

#### 7. Returns Empty List When No Submodules
- **Test Name**: `test_no_submodules_configured`
- **Description**: When querying submodule paths in a manifest with no submodules.
- **Expected Outcome**: Returns empty list for init paths and alternate remotes.

#### 8. Returns All Submodules Across Combinations
- **Test Name**: `test_submodule_init_paths_all_combos`
- **Description**: When requesting all submodule init paths without combo filter.
- **Expected Outcome**: Returns union of all submodule paths from all combinations.


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
