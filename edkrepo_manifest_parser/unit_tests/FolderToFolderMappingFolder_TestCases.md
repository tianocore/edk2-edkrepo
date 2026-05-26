# Test Cases for the `_FolderToFolderMappingFolder` Class

## Test Cases

### TestFolderToFolderMappingFolderInit
Tests `_FolderToFolderMappingFolder.__init__` which parses optional `project1`/`project2` attributes and builds an excludes list from `<Exclude>` children.

#### 1. All Fields Default When All Attributes and Children Absent
- **Test Name**: `test_all_fields_default_when_absent`
- **Description**: When all optional attributes (`project1`, `project2`) and `<Exclude>` child elements are absent.
- **Expected Outcome**: `self.project1_folder` is `None`, `self.project2_folder` is `None`, and `self.excludes` is `[]`.

#### 2. Sets project1_folder When project1 Attribute Present
- **Test Name**: `test_init_sets_project_folder_when_present[project1_folder_present]`
- **Description**: When the `project1` attribute is present.
- **Expected Outcome**: `self.project1_folder` equals the attribute value.

#### 3. Sets project2_folder When project2 Attribute Present
- **Test Name**: `test_init_sets_project_folder_when_present[project2_folder_present]`
- **Description**: When the `project2` attribute is present.
- **Expected Outcome**: `self.project2_folder` equals the attribute value.

#### 4. Populates excludes From Exclude Children
- **Test Name**: `test_init_populates_excludes_from_exclude_children`
- **Description**: When one `<Exclude>` child is present.
- **Expected Outcome**: `self.excludes` contains one `_FolderToFolderMappingFolderExclude` with the correct path.

### TestFolderToFolderMappingFolderTuple
Tests `_FolderToFolderMappingFolder.tuple` which returns a `FolderToFolderMappingFolder` namedtuple.

#### 1. Returns Correct FolderToFolderMappingFolder Namedtuple
- **Test Name**: `test_tuple_returns_correct_folder_to_folder_mapping_folder_namedtuple`
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
