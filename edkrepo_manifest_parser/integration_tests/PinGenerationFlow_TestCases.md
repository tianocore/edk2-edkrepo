# Test Cases for `PinGenerationFlow` Integration Tests

## Test Cases

### TestPinGenerationFlow
Integration tests for generating pin files.

#### 1. Pin XML File Created With Correct Structure
- **Test Name**: `test_generate_pin_xml_from_manifest`
- **Description**: When generating a pin XML file from a manifest with commit SHAs.
- **Expected Outcome**: Pin file is created with correct XML structure; all sources contain commit attributes.

#### 2. Pin JSON File Created And Parseable
- **Test Name**: `test_generate_pin_json_from_manifest`
- **Description**: When generating a pin JSON file from a manifest.
- **Expected Outcome**: Pin file is created in JSON format; data is parseable and contains expected keys.

#### 3. Pin Preserves All Manifest Metadata
- **Test Name**: `test_pin_file_preserves_manifest_metadata`
- **Description**: When generating a pin file from a manifest.
- **Expected Outcome**: Pin contains all original metadata fields (codename, description, remotes) from the manifest.

#### 4. Pin Replaces Branches With Commit SHAs
- **Test Name**: `test_pin_file_replaces_branches_with_commits`
- **Description**: When generating a pin file with specific commit SHAs.
- **Expected Outcome**: All sources contain 40-character hexadecimal commit SHAs instead of branch names.

#### 5. Pin Contains Only Specified Combination
- **Test Name**: `test_generate_pin_for_specific_combination`
- **Description**: When generating a pin file for a specific combination.
- **Expected Outcome**: Pin contains only sources for the specified combination with correct combination name attribute.

#### 6. Pin Includes Patchset Information
- **Test Name**: `test_pin_file_includes_patchsets`
- **Description**: When generating a pin from a manifest with patchsets.
- **Expected Outcome**: Pin file includes patchset information when present in the manifest.

#### 7. Generated Pin Loads And Validates
- **Test Name**: `test_load_and_validate_generated_pin`
- **Description**: When loading a generated pin file back as a ManifestXml.
- **Expected Outcome**: Pin is recognized as a pin file; sources are parseable with correct commit values.


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
