# Test Cases for `edk_manifest_validation` Module

## Test Cases

### TestTryParseManifestXml
Tests `_try_parse_manifest_xml` which attempts to construct a `ManifestXml` from a file path and returns `(xmldata, None)` on success or `(None, exception)` on failure.

#### 1. Returns Xmldata on Success
- **Test Name**: `test_try_parse_manifest_xml_returns_xmldata_on_success`
- **Description**: When `ManifestXml` is successfully instantiated with the given file path.
- **Expected Outcome**: Returns `(xmldata, None)` where `xmldata` is the constructed `ManifestXml` instance.

#### 2. Returns None and Exception on Failure
- **Test Name**: `test_try_parse_manifest_xml_returns_none_and_exception_on_failure`
- **Description**: When `ManifestXml` raises an exception (e.g., malformed XML or I/O error).
- **Expected Outcome**: Returns `(None, exception)` where `exception` is the original raised exception.

### TestValidateParsing
Tests `validate_parsing` which attempts to parse the manifest XML file and returns a `(type, status, message)` result tuple.

#### 1. Success Returns Correct Tuple and Sets Xmldata
- **Test Name**: `test_validate_parsing_success`
- **Description**: When `ManifestXml` is successfully constructed.
- **Expected Outcome**: Returns `("PARSING", True, None)` and `_manifest_xmldata` is set to the constructed instance.

#### 2. Failure Returns Correct Tuple and Clears Xmldata
- **Test Name**: `test_validate_parsing_failure`
- **Description**: When `ManifestXml` raises an exception.
- **Expected Outcome**: Returns `("PARSING", False, <exception>)` and `_manifest_xmldata` is set to `None`.

### TestValidateCodename
Tests `validate_codename` which verifies the manifest codename matches the expected project name and returns a `(type, status, message)` result tuple.

#### 1. Fails When No Manifest Data
- **Test Name**: `test_validate_codename_fails_when_no_manifest_data`
- **Description**: When `_manifest_xmldata` is `None`.
- **Expected Outcome**: Returns `('CODENAME', False, <message containing the project name>)`.

#### 2. Succeeds When Codename Matches
- **Test Name**: `test_validate_codename_succeeds_when_codename_matches`
- **Description**: When `_manifest_xmldata.project_info.codename` equals the given project name.
- **Expected Outcome**: Returns `("CODENAME", True, None)`.

#### 3. Fails When Codename Mismatches
- **Test Name**: `test_validate_codename_fails_when_codename_mismatches`
- **Description**: When `_manifest_xmldata.project_info.codename` differs from the given project name.
- **Expected Outcome**: Returns `("CODENAME", False, <non-None message>)`.

### TestValidateCaseInsensitiveSingleMatch
Tests `validate_case_insensitive_single_match` which verifies the project name appears exactly once in the project list using case-insensitive comparison and returns a `(type, status, message)` result tuple.

#### 1. Exactly One Match Returns Duplicate True
- **Test Name**: `test_validate_case_insensitive_single_match_exactly_one_match`
- **Description**: When exactly one case-insensitive match is found in the project list.
- **Expected Outcome**: Returns `("DUPLICATE", True, None)`.

#### 2. No Match Returns Duplicate False
- **Test Name**: `test_validate_case_insensitive_single_match_fails[no_match]`
- **Description**: When no case-insensitive match is found in the project list.
- **Expected Outcome**: Returns `("DUPLICATE", False, <message containing project name>)`.

#### 3. Multiple Matches Returns Duplicate False
- **Test Name**: `test_validate_case_insensitive_single_match_fails[multiple_matches]`
- **Description**: When more than one case-insensitive match is found in the project list.
- **Expected Outcome**: Returns `("DUPLICATE", False, <message containing project name>)`.

### TestListEntries
Tests `list_entries` which returns all entries in the project list that case-insensitively match the given project name.

#### 1. Returns Matching Entries
- **Test Name**: `test_list_entries_returns_matching_entries`
- **Description**: When the project list contains entries that match the project name case-insensitively.
- **Expected Outcome**: Returns a list containing all matching entries and no non-matching entries.

#### 2. Returns Empty List When No Matches
- **Test Name**: `test_list_entries_returns_empty_when_no_matches`
- **Description**: When no entries in the project list match the project name.
- **Expected Outcome**: Returns an empty list.

### TestCaseInsensitiveEqual
Tests `case_insensitive_equal` which returns `True` if two strings are equal under Unicode NFKD case-folding normalization.

#### 1. Equal Strings Same Case
- **Test Name**: `test_case_insensitive_equal[same_case]`
- **Description**: When both arguments are identical strings (same casing).
- **Expected Outcome**: Returns `True`.

#### 2. Equal Strings Different Case
- **Test Name**: `test_case_insensitive_equal[different_case]`
- **Description**: When both arguments represent the same word with different casing.
- **Expected Outcome**: Returns `True`.

#### 3. Unequal Strings
- **Test Name**: `test_case_insensitive_equal[unequal]`
- **Description**: When both arguments are completely different words.
- **Expected Outcome**: Returns `False`.

### TestCollectFileValidationResults
Tests the `_collect_file_validation_results` helper which validates parsing and codename for a single manifest file.

