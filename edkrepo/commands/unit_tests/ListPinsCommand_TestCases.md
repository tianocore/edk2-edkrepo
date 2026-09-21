# Test Cases for `ListPinsCommand` Class

## Test Cases

### TestRunCommand
Tests `ListPinsCommand.run_command`, which resolves the manifest, refreshes the manifest repo, and lists the available pins.

#### 1. Run Command Returns Early When Pin Path Is None
- **Test Name**: `test_run_command_returns_early_when_pin_path_is_none`
- **Description**: When `manifest.general_config.pin_path` is `None`.
- **Expected Outcome**: `run_command` returns before walking any directories.

#### 2. Run Command Pulls Workspace Manifest Repo
- **Test Name**: `test_run_command_pulls_workspace_manifest_repo`
- **Description**: When `run_command` executes inside a workspace.
- **Expected Outcome**: `pull_workspace_manifest_repo` is called to refresh the manifest repo.

#### 3. Run Command Calls Find Project When Outside Workspace With Project
- **Test Name**: `test_run_command_calls_find_project_when_outside_workspace_with_project`
- **Description**: When not in a workspace but `--project` is provided.
- **Expected Outcome**: `find_project_in_all_indices` is called.

#### 4. Raises When Not In Workspace Without Project (Run Command)
- **Test Name**: `test_raises_when_not_in_workspace_without_project[run_command]`
- **Description**: When not in a workspace and no `--project` is given, calling `run_command`.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

### TestResolveManifestAndDirectory
Tests `ListPinsCommand._resolve_manifest_and_directory`, which resolves the manifest and its directory from the workspace or the `--project` argument.

#### 1. Resolve Manifest And Directory Returns Workspace Manifest
- **Test Name**: `test_resolve_manifest_and_directory_returns_workspace_manifest`
- **Description**: When inside a workspace.
- **Expected Outcome**: `_resolve_manifest_and_directory` returns the workspace manifest.

#### 2. Resolve Manifest And Directory Uses Project Arg As Fallback
- **Test Name**: `test_resolve_manifest_and_directory_uses_project_arg_as_fallback`
- **Description**: When not in a workspace but `--project` is given.
- **Expected Outcome**: `_resolve_manifest_and_directory` uses `find_project_in_all_indices`.

#### 3. Raises When Not In Workspace Without Project (Resolve Manifest And Directory)
- **Test Name**: `test_raises_when_not_in_workspace_without_project[resolve_manifest_and_directory]`
- **Description**: When not in a workspace and no `--project` is given, calling `_resolve_manifest_and_directory`.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.


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
