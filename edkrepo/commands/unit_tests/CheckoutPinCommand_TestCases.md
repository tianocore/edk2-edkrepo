# Test Cases for `checkout_pin_command` Module

## Test Cases

### TestCheckoutPinCommand
All unit tests for the `CheckoutPinCommand` class and its module-level helper functions are contained in a single test class. Shared constants (paths, project names, remote info, combo names, repo roots, metadata keys, argument names, and config keys) are defined as class-level attributes and reused across tests.

#### `get_metadata`
Returns the command metadata dict including the command name, alias, help text, and argument definitions.

##### 1. Returns Expected Metadata Structure — `test_get_metadata_returns_expected_structure`
- **Description**: Call `get_metadata` on a fresh `CheckoutPinCommand` instance.
- **Expected Outcome**: The returned dict has `name == 'checkout-pin'`, `alias == 'chp'`, a `help-text` key, and an `arguments` list containing entries for `pinfile`, `override`, and `source-manifest-repo`.

#### `run_command`
Resolves the workspace path and manifest, locates the pin file, validates project compatibility, checks out repos, and updates the current combo.

##### 1. Performs Checkout and Writes Combo — `test_run_command_performs_checkout_and_writes_combo`
- **Description**: All external dependencies are patched; `sparse_checkout_enabled` returns `False`; `get_repo_cache_obj` returns `None`; `_get_pin_path`, `ManifestXml`, `checkout_repos`, and `maintain_submodules` are patched out.
- **Expected Outcome**: `checkout_repos` is called once and `manifest.write_current_combo` is called once.

#### `_get_pin_path`
Locates the pin XML file via absolute path, manifest repo, or workspace; raises `EdkrepoInvalidParametersException` if not found.

##### 1. Absolute Path Resolved — `test_get_pin_path_absolute_path_resolved`
- **Description**: `args.pinfile` is an absolute path and `os.path.isfile` returns `True`.
- **Expected Outcome**: Returns the normalized absolute path.

##### 2. Resolved via Manifest Repo — `test_get_pin_path_resolved_via_manifest_repo`
- **Description**: `os.path.isabs` returns `False`; `manifest_repo_path` is not `None`; `_find_pin_in_manifest_repo` is patched to return the expected path; pin name has no `.xml` extension.
- **Expected Outcome**: `_find_pin_in_manifest_repo` is called with `'test.xml'`, the manifest repo path, and the pin subdir; the returned path is returned.

##### 3. Resolved via Workspace — `test_get_pin_path_resolved_via_workspace`
- **Description**: `os.path.isabs` returns `False`; `manifest_repo_path` is `None`; `_find_pin_in_workspace` is patched to return the expected path.
- **Expected Outcome**: `_find_pin_in_workspace` is called with the workspace path and pin filename; the returned path is returned.

##### 4. Not Found Raises Exception — `test_get_pin_path_not_found_raises_exception`
- **Description**: `os.path.isabs` returns `False`; `manifest_repo_path` is `None`; `_find_pin_in_workspace` returns `None`.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### `_find_pin_in_manifest_repo`
Searches for the pin file under the manifest repo pin_path subdirectory and root; returns the path or `None`.

##### 1. Found at Expected Subdirectory Path — `test_find_pin_in_manifest_repo_found_at_expected_path`
- **Description**: `os.path.isfile` returns `True` only for the expected subdirectory path.
- **Expected Outcome**: Returns the normalized subdirectory path.

##### 2. Found at Root of Manifest Repo — `test_find_pin_in_manifest_repo_found_at_root`
- **Description**: `os.path.isfile` returns `True` only for the manifest repo root path (corner case).
- **Expected Outcome**: Returns the normalized root path.

##### 3. Not Found Returns None — `test_find_pin_in_manifest_repo_not_found_returns_none`
- **Description**: `os.path.isfile` always returns `False`.
- **Expected Outcome**: Returns `None`.

#### `_find_pin_in_workspace`
Searches for the pin file at the workspace root and `repo/` subdirectory; returns the path or `None`.

##### 1. Found at Workspace Root — `test_find_pin_in_workspace_found_at_root`
- **Description**: `os.path.isfile` returns `True` only for the workspace root path.
- **Expected Outcome**: Returns the normalized workspace root path.

##### 2. Found in `repo/` Subdirectory — `test_find_pin_in_workspace_found_in_repo_subdir`
- **Description**: `os.path.isfile` returns `True` only for the `repo/` subdirectory path.
- **Expected Outcome**: Returns the normalized `repo/` path.

##### 3. Not Found Returns None — `test_find_pin_in_workspace_not_found_returns_none`
- **Description**: `os.path.isfile` always returns `False`.
- **Expected Outcome**: Returns `None`.

#### `_pin_matches_project`
Validates that the pin's codename, remotes, combo, and repo/remote mapping are compatible with the manifest.

##### 1. Codename Mismatch Raises Exception — `test_pin_matches_project_codename_mismatch_raises_exception`
- **Description**: `pin.project_info.codename` differs from `manifest.project_info.codename`.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

##### 2. Remotes Not Subset Raises Exception — `test_pin_matches_project_remotes_not_subset_raises_exception`
- **Description**: Codenames match; pin has a remote not present in the manifest's remote list.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

##### 3. Combo Not in Manifest Prints Warning — `test_pin_matches_project_combo_not_in_manifest_prints_warning`
- **Description**: Codenames and remotes match; `combinations_in_manifest` does not include the pin's current combo; pin and manifest share the same repo source.
- **Expected Outcome**: `ui_functions.print_warning_msg` is called once; no exception is raised.

##### 4. Root/Remote Mapping Disjoint Raises Exception — `test_pin_matches_project_root_remote_disjoint_raises_exception`
- **Description**: Codenames and remotes match; pin and manifest sources have completely different root/remote pairs.
- **Expected Outcome**: `EdkrepoProjectMismatchException` is raised.

##### 5. All Validations Pass — `test_pin_matches_project_all_validations_pass`
- **Description**: Codenames, remotes, combo, and source root/remote mapping all match; `Repo.commit` returns a valid object.
- **Expected Outcome**: `repo.commit` is called once with `COMMIT_SHA`; no exception is raised.

##### 6. ValueError Falls Back to Default Combo — `test_pin_matches_project_value_error_falls_back_to_default_combo`
- **Description**: Codenames, remotes, and combo match; `manifest.get_repo_sources` raises `ValueError` on the first call (pin combo not found in manifest), then returns sources on the second call (default combo).
- **Expected Outcome**: `manifest.get_repo_sources` is called twice; the second call uses `manifest.general_config.default_combo`.

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
