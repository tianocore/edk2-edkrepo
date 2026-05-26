# Test Cases for the `_FolderToFolderMappingFolderExclude` Class

## Test Cases

### TestFolderToFolderMappingFolderExcludeInit
Tests `_FolderToFolderMappingFolderExclude.__init__` which parses the optional `path` attribute from an `<Exclude>` element.

#### 1. path Defaults to None When Absent
- **Test Name**: `test_path_defaults_to_none_when_absent`
- **Description**: When the `path` attribute is absent.
- **Expected Outcome**: `self.path` is `None`.

#### 2. path Set When Present
- **Test Name**: `test_path_when_present`
- **Description**: When the `path` attribute is present.
- **Expected Outcome**: `self.path` equals the attribute value.

### TestFolderToFolderMappingFolderExcludeTuple
Tests `_FolderToFolderMappingFolderExclude.tuple` which returns a `FolderToFolderMappingFolderExclude` namedtuple.

#### 1. Returns Correct FolderToFolderMappingFolderExclude Namedtuple
- **Test Name**: `test_tuple_returns_correct_folder_to_folder_mapping_folder_exclude_namedtuple`
- **Description**: When the `path` attribute is present.
- **Expected Outcome**: `tuple` returns `FolderToFolderMappingFolderExclude(path=<value>)`.


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
