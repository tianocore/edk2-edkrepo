# Test Cases for the `_FolderToFolderMapping` Class

## Test Cases

### TestFolderToFolderMappingInit
Tests `_FolderToFolderMapping.__init__` which parses optional `project1`, `project2`, and `remote` attributes and builds a folders list from `<Folder>` and `<File>` children.

#### 1. project1 Defaults to None When Absent
- **Description**: When the `project1` attribute is absent.
- **Expected Outcome**: `self.project1` is `None`.

#### 2. project1 Set When Present
- **Description**: When the `project1` attribute is present.
- **Expected Outcome**: `self.project1` equals the attribute value.

#### 3. project2 Defaults to None When Absent
- **Description**: When the `project2` attribute is absent.
- **Expected Outcome**: `self.project2` is `None`.

#### 4. project2 Set When Present
- **Description**: When the `project2` attribute is present.
- **Expected Outcome**: `self.project2` equals the attribute value.

#### 5. remote_name Defaults to None When Absent
- **Description**: When the `remote` attribute is absent.
- **Expected Outcome**: `self.remote_name` is `None`.

#### 6. remote_name Set When Present
- **Description**: When the `remote` attribute is present.
- **Expected Outcome**: `self.remote_name` equals the attribute value.

#### 7. folders Empty When No Folder or File Children
- **Description**: When the element has no `<Folder>` or `<File>` children.
- **Expected Outcome**: `self.folders` is an empty list.

#### 8. folders Populated From Folder Children
- **Description**: When one `<Folder>` child is present.
- **Expected Outcome**: `self.folders` contains one `_FolderToFolderMappingFolder` with the correct project folder values.

#### 9. folders Populated From File Children
- **Description**: When one `<File>` child is present and no `<Folder>` children exist.
- **Expected Outcome**: `self.folders` contains one `_FolderToFolderMappingFolder` with the correct project folder values.

#### 10. folders Combines Folder and File Children
- **Description**: When both a `<Folder>` child and a `<File>` child are present.
- **Expected Outcome**: `self.folders` contains one entry for each, totalling two items.

### TestFolderToFolderMappingTuple
Tests `_FolderToFolderMapping.tuple` which returns a `FolderToFolderMapping` namedtuple.

#### 11. Returns Correct FolderToFolderMapping Namedtuple
- **Description**: When all attributes and one `<Folder>` child are present.
- **Expected Outcome**: `tuple` returns a `FolderToFolderMapping` namedtuple with all fields correctly populated.


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
