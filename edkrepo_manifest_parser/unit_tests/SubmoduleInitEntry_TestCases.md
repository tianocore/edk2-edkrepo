# Test Cases for the `_SubmoduleInitEntry` Class

## Test Cases

### TestParseSubmoduleInitRequiredAttribs
Tests `_parse_submodule_init_required_attribs` which returns `(remote_name, path)` or raises `KeyError` if the required `remote` attribute is missing.

#### 1. Returns All Fields When All Present
- **Test Name**: `test_parse_returns_all_fields_when_all_present`
- **Description**: When the required `remote` attribute is present and `element.text` provides the path.
- **Expected Outcome**: Returns a tuple of `(remote_name, path)` with the correct values.

#### 2. Raises When remote Missing
- **Test Name**: `test_parse_raises_when_remote_missing`
- **Description**: When the `remote` attribute is absent from the element.
- **Expected Outcome**: Raises `KeyError` whose message contains the required-attribute error prefix.

### TestSubmoduleInitEntryInit
Tests `_SubmoduleInitEntry.__init__` which parses required and optional attributes from a `<SubmoduleInitEntry>` element.

#### 1. Sets All Required Fields
- **Test Name**: `test_init_sets_all_required_fields`
- **Description**: When the required `remote` attribute and element text are present.
- **Expected Outcome**: `self.remote_name` and `self.path` are set to the correct values.

#### 2. All Optional Fields Default When Absent
- **Test Name**: `test_all_optional_fields_default_when_absent`
- **Description**: When the `combo` and `recursive` attributes are both absent.
- **Expected Outcome**: `self.combo` is `None` and `self.recursive` is `False`.

#### 3. combo Set When Present
- **Test Name**: `test_combo_when_present`
- **Description**: When the `combo` attribute is present.
- **Expected Outcome**: `self.combo` equals the attribute value.

#### 4. recursive True When Attribute Is "true"
- **Test Name**: `test_init_sets_recursive_flag[recursive_true]`
- **Description**: When the `recursive` attribute is `"true"`.
- **Expected Outcome**: `self.recursive` is `True`.

#### 5. recursive False When Attribute Is "false"
- **Test Name**: `test_init_sets_recursive_flag[recursive_false]`
- **Description**: When the `recursive` attribute is `"false"`.
- **Expected Outcome**: `self.recursive` is `False`.

### TestSubmoduleInitEntryTuple
Tests `_SubmoduleInitEntry.tuple` which returns a `SubmoduleInitPath` namedtuple.

#### 1. Returns Correct SubmoduleInitPath Namedtuple
- **Test Name**: `test_tuple_returns_correct_submodule_init_path_namedtuple`
- **Description**: When the object has been initialized with required fields and no optional fields.
- **Expected Outcome**: `tuple` returns a `SubmoduleInitPath` namedtuple with all fields correctly populated.


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
