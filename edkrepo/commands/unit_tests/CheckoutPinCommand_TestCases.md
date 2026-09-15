# Test Cases for `CheckoutPinCommand` Class

## Test Cases

### TestRunCommand
Tests `CheckoutPinCommand.run_command` which validates the pin file, performs the checkout, and updates workspace state.

#### 1. Run Command Calls Check Dirty Repos
- **Test Name**: `test_run_command_calls_check_dirty_repos`
- **Description**: When `run_command` executes with a valid pin.
- **Expected Outcome**: `check_dirty_repos` is called once with the workspace manifest and the workspace path.

#### 2. Run Command Writes Pin Combo Name
- **Test Name**: `test_run_command_writes_pin_combo_name`
- **Description**: When `run_command` executes with a valid pin file.
- **Expected Outcome**: `write_current_combo` is called using the `PIN_COMBO` format with the pin filename.

#### 3. Run Command Performs Sparse Reset When Enabled
- **Test Name**: `test_run_command_performs_sparse_reset_when_enabled`
- **Description**: When sparse checkout is enabled.
- **Expected Outcome**: `reset_sparse_checkout` is called before checkout.

#### 4. Run Command Deinit Error Does Not Stop Checkout
- **Test Name**: `test_run_command_deinit_error_does_not_stop_checkout`
- **Description**: When `deinit_full` raises an exception.
- **Expected Outcome**: The exception is caught and `checkout_repos` is still called.

#### 5. Run Command Maintains Submodules Even When Checkout Raises
- **Test Name**: `test_run_command_maintains_submodules_even_when_checkout_raises`
- **Description**: When `checkout_repos` raises an exception.
- **Expected Outcome**: `maintain_submodules` is still called in the `finally` block.

### TestPinMatchesProject
Tests the private `__pin_matches_project` which validates that a pin file matches the workspace manifest's project structure.

#### 1. Pin Matches Project Raises When Codename Differs
- **Test Name**: `test_pin_matches_project_raises_when_codename_differs`
- **Description**: When the pin and manifest codenames differ.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

#### 2. Pin Matches Project Raises When Pin Remotes Not Subset
- **Test Name**: `test_pin_matches_project_raises_when_pin_remotes_not_subset`
- **Description**: When the pin remotes are not a subset of the manifest remotes.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

#### 3. Pin Matches Project Warns When Combo Not In Manifest
- **Test Name**: `test_pin_matches_project_warns_when_combo_not_in_manifest`
- **Description**: When the pin combo is not present in the manifest.
- **Expected Outcome**: `print_warning_msg` is called with the combo name.

#### 4. Pin Matches Project Raises When Root Remote Pairs Disjoint
- **Test Name**: `test_pin_matches_project_raises_when_root_remote_pairs_disjoint`
- **Description**: When the pin and manifest source root/remote pairs share nothing.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

#### 5. Pin Matches Project Raises When Pin Commit Not Found In Repo
- **Test Name**: `test_pin_matches_project_raises_when_pin_commit_not_found_in_repo`
- **Description**: When the pinned commit cannot be located in the local repo.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

### TestGetPinPath
Tests the private `__get_pin_path` which resolves the on-disk path of the requested pin file.

#### 1. Get Pin Path Raises When Pin Cannot Be Located (No Xml Extension)
- **Test Name**: `test_get_pin_path_raises_when_pin_cannot_be_located[no_xml_extension]`
- **Description**: When the pin file cannot be found in the workspace and the pin name is given without an `.xml` extension.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 2. Get Pin Path Raises When Pin Cannot Be Located (With Xml Extension)
- **Test Name**: `test_get_pin_path_raises_when_pin_cannot_be_located[with_xml_extension]`
- **Description**: When the pin file cannot be found in the workspace and the pin name is given with an `.xml` extension.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 3. Get Pin Path Returns Normalized Path When Pinfile Is Absolute Existing File
- **Test Name**: `test_get_pin_path_returns_normalized_path_when_pinfile_is_absolute_existing_file`
- **Description**: When `args.pinfile` is an absolute path to an existing file.
- **Expected Outcome**: The normalized absolute path is returned without delegating to either resolution helper.

#### 4. Get Pin Path Delegates To Find Pin In Manifest Repo When Manifest Repo Path Given
- **Test Name**: `test_get_pin_path_delegates_to_find_pin_in_manifest_repo_when_manifest_repo_path_given`
- **Description**: When a manifest repo path is available.
- **Expected Outcome**: `__find_pin_in_manifest_repo` is called once with the pin name, manifest repo path, and configured pin path, and its result is returned.

### TestFindPinInManifestRepo
Tests the private `__find_pin_in_manifest_repo` which searches the manifest repository for the pin file.

#### 1. Find Pin In Manifest Repo Checks Subdir Then Root (Found In Pin Path Subdir)
- **Test Name**: `test_find_pin_in_manifest_repo_checks_subdir_then_root[found_in_pin_path_subdir]`
- **Description**: When the pin file exists at the configured pin path subdirectory of the manifest repo.
- **Expected Outcome**: The subdirectory path is returned.

#### 2. Find Pin In Manifest Repo Checks Subdir Then Root (Found At Manifest Repo Root)
- **Test Name**: `test_find_pin_in_manifest_repo_checks_subdir_then_root[found_at_manifest_repo_root]`
- **Description**: When the pin file is not in the pin path subdirectory but exists at the root of the manifest repo.
- **Expected Outcome**: The manifest repo root path is returned.

#### 3. Find Pin In Manifest Repo Checks Subdir Then Root (Not Found)
- **Test Name**: `test_find_pin_in_manifest_repo_checks_subdir_then_root[not_found]`
- **Description**: When the pin file exists at neither candidate location.
- **Expected Outcome**: `None` is returned.

### TestFindPinInWorkspace
Tests the private `__find_pin_in_workspace` which searches the workspace for the pin file.

#### 1. Find Pin In Workspace Checks Root Then Repo Dir (Found At Workspace Root)
- **Test Name**: `test_find_pin_in_workspace_checks_root_then_repo_dir[found_at_workspace_root]`
- **Description**: When the pin file exists at the root of the workspace.
- **Expected Outcome**: The workspace root path is returned.

#### 2. Find Pin In Workspace Checks Root Then Repo Dir (Found In Repo Dir)
- **Test Name**: `test_find_pin_in_workspace_checks_root_then_repo_dir[found_in_repo_dir]`
- **Description**: When the pin file is not at the workspace root but exists in the `repo/` directory.
- **Expected Outcome**: The `repo/` directory path is returned.

#### 3. Find Pin In Workspace Checks Root Then Repo Dir (Not Found)
- **Test Name**: `test_find_pin_in_workspace_checks_root_then_repo_dir[not_found]`
- **Description**: When the pin file exists at neither candidate location.
- **Expected Outcome**: `None` is returned.


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