#### 1. Parsing Succeeds — Codename Validation Included
- **Test Name**: `test_collect_file_validation_results_parsing_succeeds_codename_included`
- **Description**: When `validate_parsing` returns success and `_manifest_xmldata` is populated.
- **Expected Outcome**: The result list contains a passing PARSING tuple followed by a passing CODENAME tuple from `validate_codename`.

#### 2. Parsing Fails — Hardcoded Codename Error Appended
- **Test Name**: `test_collect_file_validation_results_parsing_fails_hardcoded_codename_error`
- **Description**: When `validate_parsing` returns failure and `_manifest_xmldata` is `None`.
- **Expected Outcome**: The result list contains a failing PARSING tuple followed by a hardcoded `('CODENAME', False, 'Cannot process codename validation')` tuple.

### TestResolveProjectManifestPath
Tests the `_resolve_project_manifest_path` helper which computes the absolute path to a project manifest file.

#### 1. Returns Normalized Joined Path
- **Test Name**: `test_resolve_project_manifest_path_returns_normalized_joined_path`
- **Description**: Given a `CiIndexXml` mock whose `get_project_xml` returns a relative path, and a `global_manifest_directory`.
- **Expected Outcome**: Returns `os.path.join(global_manifest_directory, os.path.normpath(relative_path))`.

### TestCollectProjectValidationResults
Tests the `_collect_project_validation_results` helper which runs parsing, codename, and deduplication validations for one project.

#### 1. All Validations Pass — Three Results Returned
- **Test Name**: `test_collect_project_validation_results_all_validations_pass`
- **Description**: When all three `ValidateManifest` methods return passing tuples.
- **Expected Outcome**: The result list has exactly three entries, all with a `True` status.

#### 2. Parsing Fails — Three Results Still Returned
- **Test Name**: `test_collect_project_validation_results_parsing_fails_three_results_returned`
- **Description**: When `validate_parsing` returns a failure tuple; the other validators still run.
- **Expected Outcome**: The result list has exactly three entries; the first has `False` status.

### TestValidateManifestFiles
Tests `validate_manifestfiles` which validates every manifest file in a provided list.

#### 1. Empty List Returns Empty Dict
- **Test Name**: `test_validate_manifestfiles_empty_list_returns_empty_dict`
- **Description**: Called with an empty `manifestfile_list`.
- **Expected Outcome**: Returns an empty dictionary; `_collect_file_validation_results` is never called.

#### 2. Single Manifest — Helper Called Once
- **Test Name**: `test_validate_manifestfiles_single_manifest_calls_helper_once`
- **Description**: Called with a list containing one manifest filepath.
- **Expected Outcome**: Returns a dict with one entry keyed by the filepath whose value is the list returned by `_collect_file_validation_results`.

#### 3. Multiple Manifests — Helper Called for Each
- **Test Name**: `test_validate_manifestfiles_multiple_manifests_calls_helper_for_each`
- **Description**: Called with a list containing two manifest filepaths.
- **Expected Outcome**: Returns a dict with two entries; `_collect_file_validation_results` is called once per filepath with the correct argument.

### TestValidateManifestRepo
Tests `validate_manifestrepo` which validates all manifest files referenced by `CiIndex.xml`.

#### 1. Without Archived — Only Active Projects Processed
- **Test Name**: `test_validate_manifestrepo_without_archived_only_active_projects_processed`
- **Description**: Called with `verify_archived=False`; `CiIndex.xml` contains one active project and one archived project.
- **Expected Outcome**: Returns a dict with one entry; `archived_project_list` is not included.

#### 2. With Archived — Active and Archived Projects Processed
- **Test Name**: `test_validate_manifestrepo_with_archived_active_and_archived_processed`
- **Description**: Called with `verify_archived=True`; `CiIndex.xml` contains one active project and one archived project.
- **Expected Outcome**: Returns a dict with two entries, one per project.

### TestGetManifestValidationStatus
Tests `get_manifest_validation_status` which verifies the validation status of all manifest files; parametrized over all-pass, one-fail, and empty-dict inputs.

#### 1. All Results Pass — Returns False
- **Test Name**: `test_get_manifest_validation_status[all_pass]`
- **Description**: Every result tuple in the dict has a `True` status.
- **Expected Outcome**: Returns `False`.

#### 2. One Result Fails — Returns True
- **Test Name**: `test_get_manifest_validation_status[one_fail]`
- **Description**: At least one result tuple in the dict has a `False` status.
- **Expected Outcome**: Returns `True`.

#### 3. Empty Dict — Returns False
- **Test Name**: `test_get_manifest_validation_status[empty_dict]`
- **Description**: Called with an empty dictionary.
- **Expected Outcome**: Returns `False`.

### TestPrintManifestErrors
Tests `print_manifest_errors` which prints error details for every failed validation result.

#### 1. Prints Header and Details for Each Failure
- **Test Name**: `test_print_manifest_errors_prints_header_and_details_for_failures`
- **Description**: The dict contains one manifest file with one failing result and one passing result.
- **Expected Outcome**: `VERIFY_ERROR_HEADER` is printed once, followed by three print calls for the failing result (file name, error type, error message); the passing result is skipped.

#### 2. All Passing — Only Header Printed
- **Test Name**: `test_print_manifest_errors_all_passing_only_header_printed`
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
