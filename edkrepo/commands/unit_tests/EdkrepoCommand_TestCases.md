# Test Cases for `EdkrepoCommand` Class

## Test Cases

### TestGetMetadata
Tests `EdkrepoCommand.get_metadata`, the abstract base method that must be overridden by subclasses.

#### 1. Raises Not Implemented (Get Metadata)
- **Test Name**: `test_raises_not_implemented[get_metadata]`
- **Description**: When calling `get_metadata` on the base class.
- **Expected Outcome**: `NotImplementedError` is raised.

### TestRunCommand
Tests `EdkrepoCommand.run_command`, the abstract base method that must be overridden by subclasses.

#### 1. Raises Not Implemented (Run Command)
- **Test Name**: `test_raises_not_implemented[run_command]`
- **Description**: When calling `run_command` on the base class.
- **Expected Outcome**: `NotImplementedError` is raised.


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
