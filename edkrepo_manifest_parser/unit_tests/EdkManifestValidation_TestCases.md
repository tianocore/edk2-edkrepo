# Test Cases for `edk_manifest_validation` Module

## Test Cases

### TestCollectFileValidationResults
Tests the `_collect_file_validation_results` helper which validates parsing and codename for a single manifest file.

#### 1. Parsing Succeeds — Codename Validation Included
- **Description**: When `validate_parsing` returns success and `_manifest_xmldata` is populated.
- **Expected Outcome**: The result list contains a passing PARSING tuple followed by a passing CODENAME tuple from `validate_codename`.

#### 2. Parsing Fails — Hardcoded Codename Error Appended
- **Description**: When `validate_parsing` returns failure and `_manifest_xmldata` is `None`.
- **Expected Outcome**: The result list contains a failing PARSING tuple followed by a hardcoded `('CODENAME', False, 'Cannot process codename validation')` tuple.

### TestResolveProjectManifestPath
Tests the `_resolve_project_manifest_path` helper which computes the absolute path to a project manifest file.

#### 1. Returns Normalized Joined Path
- **Description**: Given a `CiIndexXml` mock whose `get_project_xml` returns a relative path, and a `global_manifest_directory`.
- **Expected Outcome**: Returns `os.path.join(global_manifest_directory, os.path.normpath(relative_path))`.

### TestCollectProjectValidationResults
Tests the `_collect_project_validation_results` helper which runs parsing, codename, and deduplication validations for one project.

#### 1. All Validations Pass — Three Results Returned
- **Description**: When all three `ValidateManifest` methods return passing tuples.
- **Expected Outcome**: The result list has exactly three entries, all with a `True` status.

#### 2. Parsing Fails — Three Results Still Returned
- **Description**: When `validate_parsing` returns a failure tuple; the other validators still run.
- **Expected Outcome**: The result list has exactly three entries; the first has `False` status.

### TestValidateManifestFiles
Tests `validate_manifestfiles` which validates every manifest file in a provided list.

#### 1. Empty List Returns Empty Dict
- **Description**: Called with an empty `manifestfile_list`.
- **Expected Outcome**: Returns an empty dictionary; `_collect_file_validation_results` is never called.

#### 2. Single Manifest — Helper Called Once
- **Description**: Called with a list containing one manifest filepath.
- **Expected Outcome**: Returns a dict with one entry keyed by the filepath whose value is the list returned by `_collect_file_validation_results`.

#### 3. Multiple Manifests — Helper Called for Each
- **Description**: Called with a list containing two manifest filepaths.
- **Expected Outcome**: Returns a dict with two entries; `_collect_file_validation_results` is called once per filepath with the correct argument.

### TestValidateManifestRepo
Tests `validate_manifestrepo` which validates all manifest files referenced by `CiIndex.xml`.

#### 1. Without Archived — Only Active Projects Processed
- **Description**: Called with `verify_archived=False`; `CiIndex.xml` contains one active project and one archived project.
- **Expected Outcome**: Returns a dict with one entry; `archived_project_list` is not included.

#### 2. With Archived — Active and Archived Projects Processed
- **Description**: Called with `verify_archived=True`; `CiIndex.xml` contains one active project and one archived project.
- **Expected Outcome**: Returns a dict with two entries, one per project.

### TestGetManifestValidationStatus
Tests `get_manifest_validation_status` which verifies the validation status of all manifest files; parametrized over all-pass, one-fail, and empty-dict inputs.

#### 1. All Results Pass — Returns False
- **Description**: Every result tuple in the dict has a `True` status.
- **Expected Outcome**: Returns `False`.

#### 2. One Result Fails — Returns True
- **Description**: At least one result tuple in the dict has a `False` status.
- **Expected Outcome**: Returns `True`.

#### 3. Empty Dict — Returns False
- **Description**: Called with an empty dictionary.
- **Expected Outcome**: Returns `False`.

### TestPrintManifestErrors
Tests `print_manifest_errors` which prints error details for every failed validation result.

#### 1. Prints Header and Details for Each Failure
- **Description**: The dict contains one manifest file with one failing result and one passing result.
- **Expected Outcome**: `VERIFY_ERROR_HEADER` is printed once, followed by three print calls for the failing result (file name, error type, error message); the passing result is skipped.

#### 2. All Passing — Only Header Printed
- **Description**: The dict contains one manifest file where all results are passing.
- **Expected Outcome**: `print` is called exactly once with `VERIFY_ERROR_HEADER`; no error detail lines are printed.


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
