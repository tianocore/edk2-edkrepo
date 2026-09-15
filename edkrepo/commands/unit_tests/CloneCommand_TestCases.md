# Test Cases for `CloneCommand` Class

## Test Cases

### TestInit
Tests `CloneCommand.__init__`, which is inherited unchanged from the open-source module.

#### 1. Init Creates Instance Without Error
- **Test Name**: `test_init_creates_instance_without_error`
- **Description**: When constructing `CloneCommand` with no arguments.
- **Expected Outcome**: The instance is created successfully.

### TestGetMetadata
Tests `CloneCommand.get_metadata`, which is inherited unchanged from the open-source module and validates the expected set of argument names.

#### 1. Get Metadata Includes Expected Argument Names
- **Test Name**: `test_get_metadata_includes_expected_argument_names`
- **Description**: When `get_metadata` is called.
- **Expected Outcome**: The metadata includes exactly the expected set of argument names.

### TestResolveReferenceSettings
Tests `CloneCommand._resolve_reference_settings`, which is inherited unchanged from the open-source module and resolves reference-repo settings from config defaults and args overrides.

#### 1. Resolve Reference Settings Uses Config Defaults
- **Test Name**: `test_resolve_reference_settings_uses_config_defaults`
- **Description**: When no override flags are set on args.
- **Expected Outcome**: `_resolve_reference_settings` returns the reference/dissociate defaults from config.

#### 2. Resolve Reference Settings Builds Path Map When Reference Enabled
- **Test Name**: `test_resolve_reference_settings_builds_path_map_when_reference_enabled`
- **Description**: When `use_reference` is `True`.
- **Expected Outcome**: `_resolve_reference_settings` builds the `reference_path_map` from config.

#### 3. Resolve Reference Settings Flag Overrides Setting (Reference If Able Enables)
- **Test Name**: `test_resolve_reference_settings_flag_overrides_setting[reference_if_able_enables]`
- **Description**: When the `reference_if_able` flag is set on args over a disabled default.
- **Expected Outcome**: `use_reference` is overridden to `True`.

#### 4. Resolve Reference Settings Flag Overrides Setting (No Reference If Able Disables)
- **Test Name**: `test_resolve_reference_settings_flag_overrides_setting[no_reference_if_able_disables]`
- **Description**: When the `no_reference_if_able` flag is set on args over an enabled default.
- **Expected Outcome**: `use_reference` is overridden to `False`.

#### 5. Resolve Reference Settings Flag Overrides Setting (Dissociate Enables)
- **Test Name**: `test_resolve_reference_settings_flag_overrides_setting[dissociate_enables]`
- **Description**: When the `dissociate` flag is set on args over a disabled default.
- **Expected Outcome**: `use_dissociate` is overridden to `True`.

#### 6. Resolve Reference Settings Flag Overrides Setting (No Dissociate Disables)
- **Test Name**: `test_resolve_reference_settings_flag_overrides_setting[no_dissociate_disables]`
- **Description**: When the `no_dissociate` flag is set on args over an enabled default.
- **Expected Outcome**: `use_dissociate` is overridden to `False`.

### TestRunCommand
Tests `CloneCommand.run_command`, the open-source-specific clone orchestration behavior.

#### 1. Raises When Workspace Is Not Empty
- **Test Name**: `test_run_command_raises_when_workspace_is_not_empty`
- **Description**: When the workspace directory exists and contains files.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 2. Wraps Manifest Not Found As Invalid Parameters
- **Test Name**: `test_run_command_wraps_manifest_not_found_as_invalid_parameters`
- **Description**: When `EdkrepoManifestNotFoundException` is raised during project lookup.
- **Expected Outcome**: It is converted into an `EdkrepoInvalidParametersException`.

#### 3. Skips Submodules When Flag Set
- **Test Name**: `test_run_command_skips_submodules_when_flag_set`
- **Description**: When `skip_submodule` is `True`.
- **Expected Outcome**: `maintain_submodules` is not called.

#### 4. Writes Matched Combo When Combination Specified
- **Test Name**: `test_run_command_writes_matched_combo_when_combination_specified`
- **Description**: When `args.Combination` matches a combination in the manifest.
- **Expected Outcome**: The matched combo name is written as the current combo.

#### 5. Raises When Combination Does Not Match Manifest
- **Test Name**: `test_run_command_raises_when_combination_does_not_match_manifest`
- **Description**: When `args.Combination` cannot be matched to any combination in the manifest.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised and the local manifest directory is removed.

#### 6. Uses Current Combo For Pin File
- **Test Name**: `test_run_command_uses_current_combo_for_pin_file`
- **Description**: When no `Combination` is specified and the manifest is a pin file.
- **Expected Outcome**: The pin file's `current_combo` is used to fetch repo sources, without writing a new current combo.

#### 7. Raises When Local Roots Duplicated
- **Test Name**: `test_run_command_raises_when_local_roots_duplicated`
- **Description**: When two or more repo sources in the resolved combo share the same local root.
- **Expected Outcome**: `EdkrepoManifestInvalidException` is raised and the local manifest directory is removed.

#### 8. Run Command Invokes Expected Action (Clone Repos Called)
- **Test Name**: `test_run_command_invokes_expected_action[clone_repos_called]`
- **Description**: When `run_command` performs a successful clone.
- **Expected Outcome**: `clone_repos` is invoked as the expected internal action.

#### 9. Run Command Invokes Expected Action (Maintain Submodules Called)
- **Test Name**: `test_run_command_invokes_expected_action[maintain_submodules_called]`
- **Description**: When `run_command` performs a successful clone.
- **Expected Outcome**: `maintain_submodules` is invoked as the expected internal action.

#### 10. Sparse Checkout Enable Logic (No Sparse Settings Forces Disabled)
- **Test Name**: `test_run_command_sparse_checkout_enable_logic[no_sparse_settings_forces_disabled]`
- **Description**: When the manifest has no `sparse_settings`, even if `args.sparse` is `True`.
- **Expected Outcome**: `sparse_checkout` is not called.

#### 11. Sparse Checkout Enable Logic (Sparse By Default Enables)
- **Test Name**: `test_run_command_sparse_checkout_enable_logic[sparse_by_default_enables]`
- **Description**: When the manifest's `sparse_settings.sparse_by_default` is `True`.
- **Expected Outcome**: `sparse_checkout` is called.

#### 12. Sparse Checkout Enable Logic (Nosparse Overrides Sparse By Default)
- **Test Name**: `test_run_command_sparse_checkout_enable_logic[nosparse_overrides_sparse_by_default]`
- **Description**: When `args.nosparse` is `True` even though `sparse_by_default` is `True`.
- **Expected Outcome**: `sparse_checkout` is not called.

#### 13. Sparse Checkout Enable Logic (Args Sparse Enables When Settings Present)
- **Test Name**: `test_run_command_sparse_checkout_enable_logic[args_sparse_enables_when_settings_present]`
- **Description**: When `args.sparse` is `True` and `sparse_settings` is present but `sparse_by_default` is `False`.
- **Expected Outcome**: `sparse_checkout` is called.


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
