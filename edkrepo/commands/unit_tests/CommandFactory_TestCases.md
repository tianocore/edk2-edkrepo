# Test Cases for `command_factory` Module

## Test Cases

### TestCreateCompositeCommand
Tests the `command_factory.create_composite_command` function.

#### 1. Create Composite Command (Single Command)
- **Test Name**: `test_create_composite_command[single_command]`
- **Description**: When creating a composite command from a single command class.
- **Expected Outcome**: `create_composite_command` returns a `CompositeCommand` with exactly one command instance.

#### 2. Create Composite Command (Two Commands)
- **Test Name**: `test_create_composite_command[two_commands]`
- **Description**: When creating a composite command from two command classes.
- **Expected Outcome**: `create_composite_command` returns a `CompositeCommand` with exactly two command instances.

### TestIsCommand
Tests the `command_factory._is_command` function.

#### 1. Is Command (Base Class Returns False)
- **Test Name**: `test_is_command[base_class_returns_false]`
- **Description**: When evaluating the base command class itself.
- **Expected Outcome**: `_is_command` returns `False`.

#### 2. Is Command (Edkrepo Subclass Returns True)
- **Test Name**: `test_is_command[edkrepo_subclass_returns_true]`
- **Description**: When evaluating a subclass of the edkrepo command class.
- **Expected Outcome**: `_is_command` returns `True`.

#### 3. Is Command (Plain Class Returns False)
- **Test Name**: `test_is_command[plain_class_returns_false]`
- **Description**: When evaluating a plain class that does not implement the command interface.
- **Expected Outcome**: `_is_command` returns `False`.

#### 4. Is Command (Duck Typed Returns True)
- **Test Name**: `test_is_command[duck_typed_returns_true]`
- **Description**: When evaluating a duck-typed class that implements the command interface.
- **Expected Outcome**: `_is_command` returns `True`.

### TestGetCommands
Tests the `command_factory.get_commands` command-discovery function.

#### 1. Get Commands Skips Dunder Init And Non Python Files
- **Test Name**: `test_get_commands_skips_dunder_init_and_non_python_files`
- **Description**: When a command package directory contains `__init__.py` and non-Python files alongside a command module.
- **Expected Outcome**: Only the `.py` command module is imported and scanned; `__init__.py` and non-Python files are ignored.

#### 2. Get Commands Preferred Package Overrides Duplicates And Appends Last
- **Test Name**: `test_get_commands_preferred_package_overrides_duplicates_and_appends_last`
- **Description**: When a command name is defined in both a normal package and the preferred package.
- **Expected Outcome**: The command appears once, sourced from the preferred package, ordered after the non-preferred commands.


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
