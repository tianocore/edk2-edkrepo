# Test Cases for `CheckoutCommand` Class

## Test Cases

### TestRunCommand
Tests `CheckoutCommand.run_command` which validates the requested combination against the workspace manifest and performs the checkout.

#### 1. Valid Combination Calls Checkout
- **Test Name**: `test_run_command_valid_combination_calls_checkout`
- **Description**: When the requested combination exists in the workspace manifest.
- **Expected Outcome**: `checkout` is called once with the resolved combination, global manifest path, verbose, and override arguments.

#### 2. Valid Combination Uses Global Manifest Path From Manifest Repo
- **Test Name**: `test_run_command_valid_combination_uses_global_manifest_path_from_manifest_repo`
- **Description**: When the combination is valid and the global manifest path is resolved from the manifest repository.
- **Expected Outcome**: `get_manifest_repo_path` is called with the `source_manifest_repo` from the workspace manifest.

#### 3. Invalid Combination Raises Exception
- **Test Name**: `test_run_command_invalid_combination_raises_exception`
- **Description**: When the requested combination is not in the manifest.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 4. Invalid Combination Exception Names Combination
- **Test Name**: `test_run_command_invalid_combination_exception_names_combination`
- **Description**: When the requested combination is not in the manifest.
- **Expected Outcome**: The exception message contains the combination name that was not found.

#### 5. Invalid Combination Does Not Call Checkout
- **Test Name**: `test_run_command_invalid_combination_does_not_call_checkout`
- **Description**: When the requested combination is not in the manifest.
- **Expected Outcome**: `checkout` is never called.


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
