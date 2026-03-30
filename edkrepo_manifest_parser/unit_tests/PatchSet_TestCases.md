# Test Cases for `_PatchSet` Class

## Test Cases

### TestParsePatchsetRequiredAttribs
Tests `_parse_patchset_required_attribs` which parses the four required attributes of a `<PatchSet>` XML element, or raises `KeyError` when any are absent.

#### 1. Returns All Four Values When All Present
- **Description**: When `remote`, `name`, `parentSha`, and `fetchBranch` are all present in `element.attrib`.
- **Expected Outcome**: Returns the tuple `(remote, name, parentSha, fetchBranch)` with the correct values.

#### 2. Raises KeyError When `remote` Missing
- **Description**: When `remote` is absent from `element.attrib`.
- **Expected Outcome**: `KeyError` is raised containing the required-attribute error message prefix.

#### 3. Raises KeyError When `name` Missing
- **Description**: When `name` is absent from `element.attrib`.
- **Expected Outcome**: `KeyError` is raised containing the required-attribute error message prefix.

#### 4. Raises KeyError When `parentSha` Missing
- **Description**: When `parentSha` is absent from `element.attrib`.
- **Expected Outcome**: `KeyError` is raised containing the required-attribute error message prefix.

#### 5. Raises KeyError When `fetchBranch` Missing
- **Description**: When `fetchBranch` is absent from `element.attrib`.
- **Expected Outcome**: `KeyError` is raised containing the required-attribute error message prefix.

### TestPatchSetInit
Tests `_PatchSet.__init__` which delegates required-attribute parsing to `_parse_patchset_required_attribs` and assigns the four fields.

#### 1. Sets All Fields From Required Attribs
- **Description**: When all four required attributes are present.
- **Expected Outcome**: `self.remote`, `self.name`, `self.parentSha`, and `self.fetchBranch` are set to the corresponding attribute values.

### TestPatchSetEq
Tests `_PatchSet.__eq__` which returns `True` only when compared to a `_PatchSet` with identical values for all four fields.

#### 1. Returns True for Equal Patchsets
- **Description**: Two `_PatchSet` instances constructed from identical attribute dicts.
- **Expected Outcome**: `ps1 == ps2` evaluates to `True`.

#### 2. Returns False for Different Patchsets
- **Description**: Two `_PatchSet` instances that differ in at least one field.
- **Expected Outcome**: `ps1 != ps2` evaluates to `True`.

#### 3. Returns False for Non-`_PatchSet` Type
- **Description**: Comparing a `_PatchSet` to an object that is not a `_PatchSet`.
- **Expected Outcome**: `__eq__` returns `False`.

### TestPatchSetTuple
Tests `_PatchSet.tuple` which returns a `PatchSet` namedtuple with the four field values.

#### 1. Returns Correct PatchSet Namedtuple
- **Description**: When all fields are set.
- **Expected Outcome**: `tuple` returns a `PatchSet(remote, name, parent_sha, fetch_branch)` with the correct values.


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
