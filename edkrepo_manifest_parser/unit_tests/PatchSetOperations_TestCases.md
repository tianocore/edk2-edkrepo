# Test Cases for `_PatchSetOperations` Class

## Test Cases

### TestPatchSetOperationsInit
Tests `_PatchSetOperations.__init__` which reads `element.tag` for the operation type and treats all five XML attributes as optional, defaulting each to `None` when absent.

#### 1. Sets Type From Element Tag
- **Test Name**: `test_init_sets_type_from_element_tag`
- **Description**: When element has a tag (e.g., `'CherryPick'`).
- **Expected Outcome**: `self.type` is set to `element.tag`.

#### 2. Sets All Optional Attribs When Present
- **Test Name**: `test_init_sets_all_optional_attribs_when_present`
- **Description**: When `file`, `sha`, `sourceRemote`, `sourceBranch`, and `mergeStrategy` are all present in `element.attrib`.
- **Expected Outcome**: Each corresponding field is set to its attribute value.

#### 3. Sets `file` to None When Missing
- **Test Name**: `test_init_optional_attrib_defaults_to_none_when_missing[file]`
- **Description**: When `file` is absent from `element.attrib`.
- **Expected Outcome**: `self.file` is `None`.

#### 4. Sets `sha` to None When Missing
- **Test Name**: `test_init_optional_attrib_defaults_to_none_when_missing[sha]`
- **Description**: When `sha` is absent from `element.attrib`.
- **Expected Outcome**: `self.sha` is `None`.

#### 5. Sets `source_remote` to None When Missing
- **Test Name**: `test_init_optional_attrib_defaults_to_none_when_missing[source_remote]`
- **Description**: When `sourceRemote` is absent from `element.attrib`.
- **Expected Outcome**: `self.source_remote` is `None`.

#### 6. Sets `source_branch` to None When Missing
- **Test Name**: `test_init_optional_attrib_defaults_to_none_when_missing[source_branch]`
- **Description**: When `sourceBranch` is absent from `element.attrib`.
- **Expected Outcome**: `self.source_branch` is `None`.

#### 7. Sets `merge_strategy` to None When Missing
- **Test Name**: `test_init_optional_attrib_defaults_to_none_when_missing[merge_strategy]`
- **Description**: When `mergeStrategy` is absent from `element.attrib`.
- **Expected Outcome**: `self.merge_strategy` is `None`.

### TestPatchSetOperationsTuple
Tests `_PatchSetOperations.tuple` which returns a `PatchOperation` namedtuple with all six field values.

#### 1. Returns Correct PatchOperation Namedtuple
- **Test Name**: `test_tuple_returns_correct_patch_operation_namedtuple`
- **Description**: When all optional attributes are present.
- **Expected Outcome**: `tuple` returns a `PatchOperation(type, file, sha, source_remote, source_branch, merge_strategy)` with the correct values.


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
