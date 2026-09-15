# Test Cases for `StatusCommand` Class

## Test Cases

### TestRunCommand
Tests `StatusCommand.run_command` which resolves each repo source in the current combo and reports its git status.

#### 1. Queries Repo Sources From Current Combo
- **Test Name**: `test_run_command_queries_repo_sources_from_current_combo`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_repo_sources` is called with the current combo from the manifest.

#### 2. Creates Repo At Correct Local Path
- **Test Name**: `test_run_command_creates_repo_at_correct_local_path`
- **Description**: When `run_command` processes a repo source.
- **Expected Outcome**: `Repo` is instantiated with the absolute path formed from the workspace root and repo root.

#### 3. Calls Unconditional Workspace Function (Get Workspace Path)
- **Test Name**: `test_run_command_calls_unconditional_workspace_function[get_workspace_path]`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_workspace_path` is called unconditionally.

#### 4. Calls Unconditional Workspace Function (Get Workspace Manifest)
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
