# Test Cases for `MaintenanceCommande` Class

## Test Cases

### TestRunCommand
Tests `MaintenanceCommande.run_command` which performs unconditional global maintenance and, when in a workspace with gc enabled, runs git maintenance per repo.

#### 1. Always Calls Set Long Path Support
- **Test Name**: `test_run_command_always_calls_set_long_path_support`
- **Description**: When `run_command` executes on any run.
- **Expected Outcome**: `set_long_path_support` is called unconditionally.

#### 2. Always Calls Clean Git Globalconfig
- **Test Name**: `test_run_command_always_calls_clean_git_globalconfig`
- **Description**: When `run_command` executes on any run.
- **Expected Outcome**: `clean_git_globalconfig` is called unconditionally.

#### 3. Skips Workspace Ops When No Gc Is Set
- **Test Name**: `test_run_command_skips_workspace_ops_when_no_gc_is_set`
- **Description**: When `--no-gc` is set.
- **Expected Outcome**: `get_workspace_path` is never called.

#### 4. Skips Gc When Outside Workspace
- **Test Name**: `test_run_command_skips_gc_when_outside_workspace`
- **Description**: When not in a valid workspace.
- **Expected Outcome**: `get_workspace_manifest` is never called.

#### 5. Runs Git Maintenance For Each Repo When In Workspace
- **Test Name**: `test_run_command_runs_git_maintenance_for_each_repo_when_in_workspace`
- **Description**: When in a valid workspace with gc enabled.
- **Expected Outcome**: Each repo has reflog expire, gc, and remote prune run.


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
