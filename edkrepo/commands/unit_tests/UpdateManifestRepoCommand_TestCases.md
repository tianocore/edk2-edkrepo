# Test Cases for `UpdateManifestRepoCommand` Class

## Test Cases

### TestRunCommand
Tests `UpdateManifestRepoCommand.run_command` which refreshes all configured manifest repos, optionally with a hard reset.

#### 1. Passes Hard Flag To Pull All Manifest Repos (Hard)
- **Test Name**: `test_run_command_passes_hard_flag_to_pull_all_manifest_repos[hard]`
- **Description**: When `args.hard` is `True`.
- **Expected Outcome**: `args.hard` is forwarded as `reset_hard` to `pull_all_manifest_repos`, called exactly once.

#### 2. Passes Hard Flag To Pull All Manifest Repos (Not Hard)
- **Test Name**: `test_run_command_passes_hard_flag_to_pull_all_manifest_repos[not_hard]`
- **Description**: When `args.hard` is `False`.
- **Expected Outcome**: `args.hard` is forwarded as `reset_hard` to `pull_all_manifest_repos`, called exactly once.


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
