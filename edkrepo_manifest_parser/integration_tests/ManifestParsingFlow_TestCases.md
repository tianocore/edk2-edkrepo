# Test Cases for `ManifestParsingFlow` Integration Tests

## Test Cases

### TestManifestParsingFlow
Integration tests for parsing complete manifests from various formats and configurations.

#### 1. Manifest Loads Successfully
- **Test Name**: `test_manifest_loads_successfully[complete_xml]`
- **Description**: When loading a complete XML manifest with all sections populated (parametrized case).
- **Expected Outcome**: ManifestXml instance is created successfully without errors.

#### 2. Manifest Loads Successfully
- **Test Name**: `test_manifest_loads_successfully[minimal_xml]`
- **Description**: When loading a minimal XML manifest containing only required fields (parametrized case).
- **Expected Outcome**: ManifestXml instance is created with defaults for optional fields.

#### 3. Manifest Loads Successfully
- **Test Name**: `test_manifest_loads_successfully[complete_json]`
- **Description**: When loading a manifest from JSON format (parametrized case).
- **Expected Outcome**: ManifestXml instance is created successfully from JSON input.

#### 4. Manifest Loads Successfully
- **Test Name**: `test_manifest_loads_successfully[with_include]`
- **Description**: When loading a manifest that includes external XML files (parametrized case).
- **Expected Outcome**: Included content is merged correctly into the ManifestXml instance.

#### 5. Invalid Manifest Raises TypeError
- **Test Name**: `test_invalid_manifest_raises_type_error`
- **Description**: When attempting to load an invalid manifest file.
- **Expected Outcome**: Raises TypeError.

#### 6. Complete Manifest Contains Project Info
- **Test Name**: `test_complete_manifest_has_project_info`
- **Description**: When accessing the project_info property of a complete manifest.
- **Expected Outcome**: Returns ProjectInfo with correct codename, description, short_name, and org.

#### 7. Minimal Manifest Contains Project Info
- **Test Name**: `test_minimal_manifest_has_project_info`
- **Description**: When accessing the project_info property of a minimal manifest.
- **Expected Outcome**: Returns ProjectInfo with all required fields.

#### 8. Complete Manifest Contains General Config
- **Test Name**: `test_complete_manifest_has_general_config`
- **Description**: When accessing the general_config property of a complete manifest.
- **Expected Outcome**: Returns GeneralConfig with correct default_combo, current_combo, and pin_path.

#### 9. Minimal Manifest Contains General Config
- **Test Name**: `test_minimal_manifest_has_general_config`
- **Description**: When accessing the general_config property of a minimal manifest.
- **Expected Outcome**: Returns GeneralConfig with required configuration values.

#### 10. Complete Manifest Contains Remotes
- **Test Name**: `test_complete_manifest_has_remotes`
- **Description**: When accessing the remotes property of a complete manifest.
- **Expected Outcome**: Returns list of RemoteRepo tuples with correct names and URLs.

#### 11. Minimal Manifest Contains Remotes
- **Test Name**: `test_minimal_manifest_has_remotes`
- **Description**: When accessing the remotes property of a minimal manifest.
- **Expected Outcome**: Returns single RemoteRepo tuple with correct name and URL.

#### 12. Complete Manifest Contains Combinations
- **Test Name**: `test_complete_manifest_has_combinations`
- **Description**: When accessing the combinations property of a complete manifest.
- **Expected Outcome**: Returns list of non-archived Combination tuples with correct names.

#### 13. Minimal Manifest Contains Combinations
- **Test Name**: `test_minimal_manifest_has_combinations`
- **Description**: When accessing the combinations property of a minimal manifest.
- **Expected Outcome**: Returns single Combination tuple with correct name and description.

#### 14. Returns Repo Sources For Main Combination
- **Test Name**: `test_complete_manifest_get_repo_sources_for_main_combo`
- **Description**: When requesting repo sources for the main combination.
- **Expected Outcome**: Returns correct RepoSource tuples for all repositories in the main combination.

#### 15. Returns Repo Sources For Dev Combination
- **Test Name**: `test_complete_manifest_get_repo_sources_for_dev_combo`
- **Description**: When requesting repo sources for the dev combination.
- **Expected Outcome**: Returns RepoSource tuples with develop branches.

#### 16. Returns Repo Sources From Minimal Manifest
- **Test Name**: `test_minimal_manifest_get_repo_sources_for_main_combo`
- **Description**: When requesting repo sources from a minimal manifest.
- **Expected Outcome**: Returns single RepoSource tuple with correct values.

#### 17. Complete Manifest Contains Sparse Settings
- **Test Name**: `test_complete_manifest_has_sparse_settings`
- **Description**: When accessing the sparse_settings property.
- **Expected Outcome**: Returns SparseSettings tuple with correct sparse_by_default value.

#### 18. Complete Manifest Contains Sparse Data
- **Test Name**: `test_complete_manifest_has_sparse_data`
- **Description**: When accessing the sparse_data property.
- **Expected Outcome**: Returns list of SparseData tuples for each combination.

#### 19. Complete Manifest Contains Patch Sets
- **Test Name**: `test_complete_manifest_has_patch_sets`
- **Description**: When querying the manifest for patch sets.
- **Expected Outcome**: Returns PatchSet tuple with correct name, remote, and fetch_branch.

#### 20. Complete Manifest Contains Folder Mappings
- **Test Name**: `test_complete_manifest_has_folder_mappings`
- **Description**: When accessing the folder_to_folder_mappings property.
- **Expected Outcome**: Returns list of FolderToFolderMapping tuples with correct project mappings.

#### 21. Complete Manifest Contains Client Git Hooks
- **Test Name**: `test_complete_manifest_has_client_git_hooks`
- **Description**: When accessing the client_git_hooks property.
- **Expected Outcome**: Returns list of RepoHook tuples with correct source and destination paths.

#### 22. JSON Manifest Contains Project Info
- **Test Name**: `test_json_manifest_parses_project_info_correctly`
- **Description**: When accessing project_info from a JSON manifest.
- **Expected Outcome**: Returns ProjectInfo with correct codename from JSON input.

#### 23. JSON Manifest Contains Combinations
- **Test Name**: `test_json_manifest_parses_combinations_correctly`
- **Description**: When accessing combinations from a JSON manifest.
- **Expected Outcome**: Returns correct number of Combination tuples from JSON input.

#### 24. Included Manifests Merge Remotes
- **Test Name**: `test_manifest_with_include_merges_remotes`
- **Description**: When loading a manifest with included files.
- **Expected Outcome**: Returns combined list of remotes from main and included manifests.

#### 25. Returns Archived Combinations
- **Test Name**: `test_complete_manifest_get_archived_combinations`
- **Description**: When accessing the archived_combinations property.
- **Expected Outcome**: Returns list of archived Combination tuples.

#### 26. Minimal Manifest Has No Archived Combinations
- **Test Name**: `test_minimal_manifest_has_no_archived_combinations`
- **Description**: When accessing archived_combinations from a minimal manifest.
- **Expected Outcome**: Returns empty list.


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
