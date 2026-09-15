# Test Cases for `CompositeCommand` Class

## Test Cases

### TestGetMetadata
Tests `CompositeCommand.get_metadata`, which looks up the metadata for a registered command and appends the standard arguments.

#### 1. Get Metadata Returns Metadata For Registered Command
- **Test Name**: `test_get_metadata_returns_metadata_for_registered_command`
- **Description**: When requesting metadata for a command that has been added.
- **Expected Outcome**: `get_metadata` returns the metadata dict for that command.

#### 2. Get Metadata Returns None For Unknown Command
- **Test Name**: `test_get_metadata_returns_none_for_unknown_command`
- **Description**: When no command matches the given name.
- **Expected Outcome**: `get_metadata` returns `None`.

#### 3. Get Metadata Includes Standard Argument (Performance)
- **Test Name**: `test_get_metadata_includes_standard_argument[performance]`
- **Description**: When retrieving metadata that includes the performance standard argument.
- **Expected Outcome**: `get_metadata` includes the standard argument class in the metadata arguments list.

#### 4. Get Metadata Includes Standard Argument (Verbose)
- **Test Name**: `test_get_metadata_includes_standard_argument[verbose]`
- **Description**: When retrieving metadata that includes the verbose standard argument.
- **Expected Outcome**: `get_metadata` includes the standard argument class in the metadata arguments list.

#### 5. Get Metadata Includes Standard Argument (Color)
- **Test Name**: `test_get_metadata_includes_standard_argument[color]`
- **Description**: When retrieving metadata that includes the color standard argument.
- **Expected Outcome**: `get_metadata` includes the standard argument class in the metadata arguments list.

### TestRunCommand
Tests `CompositeCommand.run_command`, which routes execution to the matching command and initializes the color console.

#### 1. Run Command Routes By Name
- **Test Name**: `test_run_command_routes_by_name`
- **Description**: When `run_command` is called by command name.
- **Expected Outcome**: It delegates to the matching command.

#### 2. Run Command Routes By Alias
- **Test Name**: `test_run_command_routes_by_alias`
- **Description**: When `run_command` is called by command alias.
- **Expected Outcome**: It delegates to the matching command.

#### 3. Run Command Sets Color Attributes On Args
- **Test Name**: `test_run_command_sets_color_attributes_on_args`
- **Description**: When `run_command` initializes the color console.
- **Expected Outcome**: It sets `strip_color` and `convert_ansi` on args from `init_color_console`.

### TestCommandList
Tests `CompositeCommand.command_list`, which returns the registered command names in alphabetical order.

#### 1. Command List Returns Sorted Names
- **Test Name**: `test_command_list_returns_sorted_names`
- **Description**: When requesting the command list regardless of insertion order.
- **Expected Outcome**: `command_list` returns command names in alphabetical order.


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
