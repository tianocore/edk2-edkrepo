# Test Cases for `F2fCherryPickCommand` Class

## Test Cases

### TestRunCommand
Tests `F2fCherryPickCommand.run_command`, which lists templates, validates arguments, and orchestrates new, resumed, and aborted cherry picks.

#### 1. List Templates Calls List Templates And Returns
- **Test Name**: `test_run_command_list_templates_calls_list_templates_and_returns`
- **Description**: When `list_templates` is set.
- **Expected Outcome**: `_list_templates` is called and the command returns early without completing a cherry pick.

#### 2. Raises When Commit Missing Without Continue Or Abort
- **Test Name**: `test_run_command_raises_when_commit_missing_without_continue_or_abort`
- **Description**: When no commit is given and neither `--continue` nor `--abort` is set.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 3. New Cherry Pick Calls Complete Cherry Pick
- **Test Name**: `test_run_command_new_cherry_pick_calls_complete_cherry_pick`
- **Description**: When a commit is provided without `--continue` or `--abort` (a new cherry pick).
- **Expected Outcome**: `_complete_cherry_pick` is called.

#### 4. Continue Resumes And Calls Complete Cherry Pick
- **Test Name**: `test_run_command_continue_resumes_and_calls_complete_cherry_pick`
- **Description**: When `--continue` is set.
- **Expected Outcome**: `_resume_cherry_pick` is called and `_complete_cherry_pick` follows.

#### 5. Abort Returns Without Calling Complete Cherry Pick
- **Test Name**: `test_run_command_abort_returns_without_calling_complete_cherry_pick`
- **Description**: When `_resume_cherry_pick` raises `EdkrepoAbortCherryPickException`.
- **Expected Outcome**: `run_command` returns without calling `_complete_cherry_pick`.

### TestCherryPickOperationsToIncludeFolderList
Tests the module-level `cherry_pick_operations_to_include_folder_list` helper, which flattens the source folders of the cherry-pick operations.

#### 1. Cherry Pick Operations To Include Folder List Flattens Sources
- **Test Name**: `test_cherry_pick_operations_to_include_folder_list_flattens_sources`
- **Description**: When flattening the source folders across multiple cherry-pick operations.
- **Expected Outcome**: The `source` folder of every operation entry is returned in a single flat list.

### TestStripCommitMessage
Tests the module-level `strip_commit_message` helper, which removes Gerrit trailers and optionally appends the source SHA.

#### 1. Strip Commit Message Removes Gerrit Trailers And Converts Change Id
- **Test Name**: `test_strip_commit_message_removes_gerrit_trailers_and_converts_change_id`
- **Description**: When a commit message contains Gerrit trailers (`Original-chg-id`, `Change-Id`, `Reviewed-on`, `Tested-by`, `Reviewed-by`).
- **Expected Outcome**: The trailers are dropped and the `Change-Id` value is rewritten as `Original-chg-id`.

#### 2. Strip Commit Message Appends Source Sha When Requested
- **Test Name**: `test_strip_commit_message_appends_source_sha_when_requested`
- **Description**: When `append_sha` is set and a source commit is supplied.
- **Expected Outcome**: A `(cherry picked from commit <sha>)` line is appended to the message.

### TestInsideDirectory
Tests the module-level `inside_directory` helper, which reports whether a child path is nested within a parent path.

#### 1. Inside Directory (Child Inside Parent)
- **Test Name**: `test_inside_directory[child_inside_parent]`
- **Description**: When the child path is nested within the parent path.
- **Expected Outcome**: `inside_directory` returns `True`.

#### 2. Inside Directory (Sibling With Shared Prefix)
- **Test Name**: `test_inside_directory[sibling_with_shared_prefix]`
- **Description**: When the child path merely shares a name prefix with the parent path.
- **Expected Outcome**: `inside_directory` returns `False`.

#### 3. Inside Directory (Unrelated Paths)
- **Test Name**: `test_inside_directory[unrelated_paths]`
- **Description**: When the child path is unrelated to the parent path.
- **Expected Outcome**: `inside_directory` returns `False`.

### TestGetCommonFolderName
Tests the module-level `get_common_folder_name` helper, which returns the longest common substring of two folder names, honoring the ignored-folders configuration.

#### 1. Get Common Folder Name (Longest Common Substring)
- **Test Name**: `test_get_common_folder_name[longest_common_substring]`
- **Description**: When two folder names share a substring longer than three characters and no folders are ignored.
- **Expected Outcome**: The longest common substring is returned.

#### 2. Get Common Folder Name (Ignored Folder Removes Common Part)
- **Test Name**: `test_get_common_folder_name[ignored_folder_removes_common_part]`
- **Description**: When the only shared substring corresponds to an ignored folder.
- **Expected Outcome**: An empty string is returned.

#### 3. Get Common Folder Name (No Common Substring)
- **Test Name**: `test_get_common_folder_name[no_common_substring]`
- **Description**: When the two folder names have no common substring.
- **Expected Outcome**: An empty string is returned.


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
