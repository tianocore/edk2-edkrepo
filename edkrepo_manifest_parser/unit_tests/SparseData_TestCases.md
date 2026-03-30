# Test Cases for the `_SparseData` Class

## Test Cases

### TestSparseDataInit
Tests `_SparseData.__init__` which parses optional attributes and iterates `AlwaysInclude` / `AlwaysExclude` children from a `<SparseData>` element.

#### 1. combination Defaults to None When Absent
- **Description**: When the `combination` attribute is absent.
- **Expected Outcome**: `self.combination` is `None`.

#### 2. combination Set When Present
- **Description**: When the `combination` attribute is present.
- **Expected Outcome**: `self.combination` equals the attribute value.

#### 3. remote_name Defaults to None When Absent
- **Description**: When the `remote` attribute is absent.
- **Expected Outcome**: `self.remote_name` is `None`.

#### 4. remote_name Set When Present
- **Description**: When the `remote` attribute is present.
- **Expected Outcome**: `self.remote_name` equals the attribute value.

#### 5. always_include Empty When No AlwaysInclude Children
- **Description**: When the element has no `AlwaysInclude` child elements.
- **Expected Outcome**: `self.always_include` is an empty list.

#### 6. always_include Populated From Single AlwaysInclude Child
- **Description**: When one `AlwaysInclude` child is present with a single path.
- **Expected Outcome**: `self.always_include` contains that path as its sole entry.

#### 7. always_include Splits Pipe-Separated Values
- **Description**: When an `AlwaysInclude` child contains multiple paths separated by `|`.
- **Expected Outcome**: Each path is added as a separate entry in `self.always_include`.

#### 8. always_exclude Empty When No AlwaysExclude Children
- **Description**: When the element has no `AlwaysExclude` child elements.
- **Expected Outcome**: `self.always_exclude` is an empty list.

#### 9. always_exclude Populated From Single AlwaysExclude Child
- **Description**: When one `AlwaysExclude` child is present with a single path.
- **Expected Outcome**: `self.always_exclude` contains that path as its sole entry.

### TestSparseDataTuple
Tests `_SparseData.tuple` which returns a `SparseData` namedtuple.

#### 10. Returns Correct SparseData Namedtuple
- **Description**: When all optional fields and both include/exclude children are present.
- **Expected Outcome**: `tuple` returns a `SparseData` namedtuple with all fields correctly populated.


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
