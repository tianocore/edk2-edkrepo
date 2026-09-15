# Test Cases for `ReferenceRepos` Class

## Test Cases

### TestRunCommand
Tests `ReferenceRepos.run_command` which lists, adds, removes, and toggles reference repositories and validates the associated arguments.

#### 1. List Action Calls List Reference Repos
- **Test Name**: `test_run_command_list_action_calls_list_reference_repos`
- **Description**: When the list action runs.
- **Expected Outcome**: It delegates to `_list_reference_repos` with the `user_cfg_file` from config.

#### 2. Valid Repo Operation Calls Expected Method (Add)
- **Test Name**: `test_run_command_valid_repo_operation_calls_expected_method[add]`
- **Description**: When the add action runs with a new name, url, and path.
- **Expected Outcome**: `add_reference_repo` is called once on `user_cfg_file` with the name, url, and path.

#### 3. Valid Repo Operation Calls Expected Method (Remove)
- **Test Name**: `test_run_command_valid_repo_operation_calls_expected_method[remove]`
- **Description**: When the remove action runs for an enabled repo.
- **Expected Outcome**: `remove_reference_repo` is called once on `user_cfg_file` with the name.

#### 4. Action Without Name Raises Exception (Add)
- **Test Name**: `test_run_command_action_without_name_raises_exception[add]`
- **Description**: When the add action runs without a name argument.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 5. Action Without Name Raises Exception (Remove)
- **Test Name**: `test_run_command_action_without_name_raises_exception[remove]`
- **Description**: When the remove action runs without a name argument.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 6. Raises For Invalid Repo Operation (Add Existing)
- **Test Name**: `test_run_command_raises_for_invalid_repo_operation[add_existing]`
- **Description**: When adding a repo that already exists.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 7. Raises For Invalid Repo Operation (Remove Nonexistent)
- **Test Name**: `test_run_command_raises_for_invalid_repo_operation[remove_nonexistent]`
- **Description**: When removing a repo that does not exist.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 8. Raises For Invalid Repo Operation (Missing Url)
- **Test Name**: `test_run_command_raises_for_invalid_repo_operation[missing_url]`
- **Description**: When the add action is missing the url field.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 9. Raises For Invalid Repo Operation (Missing Path)
- **Test Name**: `test_run_command_raises_for_invalid_repo_operation[missing_path]`
- **Description**: When the add action is missing the path field.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 10. Toggle Actions Call Setter With Expected Value (Enable)
- **Test Name**: `test_run_command_toggle_actions_call_setter_with_expected_value[enable]`
- **Description**: When the enable action runs.
- **Expected Outcome**: `set_reference_repos_enable_by_default` is called with `True`.

#### 11. Toggle Actions Call Setter With Expected Value (Disable)
- **Test Name**: `test_run_command_toggle_actions_call_setter_with_expected_value[disable]`
- **Description**: When the disable action runs.
- **Expected Outcome**: `set_reference_repos_enable_by_default` is called with `False`.

#### 12. Toggle Actions Call Setter With Expected Value (Enable Dissociate)
- **Test Name**: `test_run_command_toggle_actions_call_setter_with_expected_value[enable_dissociate]`
- **Description**: When the enable-dissociate action runs.
- **Expected Outcome**: `set_reference_repos_dissociate_by_default` is called with `True`.

#### 13. Toggle Actions Call Setter With Expected Value (Disable Dissociate)
- **Test Name**: `test_run_command_toggle_actions_call_setter_with_expected_value[disable_dissociate]`
- **Description**: When the disable-dissociate action runs.
- **Expected Outcome**: `set_reference_repos_dissociate_by_default` is called with `False`.

### TestListReferenceRepos
Tests `ReferenceRepos._list_reference_repos`, which reports the configured reference repositories from the user config.

#### 1. List Reference Repos (Populated)
- **Test Name**: `test_list_reference_repos[populated]`
- **Description**: When `_list_reference_repos` runs with one or more enabled reference repos.
- **Expected Outcome**: The URL and path of each enabled reference repo are looked up from the user config.

#### 2. List Reference Repos (Empty)
- **Test Name**: `test_list_reference_repos[empty]`
- **Description**: When `_list_reference_repos` runs with no enabled reference repos.
- **Expected Outcome**: The no-repos-configured message is printed and no repo URL lookup is performed.


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
