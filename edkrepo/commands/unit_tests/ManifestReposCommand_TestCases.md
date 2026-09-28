# Test Cases for `ManifestRepos` Class

## Test Cases

### TestRunCommand
Tests `ManifestRepos.run_command` which lists, adds, and removes manifest repositories and validates the associated arguments.

#### 1. List Action Calls List Available Manifest Repos
- **Test Name**: `test_run_command_list_action_calls_list_available_manifest_repos`
- **Description**: When the list action runs.
- **Expected Outcome**: `list_available_manifest_repos` is called with `cfg_file` and `user_cfg_file` from config.

#### 2. List Action Text Format Calls List Manifest Repos
- **Test Name**: `test_run_command_list_action_text_format_calls_list_manifest_repos`
- **Description**: When the list action runs with no explicit format.
- **Expected Outcome**: It routes to `_list_manifest_repos` for text output.

#### 3. List Action Invalid Format Raises Exception
- **Test Name**: `test_run_command_list_action_invalid_format_raises_exception`
- **Description**: When the list action runs with an unrecognised format type.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 4. Remove Nonexistent Repo Raises Exception
- **Test Name**: `test_run_command_remove_nonexistent_repo_raises_exception`
- **Description**: When removing a repo absent from the user cfg `manifest_repo_list`.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 5. Action Without Name Raises Exception (Add)
- **Test Name**: `test_run_command_action_without_name_raises_exception[add]`
- **Description**: When the add action runs without a name argument.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 6. Action Without Name Raises Exception (Remove)
- **Test Name**: `test_run_command_action_without_name_raises_exception[remove]`
- **Description**: When the remove action runs without a name argument.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 7. Raises For Conflict With Existing Repos (Remove Cfg Repo)
- **Test Name**: `test_run_command_raises_for_conflict_with_existing_repos[remove_cfg_repo]`
- **Description**: When removing a cfg-defined repo.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 8. Raises For Conflict With Existing Repos (Add Existing Repo)
- **Test Name**: `test_run_command_raises_for_conflict_with_existing_repos[add_existing_repo]`
- **Description**: When adding a repo that already exists.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 9. Add Without Required Fields Raises Exception (Missing Branch)
- **Test Name**: `test_run_command_add_without_required_fields_raises_exception[missing_branch]`
- **Description**: When the add action is missing the branch field.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 10. Add Without Required Fields Raises Exception (Missing Url)
- **Test Name**: `test_run_command_add_without_required_fields_raises_exception[missing_url]`
- **Description**: When the add action is missing the url field.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 11. Add Without Required Fields Raises Exception (Missing Path)
- **Test Name**: `test_run_command_add_without_required_fields_raises_exception[missing_path]`
- **Description**: When the add action is missing the path field.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

### TestListManifestReposJson
Tests `ManifestRepos._list_manifest_repos_json`, which builds the JSON representation of the configured manifest repositories.

#### 1. List Manifest Repos Json Builds Structure With Names And Paths
- **Test Name**: `test_list_manifest_repos_json_builds_structure_with_names_and_paths`
- **Description**: When `_list_manifest_repos_json` builds JSON output for cfg and user-cfg repos.
- **Expected Outcome**: The returned JSON groups repos under `edkrepo_cfg` and `edkrepo_user_cfg`, each entry carrying its `name` and normalized `path`.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo\commands\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
