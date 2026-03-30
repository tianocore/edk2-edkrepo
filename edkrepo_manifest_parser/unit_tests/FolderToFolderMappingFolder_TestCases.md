# Test Cases for the `_FolderToFolderMappingFolder` Class

## Test Cases

### TestFolderToFolderMappingFolderInit
Tests `_FolderToFolderMappingFolder.__init__` which parses optional `project1`/`project2` attributes and builds an excludes list from `<Exclude>` children.

#### 1. project1_folder Defaults to None When Absent
- **Description**: When the `project1` attribute is absent.
- **Expected Outcome**: `self.project1_folder` is `None`.

#### 2. project1_folder Set When Present
- **Description**: When the `project1` attribute is present.
- **Expected Outcome**: `self.project1_folder` equals the attribute value.

#### 3. project2_folder Defaults to None When Absent
- **Description**: When the `project2` attribute is absent.
- **Expected Outcome**: `self.project2_folder` is `None`.

#### 4. project2_folder Set When Present
- **Description**: When the `project2` attribute is present.
- **Expected Outcome**: `self.project2_folder` equals the attribute value.

#### 5. excludes Empty When No Exclude Children
- **Description**: When the element has no `<Exclude>` child elements.
- **Expected Outcome**: `self.excludes` is an empty list.

#### 6. excludes Populated From Exclude Children
- **Description**: When one `<Exclude>` child is present.
- **Expected Outcome**: `self.excludes` contains one `_FolderToFolderMappingFolderExclude` with the correct path.

### TestFolderToFolderMappingFolderTuple
Tests `_FolderToFolderMappingFolder.tuple` which returns a `FolderToFolderMappingFolder` namedtuple.

#### 7. Returns Correct FolderToFolderMappingFolder Namedtuple
- **Description**: When both project folder attributes and one Exclude child are present.
- **Expected Outcome**: `tuple` returns a `FolderToFolderMappingFolder` namedtuple with all fields correctly populated.


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
