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
Iterates over every repository in the current combo and runs `git clean` with flags derived from the command-line arguments, printing any output produced. The `q` flag maps directly to `args.quiet`.

##### 1. No Force — `n=True` — Print Called — `test_no_force_sets_n_true_print_called`
- **Description**: `args.force` is `False`; `repo.git.clean` is called with `n=True` (dry-run) and returns a non-empty result string.
- **Expected Outcome**: `repo.git.clean` is called with `f=False, d=False, n=True, q=False, x=False`; `ui_functions.print_info_msg` is called once with the result string.

##### 2. Force — `n=False` — Print Called — `test_force_sets_n_false_print_called`
- **Description**: `args.force` is `True`; `repo.git.clean` is called with `f=True` and `n=False` and returns a non-empty result string.
- **Expected Outcome**: `repo.git.clean` is called with `f=True, d=True, n=False, q=False, x=False`; `ui_functions.print_info_msg` is called once with the result string.

##### 3. Clean Produces No Output — Print Not Called — `test_clean_produces_no_output_print_not_called`
- **Description**: `args.force` is `True`; `repo.git.clean` returns an empty string.
- **Expected Outcome**: `ui_functions.print_info_msg` is never called.

##### 4. Quiet=False, Force=False — `q=False` — `test_quiet_false_force_false_passes_q_false`
- **Description**: Both `args.quiet` and `args.force` are `False`.
- **Expected Outcome**: `repo.git.clean` is called with `q=False`, `f=False`, and `n=True`.

##### 5. Quiet=False, Force=True — `q=False` — `test_quiet_false_force_true_passes_q_false`
- **Description**: `args.quiet` is `False` and `args.force` is `True`.
- **Expected Outcome**: `repo.git.clean` is called with `q=False`, `f=True`, and `n=False`.

##### 6. Quiet=True, Force=False — `q=True` — `test_quiet_true_force_false_passes_q_true`
- **Description**: `args.quiet` is `True` and `args.force` is `False`. The `q` flag maps directly to `args.quiet`, so the user’s explicit `--quiet` request is respected even without `--force`.
- **Expected Outcome**: `repo.git.clean` is called with `q=True`, `f=False`, and `n=True`.

##### 7. Quiet=True, Force=True — `q=True` — `test_quiet_true_force_true_passes_q_true`
- **Description**: Both `args.quiet` and `args.force` are `True`.
- **Expected Outcome**: `repo.git.clean` is called with `q=True`, `f=True`, and `n=False`.

##### 8. Multiple Repos — Each Repo Is Cleaned — `test_multiple_repos_each_cleaned`
- **Description**: The manifest returns two repo sources for the current combo.
- **Expected Outcome**: `Repo` is instantiated twice and `git.clean` is called once per repo.

##### 9. Include Ignored Files — `x=True` Passed — `test_include_ignored_passes_x_true`
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
