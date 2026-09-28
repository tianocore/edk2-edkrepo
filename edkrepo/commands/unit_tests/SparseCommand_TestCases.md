# Test Cases for `SparseCommand` Class

## Test Cases

### TestInit
Tests `SparseCommand.__init__`, which is inherited unchanged from the open-source module and constructs the command instance.

#### 1. Init Creates Instance Without Error
- **Test Name**: `test_init_creates_instance_without_error`
- **Description**: When constructing `SparseCommand` with no arguments.
- **Expected Outcome**: The instance is created successfully.

### TestRunCommand
Tests `SparseCommand.run_command`, which enables or disables sparse checkout and validates the requested state transition.

#### 1. Enable Performs Sparse Checkout
- **Test Name**: `test_run_command_enable_performs_sparse_checkout`
- **Description**: When enabling sparse while it is currently disabled.
- **Expected Outcome**: Dirty repos are checked and the sparse checkout is performed.

#### 2. Disable Resets Sparse Checkout
- **Test Name**: `test_run_command_disable_resets_sparse_checkout`
- **Description**: When disabling sparse while it is currently enabled.
- **Expected Outcome**: The sparse checkout is reset.

#### 3. Raises Sparse Exception For Invalid State (Both Flags)
- **Test Name**: `test_run_command_raises_sparse_exception_for_invalid_state[both_flags]`
- **Description**: When both the enable and disable flags are set.
- **Expected Outcome**: `EdkrepoSparseException` is raised.

#### 4. Raises Sparse Exception For Invalid State (Disable Already Disabled)
- **Test Name**: `test_run_command_raises_sparse_exception_for_invalid_state[disable_already_disabled]`
- **Description**: When disabling sparse while it is already disabled.
- **Expected Outcome**: `EdkrepoSparseException` is raised.

#### 5. Raises Sparse Exception For Invalid State (Enable Already Enabled)
- **Test Name**: `test_run_command_raises_sparse_exception_for_invalid_state[enable_already_enabled]`
- **Description**: When enabling sparse while it is already enabled.
- **Expected Outcome**: `EdkrepoSparseException` is raised.

### TestGetMetadata
Tests `SparseCommand.get_metadata`, which is inherited unchanged from the open-source module and reports the command name, help text, and arguments.

#### 1. Get Metadata Returns Expected Top Level Field (Name)
- **Test Name**: `test_get_metadata_returns_expected_top_level_field[name]`
- **Description**: When `get_metadata` is called.
- **Expected Outcome**: The metadata reports `sparse` as the command name.

#### 2. Get Metadata Returns Expected Top Level Field (Help Text)
- **Test Name**: `test_get_metadata_returns_expected_top_level_field[help_text]`
- **Description**: When `get_metadata` is called.
- **Expected Outcome**: The metadata help text matches the sparse command description.

#### 3. Get Metadata Includes Argument With Help Text (Enable)
- **Test Name**: `test_get_metadata_includes_argument_with_help_text[enable]`
- **Description**: When `get_metadata` is called.
- **Expected Outcome**: The metadata includes the `enable` argument with its help text.

#### 4. Get Metadata Includes Argument With Help Text (Disable)
- **Test Name**: `test_get_metadata_includes_argument_with_help_text[disable]`
- **Description**: When `get_metadata` is called.
- **Expected Outcome**: The metadata includes the `disable` argument with its help text.


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
