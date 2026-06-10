# Test Cases for `ValidationFlow` Integration Tests

## Test Cases

### TestValidationFlow
Integration tests for manifest validation functionality.

#### 1. Valid Manifests Pass Parsing Validation
- **Test Name**: `test_valid_manifest_parses_successfully[complete]`
- **Description**: When validating parsing of a complete, well-formed manifest with all optional sections (parametrized case).
- **Expected Outcome**: Returns validation result with status True and no error message.

#### 2. Valid Manifests Pass Parsing Validation
- **Test Name**: `test_valid_manifest_parses_successfully[minimal]`
- **Description**: When validating parsing of a minimal manifest with only required fields (parametrized case).
- **Expected Outcome**: Returns validation result with status True and no error message.

#### 3. Invalid Manifest Fails Parsing Validation
- **Test Name**: `test_validate_invalid_manifest_fails_parsing`
- **Description**: When validating parsing of a manifest with malformed XML structure.
- **Expected Outcome**: Returns validation result with status False and error message details.

#### 4. Matching Codename Passes Validation
- **Test Name**: `test_validate_codename_matches_project`
- **Description**: When validating codename against a matching project name.
- **Expected Outcome**: Returns validation result with status True and no error message.

#### 5. Mismatched Codename Fails Validation
- **Test Name**: `test_validate_codename_mismatches_project`
- **Description**: When validating codename against a non-matching project name.
- **Expected Outcome**: Returns validation result with status False and mismatch error message.

#### 6. Codename Validation Before Parsing Fails
- **Test Name**: `test_validate_codename_before_parsing_fails`
- **Description**: When attempting codename validation before calling validate_parsing.
- **Expected Outcome**: Returns validation result with status False indicating parsing is required first.

#### 7. Batch Validation Returns Results Dictionary
- **Test Name**: `test_validate_manifestfiles_returns_results_dict`
- **Description**: When validating a list of manifest files using the batch validation function.
- **Expected Outcome**: Returns dictionary mapping file paths to lists of validation results.


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
