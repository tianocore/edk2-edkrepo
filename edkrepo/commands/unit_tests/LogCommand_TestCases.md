# Test Cases for `LogCommand` Class

## Test Cases

### TestRunCommand
Tests `LogCommand.run_command` which validates the `--number` argument, sorts commits, and optionally pipes output through `less`.

#### 1. Run Command Returns Early When Number Is Not Integer
- **Test Name**: `test_run_command_returns_early_when_number_is_not_integer`
- **Description**: When `--number` is not a valid integer.
- **Expected Outcome**: `run_command` returns without calling `sort_commits`.

#### 2. Run Command Opens Less When Available
- **Test Name**: `test_run_command_opens_less_when_available`
- **Description**: When `find_less` returns a valid path.
- **Expected Outcome**: `subprocess.Popen` is called to display the output.

#### 3. Run Command Calls Sort Commits With Correct Number (Integer String)
- **Test Name**: `test_run_command_calls_sort_commits_with_correct_number[integer_string]`
- **Description**: When `--number` is an integer string.
- **Expected Outcome**: `sort_commits` receives the value converted to an int.

#### 4. Run Command Calls Sort Commits With Correct Number (None)
- **Test Name**: `test_run_command_calls_sort_commits_with_correct_number[none]`
- **Description**: When `--number` is `None`.
- **Expected Outcome**: `sort_commits` receives `None`.


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
