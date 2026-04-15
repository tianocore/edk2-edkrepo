# Test Cases for `ValidateManifest` Class

## Test Cases

### TestTryParseManifestXml
Tests `_try_parse_manifest_xml` which attempts to construct a `ManifestXml` from a file path and returns `(xmldata, None)` on success or `(None, exception)` on failure.

#### 1. Returns Xmldata on Success
- **Description**: When `ManifestXml` is successfully instantiated with the given file path.
- **Expected Outcome**: Returns `(xmldata, None)` where `xmldata` is the constructed `ManifestXml` instance.

#### 2. Returns None and Exception on Failure
- **Description**: When `ManifestXml` raises an exception (e.g., malformed XML or I/O error).
- **Expected Outcome**: Returns `(None, exception)` where `exception` is the original raised exception.

### TestValidateParsing
Tests `validate_parsing` which attempts to parse the manifest XML file and returns a `(type, status, message)` result tuple.

#### 1. Success Returns Correct Tuple and Sets Xmldata
- **Description**: When `ManifestXml` is successfully constructed.
- **Expected Outcome**: Returns `("PARSING", True, None)` and `_manifest_xmldata` is set to the constructed instance.

#### 2. Failure Returns Correct Tuple and Clears Xmldata
- **Description**: When `ManifestXml` raises an exception.
- **Expected Outcome**: Returns `("PARSING", False, <exception>)` and `_manifest_xmldata` is set to `None`.

### TestValidateCodename
Tests `validate_codename` which verifies the manifest codename matches the expected project name and returns a `(type, status, message)` result tuple.

#### 1. Fails When No Manifest Data
- **Description**: When `_manifest_xmldata` is `None`.
- **Expected Outcome**: Returns `('CODENAME', False, <message containing the project name>)`.

#### 2. Succeeds When Codename Matches
- **Description**: When `_manifest_xmldata.project_info.codename` equals the given project name.
- **Expected Outcome**: Returns `("CODENAME", True, None)`.

#### 3. Fails When Codename Mismatches
- **Description**: When `_manifest_xmldata.project_info.codename` differs from the given project name.
- **Expected Outcome**: Returns `("CODENAME", False, <non-None message>)`.

### TestValidateCaseInsensitiveSingleMatch
Tests `validate_case_insensitive_single_match` which verifies the project name appears exactly once in the project list using case-insensitive comparison and returns a `(type, status, message)` result tuple.

#### 1. Exactly One Match Returns Duplicate True
- **Description**: When exactly one case-insensitive match is found in the project list.
- **Expected Outcome**: Returns `("DUPLICATE", True, None)`.

#### 2. No Match Returns Duplicate False
- **Description**: When no case-insensitive match is found in the project list.
- **Expected Outcome**: Returns `("DUPLICATE", False, <message containing project name>)`.

#### 3. Multiple Matches Returns Duplicate False
- **Description**: When more than one case-insensitive match is found in the project list.
- **Expected Outcome**: Returns `("DUPLICATE", False, <message containing project name>)`.

### TestListEntries
Tests `list_entries` which returns all entries in the project list that case-insensitively match the given project name.

#### 1. Returns Matching Entries
- **Description**: When the project list contains entries that match the project name case-insensitively.
- **Expected Outcome**: Returns a list containing all matching entries and no non-matching entries.

#### 2. Returns Empty List When No Matches
- **Description**: When no entries in the project list match the project name.
- **Expected Outcome**: Returns an empty list.

### TestCaseInsensitiveEqual
Tests `case_insensitive_equal` which returns `True` if two strings are equal under Unicode NFKD case-folding normalization.

#### 1. Equal Strings Same Case
- **Description**: When both arguments are identical strings (same casing).
- **Expected Outcome**: Returns `True`.

#### 2. Equal Strings Different Case
- **Description**: When both arguments represent the same word with different casing.
- **Expected Outcome**: Returns `True`.

#### 3. Unequal Strings
- **Description**: When both arguments are completely different words.
- **Expected Outcome**: Returns `False`.


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
