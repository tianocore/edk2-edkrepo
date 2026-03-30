# Test Cases for `_GeneralConfig` Class

## Test Cases

### TestGeneralConfigInit
Tests `_GeneralConfig.__init__` which reads four optional child elements from a `<GeneralConfig>` XML element, defaulting each to `None` when absent.

#### 1. Sets `pin_path` When PinPath Present
- **Description**: When the `PinPath` child element is present with text content.
- **Expected Outcome**: `self.pin_path` is set to the element's text value.

#### 2. Sets `pin_path` to None When PinPath Absent
- **Description**: When the `PinPath` child element is absent (i.e., `find('PinPath')` returns `None`).
- **Expected Outcome**: `self.pin_path` is `None`.

#### 3. Sets `default_combo` When DefaultCombo Present
- **Description**: When the `DefaultCombo` child element is present with a `combination` attribute.
- **Expected Outcome**: `self.default_combo` is set to the `combination` attribute value.

#### 4. Sets `default_combo` to None When DefaultCombo Absent
- **Description**: When the `DefaultCombo` child element is absent.
- **Expected Outcome**: `self.default_combo` is `None`.

#### 5. Sets `curr_combo` When CurrentClonedCombo Present
- **Description**: When the `CurrentClonedCombo` child element is present with a `combination` attribute.
- **Expected Outcome**: `self.curr_combo` is set to the `combination` attribute value.

#### 6. Sets `curr_combo` to None When CurrentClonedCombo Absent
- **Description**: When the `CurrentClonedCombo` child element is absent.
- **Expected Outcome**: `self.curr_combo` is `None`.

#### 7. Sets `source_manifest_repo` When SourceManifestRepository Present
- **Description**: When the `SourceManifestRepository` child element is present with a `manifest_repo` attribute.
- **Expected Outcome**: `self.source_manifest_repo` is set to the `manifest_repo` attribute value.

#### 8. Sets `source_manifest_repo` to None When SourceManifestRepository Absent
- **Description**: When the `SourceManifestRepository` child element is absent.
- **Expected Outcome**: `self.source_manifest_repo` is `None`.

### TestGeneralConfigTuple
Tests `_GeneralConfig.tuple` which returns a `GeneralConfig` namedtuple with all four field values.

#### 1. Returns Correct GeneralConfig Namedtuple
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
