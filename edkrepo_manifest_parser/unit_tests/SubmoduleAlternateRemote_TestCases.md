# Test Cases for the `_SubmoduleAlternateRemote` Class

## Test Cases

### TestParseSubmoduleAlternateRemoteAttribs
Tests `_parse_submodule_alternate_remote_attribs` which returns `(remote_name, original_url, alt_url)` or raises `KeyError` if any required attribute is missing or the remote name is not in `remotes`.

#### 1. Returns All Fields When All Present
- **Test Name**: `test_parse_returns_all_fields_when_all_present`
- **Description**: When all required attributes (`remote`, `originalUrl`) are present and the remote name is a key in the remotes dict.
- **Expected Outcome**: Returns a tuple of `(remote_name, original_url, alt_url)` with the correct values.

#### 2. Raises When remote Missing
- **Test Name**: `test_parse_raises_when_required_attrib_missing[remote_missing]`
- **Description**: When the `remote` attribute is absent from the element.
- **Expected Outcome**: Raises `KeyError` whose message contains the required-attribute error prefix.

#### 3. Raises When originalUrl Missing
- **Test Name**: `test_parse_raises_when_required_attrib_missing[original_url_missing]`
- **Description**: When the `originalUrl` attribute is absent from the element.
- **Expected Outcome**: Raises `KeyError` whose message contains the required-attribute error prefix.

#### 4. Raises When Remote Not in Remotes
- **Test Name**: `test_parse_raises_when_remote_not_in_remotes`
- **Description**: When the `remote` attribute value is not a key in the remotes dict.
- **Expected Outcome**: Raises `KeyError` whose message contains the no-remote-exists error prefix.

### TestSubmoduleAlternateRemoteInit
Tests `_SubmoduleAlternateRemote.__init__` which parses required attributes and validates the remote from a `<SubmoduleAlternateRemote>` element.

#### 1. Sets All Fields
- **Test Name**: `test_init_sets_all_fields`
- **Description**: When all required attributes are valid and the remote is present in the remotes dict.
- **Expected Outcome**: `self.remote_name`, `self.originalUrl`, and `self.altUrl` are set to the correct values.

### TestSubmoduleAlternateRemoteTuple
Tests `_SubmoduleAlternateRemote.tuple` which returns a `SubmoduleAlternateRemote` namedtuple.

#### 1. Returns Correct SubmoduleAlternateRemote Namedtuple
- **Test Name**: `test_tuple_returns_correct_submodule_alternate_remote_namedtuple`
- **Description**: When the object has been fully initialized with valid attributes.
- **Expected Outcome**: `tuple` returns a `SubmoduleAlternateRemote` namedtuple with all fields correctly populated.


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
