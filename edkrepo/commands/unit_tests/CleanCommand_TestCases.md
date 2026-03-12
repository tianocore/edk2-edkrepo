# Test Cases for `clean_command` Module

## Test Cases

### TestCleanCommand
All unit tests for the `CleanCommand` class are contained in a single test class. Shared constants (workspace path, combo name, repo roots, output strings, metadata keys, and argument names) are defined as class-level attributes and reused across tests.

#### `get_metadata`
Returns the command metadata dict including the command name, help text, and argument definitions.

##### 1. Returns Expected Metadata Structure — `test_get_metadata_returns_expected_structure`
- **Description**: Call `get_metadata` on a fresh `CleanCommand` instance.
- **Expected Outcome**: The returned dict has `name == 'clean'`, a `help-text` key, and an `arguments` list containing entries for `force`, `quiet`, `dirs`, and `include-ignored`.

#### `run_command`
Iterates over every repository in the current combo and runs `git clean` with flags derived from the command-line arguments, printing any output produced.

##### 1. Dry-Run Mode Produces Output — Print Called — `test_dry_run_produces_output_print_called`
- **Description**: `args.force` is `False`; `repo.git.clean` is called with `n=True` (dry-run) and returns a non-empty result string.
- **Expected Outcome**: `repo.git.clean` is called with `f=False, d=False, n=True, q=False, x=False`; `ui_functions.print_info_msg` is called once with the result string.

##### 2. Force Mode Produces Output — Print Called — `test_force_mode_produces_output_print_called`
- **Description**: `args.force` is `True`; `repo.git.clean` is called with `f=True` and `n=False` and returns a non-empty result string.
- **Expected Outcome**: `repo.git.clean` is called with `f=True, d=True, n=False, q=False, x=False`; `ui_functions.print_info_msg` is called once with the result string.

##### 3. Clean Produces No Output — Print Not Called — `test_clean_produces_no_output_print_not_called`
- **Description**: `args.force` is `True`; `repo.git.clean` returns an empty string.
- **Expected Outcome**: `ui_functions.print_info_msg` is never called.

##### 4. Quiet and Force Both True — `q=True` Passed — `test_quiet_and_force_passes_q_true`
- **Description**: `args.quiet` is `True` and `args.force` is `True`; the compound condition `q=(args.quiet and args.force)` evaluates to `True`.
- **Expected Outcome**: `repo.git.clean` is called with `q=True`, `f=True`, and `n=False`.

##### 5. Multiple Repos — Each Repo Is Cleaned — `test_multiple_repos_each_cleaned`
- **Description**: The manifest returns two repo sources for the current combo.
- **Expected Outcome**: `Repo` is instantiated twice and `git.clean` is called once per repo.

##### 6. Include Ignored Files — `x=True` Passed — `test_include_ignored_passes_x_true`
- **Description**: `args.include_ignored` is `True` and `args.force` is `True`.
- **Expected Outcome**: `repo.git.clean` is called with `x=True`, `f=True`, and `n=False`.

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
