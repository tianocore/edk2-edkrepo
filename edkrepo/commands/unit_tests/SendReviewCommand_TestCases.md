# Test Cases for `send_review_command` Module

## Test Cases

### TestGetActivePrsOnBranch
Tests the `__get_active_prs_on_branch` method to ensure it raises `EdkrepoGithubApiFailException` instead of crashing when encountering bad API data. This allows the caller to catch the exception and use local branch-name inference as a fallback.

#### 1. Empty Array Response
- **Description**: When the GitHub API returns an empty array.
- **Expected Outcome**: The method raises `EdkrepoGithubApiFailException` with a descriptive message.

#### 2. Missing Fields in Response
- **Description**: When the GitHub API returns PR data but is missing required fields (e.g., `html_url`).
- **Expected Outcome**: The method catches the KeyError and raises `EdkrepoGithubApiFailException`.

#### 3. Malformed JSON Response
- **Description**: When the GitHub API returns invalid JSON that cannot be parsed.
- **Expected Outcome**: The method catches the JSONDecodeError and raises `EdkrepoGithubApiFailException`.

#### 4. Error Dict Response
- **Description**: When the GitHub API returns an error object (dict with `message` key) instead of an array.
- **Expected Outcome**: The method detects the error format and raises `EdkrepoGithubApiFailException`.

#### 5. Non-List Response
- **Description**: When the GitHub API returns a non-list type such as a string.
- **Expected Outcome**: The method validates the type and raises `EdkrepoGithubApiFailException`.

### TestBranchNameInference
Tests the branch name inference fallback logic added to `__send_github_pr_branch_mode` method. When `__get_active_prs_on_branch` raises an exception, the caller uses local branch name starting with 'pull_request' to determine whether to update an existing PR or create a new one.

#### 1. API Success Triggers Update Flow
- **Description**: When the GitHub API returns valid PR data (dict of PR number to URL).
- **Expected Outcome**: The method uses the update flow without branch inference. `__create_pr_branch` is not called.

#### 2. Pull Request Branch Name Triggers Update When API Raises Exception
- **Description**: When the GitHub API raises `EdkrepoGithubApiFailException` and the local branch name starts with 'pull_request'.
- **Expected Outcome**: The method catches the exception, infers this is an existing PR branch, and uses the update flow. `__create_pr_branch` is not called.

#### 3. Non-Pull Request Branch Name Triggers Create When API Raises Exception
- **Description**: When the GitHub API raises `EdkrepoGithubApiFailException` and the local branch name does not start with 'pull_request'.
- **Expected Outcome**: The method catches the exception, infers this is a new feature branch, and uses the create flow. `__create_pr_branch` is called once.

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