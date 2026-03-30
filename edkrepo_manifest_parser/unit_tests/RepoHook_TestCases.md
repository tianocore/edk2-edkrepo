# Test Cases for `_RepoHook` Class

## Test Cases

### TestParseRepoHookRequiredAttribs
Tests `_parse_repo_hook_required_attribs(element)` which validates that both `source` and `destination` required attributes are present, raising `KeyError` for either absence.

#### 1. Returns source and dest_path When Both Attributes Present
- **Description**: When the element contains both a `source` attribute and a `destination` attribute.
- **Expected Outcome**: Returns `(source, dest_path)` matching the element's attribute values.

#### 2. Raises KeyError When source Attribute Absent
- **Description**: When the element has no `source` attribute.
- **Expected Outcome**: Raises `KeyError` whose string representation contains the expected `REQUIRED_ATTRIB_ERROR_MSG` prefix.

#### 3. Raises KeyError When destination Attribute Absent
- **Description**: When the element has no `destination` attribute.
- **Expected Outcome**: Raises `KeyError` whose string representation contains the expected `REQUIRED_ATTRIB_ERROR_MSG` prefix.

### TestRepoHookInit
Tests `_RepoHook.__init__` which parses a `<ClientGitHook>` XML element for required attributes and resolves the remote URL from a remotes dictionary.

#### 1. Sets source and dest_path From Required Attributes
- **Description**: When the element has valid `source` and `destination` attributes.
- **Expected Outcome**: `self.source` and `self.dest_path` are set to the corresponding attribute values.

#### 2. Sets Optional Field When Present (Parametrized)
- **Description**: When the element's optional attribute is present and resolved, parametrized over `remote_url` (from remotes lookup) and `dest_file` (from `destination_file` attribute).
- **Expected Outcome**: The corresponding field on the instance equals the expected value for each variant (`remote_url_found`, `dest_file_present`).

#### 3. Sets remote_url to None When remote Attribute Absent
- **Description**: When the element has no `remote` attribute.
- **Expected Outcome**: `self.remote_url` is `None`.

#### 4. Sets dest_file to None When destination_file Attribute Absent
- **Description**: When the element has no `destination_file` attribute.
- **Expected Outcome**: `self.dest_file` is `None`.

### TestRepoHookTuple
Tests `_RepoHook.tuple` which returns a `RepoHook` namedtuple.

#### 1. Returns Correct RepoHook Namedtuple
- **Description**: When all attributes are present and the remote URL is resolved.
- **Expected Outcome**: `tuple` returns a `RepoHook` namedtuple with all fields correctly populated.


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
