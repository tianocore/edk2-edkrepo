# Test Cases for `CleanCommand` Class

## Test Cases

### TestRunCommand
Tests `CleanCommand.run_command` which runs `git clean` over every repo source in the current combo and reports the resulting output.

#### 1. Calls Git Clean For Each Repo Source
- **Test Name**: `test_run_command_calls_git_clean_for_each_repo_source`
- **Description**: When `run_command` executes over the repo sources of the current combo.
- **Expected Outcome**: `git.clean` is called once for each repo source.

#### 2. Prints Info Msg Only When Clean Returns Non Empty Output (Non Empty Output)
- **Test Name**: `test_run_command_prints_info_msg_only_when_clean_returns_non_empty_output[non_empty_output]`
- **Description**: When `git.clean` returns non-empty output.
- **Expected Outcome**: `print_info_msg` is called once with that output.

#### 3. Prints Info Msg Only When Clean Returns Non Empty Output (Empty Output)
- **Test Name**: `test_run_command_prints_info_msg_only_when_clean_returns_non_empty_output[empty_output]`
- **Description**: When `git.clean` returns an empty string.
- **Expected Outcome**: `print_info_msg` is not called.

#### 4. Git Clean Respects Force And Quiet Flags (No Force Dry Run)
- **Test Name**: `test_run_command_git_clean_respects_force_and_quiet_flags[no_force_dry_run]`
- **Description**: When `run_command` is invoked without force, so the clean runs as a dry run.
- **Expected Outcome**: The `git.clean` kwargs reflect the flag values from args.

#### 5. Git Clean Respects Force And Quiet Flags (Force Disables Dry Run)
- **Test Name**: `test_run_command_git_clean_respects_force_and_quiet_flags[force_disables_dry_run]`
- **Description**: When `run_command` is invoked with force set, disabling the dry run.
- **Expected Outcome**: The `git.clean` kwargs reflect the flag values from args.

#### 6. Git Clean Respects Force And Quiet Flags (Quiet Without Force)
- **Test Name**: `test_run_command_git_clean_respects_force_and_quiet_flags[quiet_without_force]`
- **Description**: When `run_command` is invoked with quiet but without force.
- **Expected Outcome**: The `git.clean` kwargs reflect the flag values from args.

#### 7. Git Clean Respects Force And Quiet Flags (Force And Quiet Enables Q)
- **Test Name**: `test_run_command_git_clean_respects_force_and_quiet_flags[force_and_quiet_enables_q]`
- **Description**: When `run_command` is invoked with both force and quiet set.
- **Expected Outcome**: The `git.clean` kwargs reflect the flag values from args.

#### 8. Git Clean Respects Force And Quiet Flags (Dirs Flag)
- **Test Name**: `test_run_command_git_clean_respects_force_and_quiet_flags[dirs_flag]`
- **Description**: When `run_command` is invoked with the dirs flag set.
- **Expected Outcome**: The `git.clean` kwargs reflect the flag values from args.

#### 9. Git Clean Respects Force And Quiet Flags (Include Ignored Flag)
- **Test Name**: `test_run_command_git_clean_respects_force_and_quiet_flags[include_ignored_flag]`
- **Description**: When `run_command` is invoked with the include_ignored flag set.
- **Expected Outcome**: The `git.clean` kwargs reflect the flag values from args.


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
