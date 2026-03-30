# Test Cases for the `_SparseData` Class

## Test Cases

### TestSparseDataInit
Tests `_SparseData.__init__` which parses optional attributes and iterates `AlwaysInclude` / `AlwaysExclude` children from a `<SparseData>` element.

#### 1. All Fields Default When All Attributes and Children Absent
- **Description**: When all optional attributes (`combination`, `remote`) and all child elements (`AlwaysInclude`, `AlwaysExclude`) are absent.
- **Expected Outcome**: `self.combination` is `None`, `self.remote_name` is `None`, `self.always_include` is `[]`, and `self.always_exclude` is `[]`.

#### 2. Sets combination When combination Attribute Present
- **Description**: When the `combination` attribute is present.
- **Expected Outcome**: `self.combination` equals the attribute value.

#### 3. Sets remote_name When remote Attribute Present
- **Description**: When the `remote` attribute is present.
- **Expected Outcome**: `self.remote_name` equals the attribute value.

#### 4. Populates always_include From Single AlwaysInclude Child
- **Description**: When one `AlwaysInclude` child is present with a single path.
- **Expected Outcome**: `self.always_include` contains that path as its sole entry.

#### 5. Populates always_exclude From Single AlwaysExclude Child
- **Description**: When one `AlwaysExclude` child is present with a single path.
- **Expected Outcome**: `self.always_exclude` contains that path as its sole entry.

#### 6. Splits Pipe-Separated Values for always_include
- **Description**: When an `AlwaysInclude` child contains multiple paths separated by `|`.
- **Expected Outcome**: Each path is added as a separate entry in `self.always_include`.

#### 7. Splits Pipe-Separated Values for always_exclude
- **Description**: When an `AlwaysExclude` child contains multiple paths separated by `|`.
- **Expected Outcome**: Each path is added as a separate entry in `self.always_exclude`.

### TestSparseDataTuple
Tests `_SparseData.tuple` which returns a `SparseData` namedtuple.

#### 1. Returns Correct SparseData Namedtuple
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
