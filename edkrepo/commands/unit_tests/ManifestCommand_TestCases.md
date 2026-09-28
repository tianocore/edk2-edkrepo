# Test Cases for `ManifestCommand` Class

## Test Cases

### TestRunCommand
Tests `ManifestCommand.run_command` which lists available manifest repos, refreshes them, and gracefully handles workspace lookup failures.

#### 1. Calls List Available Manifest Repos
- **Test Name**: `test_run_command_calls_list_available_manifest_repos`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `list_available_manifest_repos` is called with the cfg and user_cfg files from config.

#### 2. Calls Pull All Manifest Repos
- **Test Name**: `test_run_command_calls_pull_all_manifest_repos`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `pull_all_manifest_repos` is called unconditionally to refresh all manifest repos.

#### 3. Handles Get Workspace Manifest Exception Gracefully (Workspace Invalid)
- **Test Name**: `test_run_command_handles_get_workspace_manifest_exception_gracefully[workspace_invalid]`
- **Description**: When `get_workspace_manifest` raises `EdkrepoWorkspaceInvalidException`.
- **Expected Outcome**: The exception does not propagate to the caller.

#### 4. Handles Get Workspace Manifest Exception Gracefully (Manifest Not Found)
- **Test Name**: `test_run_command_handles_get_workspace_manifest_exception_gracefully[manifest_not_found]`
- **Description**: When `get_workspace_manifest` raises `EdkrepoManifestNotFoundException`.
- **Expected Outcome**: The exception does not propagate to the caller.


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
