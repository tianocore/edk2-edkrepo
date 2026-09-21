# Test Cases for `UninstallCommand` Class

## Test Cases

### TestRunCommand
Tests `UninstallCommand.run_command` which forwards the remaining command-line arguments to `handle_uninstall` and exits with its return value.

#### 1. Calls Handle Uninstall With Remaining Argv
- **Test Name**: `test_run_command_calls_handle_uninstall_with_remaining_argv`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `handle_uninstall` is called with `sys.argv[2:]`.

#### 2. Calls Sys Exit With Handle Uninstall Result
- **Test Name**: `test_run_command_calls_sys_exit_with_handle_uninstall_result`
- **Description**: When `run_command` executes.
- **Expected Outcome**: The return value of `handle_uninstall` is passed directly to `sys.exit`.


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
