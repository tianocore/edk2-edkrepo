# Test Cases for `checkout_command` Module

## Test Cases

### TestCheckoutCommand
All unit tests for the `CheckoutCommand` class and its module-level helper function are contained in a single test class. Shared constants (combination names, paths, repo names, metadata keys, argument names, and config keys) are defined as class-level attributes and reused across tests.

#### `get_metadata`
Returns the command metadata dict including the command name, help text, and argument definitions.

##### 1. Returns Expected Metadata Structure — `test_get_metadata_returns_expected_structure`
- **Description**: Call `get_metadata` on a fresh `CheckoutCommand` instance.
- **Expected Outcome**: The returned dict has `name == 'checkout'`, a non-empty `help-text`, and an `arguments` list containing entries for `Combination` and `override`.

#### `run_command`
Resolves the workspace manifest, looks up the global manifest path, and delegates to `_checkout_combination`.

##### 1. Resolves Manifest and Delegates — `test_run_command_resolves_manifest_and_delegates`
- **Description**: `get_workspace_manifest` returns a valid manifest; `get_manifest_repo_path` and `_checkout_combination` are patched out.
- **Expected Outcome**: `_checkout_combination` is called once with the resolved combination, manifest, global manifest path, and the `verbose`/`override` flags from `args`.

#### `_checkout_combination`
Decides whether to call `checkout` for a valid combination name, or raise `EdkrepoInvalidParametersException` for an unknown one.

##### 1. Valid Combination Triggers Checkout — `test_valid_combination_triggers_checkout`
- **Description**: `combination_is_in_manifest` returns `True` for the supplied combination name; `get_repo_cache_obj` returns a local cache mock.
- **Expected Outcome**: `checkout` is called once with the combination, global manifest path, `verbose`, `override`, and the cache object; no exception is raised.

##### 2. Invalid Combination Raises Exception — `test_invalid_combination_raises_exception`
- **Description**: `combination_is_in_manifest` returns `False` for the supplied combination name.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised and `checkout` is never called.

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
