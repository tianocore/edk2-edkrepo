# Test Cases for `SyncCommand` Class

## Test Cases

### TestRunCommand
Tests `SyncCommand.run_command` which refreshes the workspace manifest repo, checks for dirty repos, and synchronizes the workspace.

#### 1. Calls Pull Workspace Manifest Repo With Correct Args
- **Test Name**: `test_run_command_calls_pull_workspace_manifest_repo_with_correct_args`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `pull_workspace_manifest_repo` is called with the initial manifest, config entries, and `source_manifest_repo` arg.

#### 2. Falls Back To Pull All Manifest Repos On Pull Failure
- **Test Name**: `test_run_command_falls_back_to_pull_all_manifest_repos_on_pull_failure`
- **Description**: When `pull_workspace_manifest_repo` raises an exception.
- **Expected Outcome**: `run_command` falls back to `pull_all_manifest_repos`.

#### 3. Calls Check Dirty Repos With Initial Manifest And Workspace Path
- **Test Name**: `test_run_command_calls_check_dirty_repos_with_initial_manifest_and_workspace_path`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `check_dirty_repos` is called with the initial manifest and the workspace path.

#### 4. Calls Unconditional Workspace Function (Get Workspace Path)
- **Test Name**: `test_run_command_calls_unconditional_workspace_function[get_workspace_path]`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_workspace_path` is called unconditionally.

#### 5. Calls Unconditional Workspace Function (Get Workspace Manifest)
- **Test Name**: `test_run_command_calls_unconditional_workspace_function[get_workspace_manifest]`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_workspace_manifest` is called unconditionally.


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
