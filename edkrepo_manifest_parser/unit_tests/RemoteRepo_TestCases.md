# Test Cases for `_RemoteRepo` Class

## Test Cases

### TestParseRemoteRepoRequiredAttribs
Tests `_parse_remote_repo_required_attribs(element)` which validates that the required `name` attribute is present and returns `(name, url)`.

#### 1. Returns name and url When Both Attributes Present
- **Description**: When the element contains both a `name` attribute and text content as the URL.
- **Expected Outcome**: Returns `(name, url)` matching the element's `name` attribute and text.

#### 2. Raises KeyError When name Attribute Absent
- **Description**: When the element has no `name` attribute.
- **Expected Outcome**: Raises `KeyError` whose string representation contains the expected `REQUIRED_ATTRIB_ERROR_MSG` prefix.

### TestRemoteRepoInit
Tests `_RemoteRepo.__init__` which parses a `<RemoteRepo>` XML element for required and optional attributes.

#### 1. Sets name and url From Required Attributes
- **Description**: When the element has a `name` attribute and text content for the URL.
- **Expected Outcome**: `self.name` equals the `name` attribute value; `self.url` equals the element's text.

#### 2. Sets owner When owner Attribute Present
- **Description**: When the element has an `owner` attribute.
- **Expected Outcome**: `self.owner` is set to the `owner` attribute value.

#### 3. Sets owner to None When owner Attribute Absent
- **Description**: When the element has no `owner` attribute.
- **Expected Outcome**: `self.owner` is `None`.

#### 4. Sets review_type When reviewType Attribute Present
- **Description**: When the element has a `reviewType` attribute.
- **Expected Outcome**: `self.review_type` is set to the `reviewType` attribute value.

#### 5. Sets review_type to None When reviewType Attribute Absent
- **Description**: When the element has no `reviewType` attribute.
- **Expected Outcome**: `self.review_type` is `None`.

#### 6. Sets pr_strategy When prStrategy Attribute Present
- **Description**: When the element has a `prStrategy` attribute.
- **Expected Outcome**: `self.pr_strategy` is set to the `prStrategy` attribute value.

#### 7. Sets pr_strategy to None When prStrategy Attribute Absent
- **Description**: When the element has no `prStrategy` attribute.
- **Expected Outcome**: `self.pr_strategy` is `None`.

### TestRemoteRepoTuple
Tests `_RemoteRepo.tuple` which returns a `RemoteRepo` namedtuple.

#### 1. Returns Correct RemoteRepo Namedtuple
- **Description**: When all attributes are present.
- **Expected Outcome**: `tuple` returns a `RemoteRepo` namedtuple with all fields correctly populated.


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
