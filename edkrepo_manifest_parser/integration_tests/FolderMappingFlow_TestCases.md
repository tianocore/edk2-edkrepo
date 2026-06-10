# Test Cases for `FolderMappingFlow` Integration Tests

## Test Cases

### TestFolderMappingFlow
Integration tests for folder mapping configuration and data retrieval from manifests.

#### 1. Returns List Of Folder Mappings
- **Test Name**: `test_get_folder_mappings_from_manifest`
- **Description**: When accessing the folder_to_folder_mappings property.
- **Expected Outcome**: Returns list of FolderToFolderMapping objects with correct count.

#### 2. Mapping Attributes Have Correct Values
- **Test Name**: `test_folder_mapping_has_attribute[project1]`
- **Description**: When accessing the project1 attribute of a folder mapping (parametrized case).
- **Expected Outcome**: Returns the configured project1 name matching the manifest.

#### 3. Mapping Attributes Have Correct Values
- **Test Name**: `test_folder_mapping_has_attribute[project2]`
- **Description**: When accessing the project2 attribute of a folder mapping (parametrized case).
- **Expected Outcome**: Returns the configured project2 name matching the manifest.

#### 4. Mapping Attributes Have Correct Values
- **Test Name**: `test_folder_mapping_has_attribute[remote_name]`
- **Description**: When accessing the remote_name attribute of a folder mapping (parametrized case).
- **Expected Outcome**: Returns the configured remote name matching the manifest.

#### 5. Mapping Contains Folders List
- **Test Name**: `test_folder_mapping_has_folders_list`
- **Description**: When accessing the folders attribute of a folder mapping.
- **Expected Outcome**: Returns a list of folder objects with correct count.

#### 6. Folder Project Folder Attributes Have Correct Values
- **Test Name**: `test_folder_has_project_folder_attribute[project1_folder]`
- **Description**: When accessing the project1_folder attribute of a folder object (parametrized case).
- **Expected Outcome**: Returns the configured project1 folder path.

#### 7. Folder Project Folder Attributes Have Correct Values
- **Test Name**: `test_folder_has_project_folder_attribute[project2_folder]`
- **Description**: When accessing the project2_folder attribute of a folder object (parametrized case).
- **Expected Outcome**: Returns the configured project2 folder path.

#### 8. Folder Contains Excludes List
- **Test Name**: `test_folder_has_excludes_list`
- **Description**: When accessing the excludes attribute of a folder object.
- **Expected Outcome**: Returns a list of exclude objects with correct count.

#### 9. Exclude Contains Path Attribute
- **Test Name**: `test_folder_exclude_has_path_attribute`
- **Description**: When accessing the path attribute of an exclude object.
- **Expected Outcome**: Returns the configured exclusion pattern.

#### 10. Returns Only Matching Project Mappings
- **Test Name**: `test_filter_folder_mappings_by_project`
- **Description**: When filtering folder mappings by project name.
- **Expected Outcome**: Returns only folder mappings where project1 matches the specified name.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\integration_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
