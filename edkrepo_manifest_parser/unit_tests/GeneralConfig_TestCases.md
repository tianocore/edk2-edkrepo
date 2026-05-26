# Test Cases for `_GeneralConfig` Class

## Test Cases

### TestGeneralConfigInit
Tests `_GeneralConfig.__init__` which reads four optional child elements from a `<GeneralConfig>` XML element, defaulting each to `None` when absent.

#### 1. Sets `pin_path` When PinPath Present
- **Test Name**: `test_init_sets_pin_path_when_present`
- **Description**: When the `PinPath` child element is present with text content.
- **Expected Outcome**: `self.pin_path` is set to the element's text value.

#### 2. Sets `pin_path` to None When PinPath Absent
- **Test Name**: `test_init_field_defaults_to_none_when_absent[pin_path_absent]`
- **Description**: When the `PinPath` child element is absent (i.e., `find('PinPath')` returns `None`).
- **Expected Outcome**: `self.pin_path` is `None`.

#### 3. Sets `default_combo` When DefaultCombo Present
- **Test Name**: `test_init_sets_default_combo_when_present`
- **Description**: When the `DefaultCombo` child element is present with a `combination` attribute.
- **Expected Outcome**: `self.default_combo` is set to the `combination` attribute value.

#### 4. Sets `default_combo` to None When DefaultCombo Absent
- **Test Name**: `test_init_field_defaults_to_none_when_absent[default_combo_absent]`
- **Description**: When the `DefaultCombo` child element is absent.
- **Expected Outcome**: `self.default_combo` is `None`.

#### 5. Sets `curr_combo` When CurrentClonedCombo Present
- **Test Name**: `test_init_sets_curr_combo_when_present`
- **Description**: When the `CurrentClonedCombo` child element is present with a `combination` attribute.
- **Expected Outcome**: `self.curr_combo` is set to the `combination` attribute value.

#### 6. Sets `curr_combo` to None When CurrentClonedCombo Absent
- **Test Name**: `test_init_field_defaults_to_none_when_absent[curr_combo_absent]`
- **Description**: When the `CurrentClonedCombo` child element is absent.
- **Expected Outcome**: `self.curr_combo` is `None`.

#### 7. Sets `source_manifest_repo` When SourceManifestRepository Present
- **Test Name**: `test_init_sets_source_manifest_repo_when_present`
- **Description**: When the `SourceManifestRepository` child element is present with a `manifest_repo` attribute.
- **Expected Outcome**: `self.source_manifest_repo` is set to the `manifest_repo` attribute value.

#### 8. Sets `source_manifest_repo` to None When SourceManifestRepository Absent
- **Test Name**: `test_init_field_defaults_to_none_when_absent[source_manifest_repo_absent]`
- **Description**: When the `SourceManifestRepository` child element is absent.
- **Expected Outcome**: `self.source_manifest_repo` is `None`.

### TestGeneralConfigTuple
Tests `_GeneralConfig.tuple` which returns a `GeneralConfig` namedtuple with all four field values.

#### 1. Returns Correct GeneralConfig Namedtuple
- **Test Name**: `test_tuple_returns_correct_general_config_namedtuple`
- **Description**: When all four optional children are present.
- **Expected Outcome**: `tuple` returns a `GeneralConfig(default_combo, current_combo, pin_path, source_manifest_repo)` with the correct values.


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
