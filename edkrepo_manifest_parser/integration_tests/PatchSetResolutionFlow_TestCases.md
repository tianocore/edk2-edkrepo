# Test Cases for `PatchSetResolutionFlow` Integration Tests

## Test Cases

### TestPatchSetResolutionFlow
Integration tests for resolving and retrieving patchsets from manifests.

#### 1. Returns Patchset For Name And Remote
- **Test Name**: `test_get_patchset_by_name_and_remote`
- **Description**: When requesting a patchset by name and remote.
- **Expected Outcome**: Returns PatchSet object with matching name.

#### 2. Patchset Attributes Have Correct Values
- **Test Name**: `test_patchset_has_attribute[remote]`
- **Description**: When accessing the remote attribute of a retrieved patchset (parametrized case).
- **Expected Outcome**: Returns the remote name matching the request.

#### 3. Patchset Attributes Have Correct Values
- **Test Name**: `test_patchset_has_attribute[fetch_branch]`
- **Description**: When accessing the fetch_branch attribute of a retrieved patchset (parametrized case).
- **Expected Outcome**: Returns the configured fetch branch reference.

#### 4. Raises KeyError For Invalid Lookup
- **Test Name**: `test_invalid_patchset_lookup_raises_key_error[nonexistent_name]`
- **Description**: When requesting a patchset that does not exist in the manifest (parametrized case).
- **Expected Outcome**: Raises KeyError.

#### 5. Raises KeyError For Invalid Lookup
- **Test Name**: `test_invalid_patchset_lookup_raises_key_error[wrong_remote]`
- **Description**: When requesting a patchset with an incorrect remote name (parametrized case).
- **Expected Outcome**: Raises KeyError.


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
