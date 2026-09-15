# Test Cases for `SquashCommand` Class

## Test Cases

### TestRunCommand
Tests `SquashCommand.run_command`, which locates the repository, validates the target branch name and commit range, and squashes commits.

#### 1. Calls Get Git Repo Root
- **Test Name**: `test_run_command_calls_get_git_repo_root`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `get_git_repo_root` is called unconditionally to locate the repository root.

#### 2. Creates Repo At Git Root Path
- **Test Name**: `test_run_command_creates_repo_at_git_root_path`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `Repo` is instantiated with the path returned by `get_git_repo_root`.

#### 3. Branch Already Exists Raises Exception And Names Branch
- **Test Name**: `test_run_command_branch_already_exists_raises_exception_and_names_branch`
- **Description**: When the target branch name already exists.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised with the branch name.

#### 4. Branch Exists Check Uses New Branch And Repo
- **Test Name**: `test_run_command_branch_exists_check_uses_new_branch_and_repo`
- **Description**: When `run_command` checks whether the target branch exists.
- **Expected Outcome**: `branch_name_exists` is called with the new-branch arg and the `Repo` instance.

#### 5. Single Commit Raises Multiple Commits Required
- **Test Name**: `test_run_command_single_commit_raises_multiple_commits_required`
- **Description**: When `commit-ish` resolves to a single commit.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised indicating a commit range is required.

### TestBranchNameExists
Tests the module-level `branch_name_exists` helper, which reports whether a branch name matches an existing repo head.

#### 1. Branch Name Exists Reports Whether Name Matches An Existing Head (Branch Exists)
- **Test Name**: `test_branch_name_exists_reports_whether_name_matches_an_existing_head[branch_exists]`
- **Description**: When the queried branch name matches an existing repo head.
- **Expected Outcome**: `branch_name_exists` returns `True`.

#### 2. Branch Name Exists Reports Whether Name Matches An Existing Head (Branch Missing)
- **Test Name**: `test_branch_name_exists_reports_whether_name_matches_an_existing_head[branch_missing]`
- **Description**: When the queried branch name does not match any existing repo head.
- **Expected Outcome**: `branch_name_exists` returns `False`.


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
