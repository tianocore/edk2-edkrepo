# Test Cases for `SendReviewCommand` Class

## Test Cases

### TestInit
Tests `SendReviewCommand.__init__`, which is inherited unchanged from the open-source module and constructs the command instance.

#### 1. Init Creates Instance Without Error
- **Test Name**: `test_init_creates_instance_without_error`
- **Description**: When constructing `SendReviewCommand` with no arguments.
- **Expected Outcome**: The instance is created successfully.

### TestCreatePrBranch
Tests `SendReviewCommand._create_pr_branch`, which creates a PR branch whose name embeds the git username and normalized title.

#### 1. Create Pr Branch Raises When Git Email Not Found
- **Test Name**: `test_create_pr_branch_raises_when_git_email_not_found`
- **Description**: When no git email is configured.
- **Expected Outcome**: `_create_pr_branch` raises `EdkRepoGitEmailNotFoundException`.

#### 2. Create Pr Branch Creates Branch With Normalized Name And Returns Its Name
- **Test Name**: `test_create_pr_branch_creates_branch_with_normalized_name_and_returns_its_name`
- **Description**: When creating a PR branch from a title containing special characters.
- **Expected Outcome**: A head branch embedding the git username and normalized title is created and its name is returned.

#### 3. Create Pr Branch Prints Info Message When Title Characters Are Stripped
- **Test Name**: `test_create_pr_branch_prints_info_message_when_title_characters_are_stripped`
- **Description**: When non-alphanumeric characters are stripped from the title.
- **Expected Outcome**: An info message is printed once.

### TestGetChangedFileList
Tests the module-level `get_changed_file_list` helper, which collects the `a_path` and `b_path` of every diff entry.

#### 1. Get Changed File List Returns A Path And B Path From Each Diff Entry
- **Test Name**: `test_get_changed_file_list_returns_a_path_and_b_path_from_each_diff_entry`
- **Description**: When the diff contains entries with distinct and identical `a_path`/`b_path` values.
- **Expected Outcome**: A set containing every `a_path` and `b_path` in the diff is returned.

#### 2. Get Changed File List Returns Empty Set For Empty Diff
- **Test Name**: `test_get_changed_file_list_returns_empty_set_for_empty_diff`
- **Description**: When the diff contains no entries.
- **Expected Outcome**: An empty set is returned.

### TestModifiedRepo
Tests the `ModifiedRepo` helper class, which resolves the manifest and git repository to submit for review from either an explicit repo reference or the single repo with local commits.

#### 1. With Repo Reference And Detached Head Raises Exception
- **Test Name**: `test_with_repo_reference_and_detached_head_raises_exception`
- **Description**: When the matched repo has a detached HEAD.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 2. With Repo Reference Not Found Raises Exception
- **Test Name**: `test_with_repo_reference_not_found_raises_exception`
- **Description**: When no manifest repo matches the repo reference.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 3. Without Repo Reference And Patch Set Raises Exception
- **Test Name**: `test_without_repo_reference_and_patch_set_raises_exception`
- **Description**: When a repo source has a patch_set configured and no repo reference is given.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 4. Without Repo Reference And No Commits Ahead Raises No Local Branches Exception
- **Test Name**: `test_without_repo_reference_and_no_commits_ahead_raises_no_local_branches_exception`
- **Description**: When no repo has commits ahead of its target branch.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 5. Without Repo Reference And Multiple Modified Repos Raises Exception
- **Test Name**: `test_without_repo_reference_and_multiple_modified_repos_raises_exception`
- **Description**: When more than one repo has commits ahead.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 6. Without Repo Reference And Single Modified Repo Sets Manifest And Git
- **Test Name**: `test_without_repo_reference_and_single_modified_repo_sets_manifest_and_git`
- **Description**: When exactly one repo source has commits ahead.
- **Expected Outcome**: `ModifiedRepo` sets `manifest` and `git` from that repo source.

#### 7. With Repo Reference Matching Repo Sets Manifest And Git (Matches By Root)
- **Test Name**: `test_with_repo_reference_matching_repo_sets_manifest_and_git[matches_by_root]`
- **Description**: When the repo reference matches a manifest repo by root.
- **Expected Outcome**: `ModifiedRepo` sets `manifest` and `git` from the matching repo.

#### 8. With Repo Reference Matching Repo Sets Manifest And Git (Matches By Remote Name)
- **Test Name**: `test_with_repo_reference_matching_repo_sets_manifest_and_git[matches_by_remote_name]`
- **Description**: When the repo reference matches a manifest repo by remote name.
- **Expected Outcome**: `ModifiedRepo` sets `manifest` and `git` from the matching repo.

### TestRunCommand
Tests `SendReviewCommand.run_command`, which resolves the workspace, builds a `ModifiedRepo`, and dispatches based on the resolved review type.

#### 1. Creates Modified Repo With Workspace And Manifest
- **Test Name**: `test_run_command_creates_modified_repo_with_workspace_and_manifest`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `ModifiedRepo` is instantiated with the workspace manifest, workspace path, and repository arg.

#### 2. Calls Get Review Type With Manifest And Repo
- **Test Name**: `test_run_command_calls_get_review_type_with_manifest_and_repo`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `__get_review_type` is called with the workspace manifest and the `ModifiedRepo` instance.


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
