# Test Cases for `ComboCommand` Class

## Test Cases

### TestRunCommand
Tests `ComboCommand.run_command`, which lists the combinations available in the workspace manifest.

#### 1. Run Command Prints Current Combo With Marker
- **Test Name**: `test_run_command_prints_current_combo_with_marker`
- **Description**: When printing the active combination.
- **Expected Outcome**: It is printed using the `CURRENT_COMBO` format.

#### 2. Run Command Non Current Combo Printed As Regular
- **Test Name**: `test_run_command_non_current_combo_printed_as_regular`
- **Description**: When a combination is not the current combo.
- **Expected Outcome**: It is printed using the `COMBO` format.

#### 3. Run Command Archived Flag Includes Archived Combos
- **Test Name**: `test_run_command_archived_flag_includes_archived_combos`
- **Description**: When `args.archived` is `True`.
- **Expected Outcome**: Archived combinations are printed using the `ARCHIVED_COMBO` format.

#### 4. Run Command Current Combo Not In Combinations Is Appended
- **Test Name**: `test_run_command_current_combo_not_in_combinations_is_appended`
- **Description**: When `current_combo` is absent from the combinations list.
- **Expected Outcome**: It is appended and displayed as current.

#### 5. Run Command Verbose Calls Find Source Manifest Repo
- **Test Name**: `test_run_command_verbose_calls_find_source_manifest_repo`
- **Description**: When `verbose` is `True`.
- **Expected Outcome**: `find_source_manifest_repo` is called with the manifest and config keys.

### TestIdentifyComboSources
Tests `ComboCommand._identify_combo_sources`, the private helper that resolves repo sources for a combo, including the pin-file resolution path.

#### 1. Identify Combo Sources Pin Loads From Pin Manifest
- **Test Name**: `test_identify_combo_sources_pin_loads_from_pin_manifest`
- **Description**: When the combo name contains `pin:`.
- **Expected Outcome**: Sources are loaded from the resolved pin manifest.

#### 2. Identify Combo Sources Regular Combo Returns Manifest Sources
- **Test Name**: `test_identify_combo_sources_regular_combo_returns_manifest_sources`
- **Description**: When the combo name is a non-pin combo.
- **Expected Outcome**: Sources are loaded directly from the manifest.

#### 3. Identify Combo Sources Pin Not Found Falls Back To Manifest
- **Test Name**: `test_identify_combo_sources_pin_not_found_falls_back_to_manifest`
- **Description**: When the pin file is not found.
- **Expected Outcome**: Sources fall back to the workspace manifest and a warning is emitted.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo\commands\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
