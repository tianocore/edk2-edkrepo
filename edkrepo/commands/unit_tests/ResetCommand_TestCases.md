# Test Cases for `ResetCommand` Class

## Test Cases

### TestRunCommand
Tests `ResetCommand.run_command` which resolves each repo source and resets its head, optionally discarding the working tree.

#### 1. Creates Repo At Correct Local Path
- **Test Name**: `test_run_command_creates_repo_at_correct_local_path`
- **Description**: When `run_command` processes a repo source.
- **Expected Outcome**: `Repo` is instantiated with the absolute path formed from the workspace root and repo root.

#### 2. Calls Unconditional Workspace Function (Get Workspace Path)
- **Test Name**: `test_run_command_calls_unconditional_workspace_function[get_workspace_path]`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_workspace_path` is called unconditionally.

#### 3. Calls Unconditional Workspace Function (Get Workspace Manifest)
- **Test Name**: `test_run_command_calls_unconditional_workspace_function[get_workspace_manifest]`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_workspace_manifest` is called unconditionally.

#### 4. Resets Repos With Correct Working Tree (Soft Reset)
- **Test Name**: `test_run_command_resets_repos_with_correct_working_tree[soft_reset]`
- **Description**: When the hard flag is not set.
- **Expected Outcome**: Each repo head is reset with `working_tree=False`.

#### 5. Resets Repos With Correct Working Tree (Hard Reset)
- **Test Name**: `test_run_command_resets_repos_with_correct_working_tree[hard_reset]`
- **Description**: When the hard flag is set.
- **Expected Outcome**: Each repo head is reset with `working_tree=True`.


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
