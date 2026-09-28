# Test Cases for `ListReposCommand` Class

## Test Cases

### TestRunCommand
Tests `ListReposCommand.run_command`, which validates the requested format, refreshes the manifest repos, and lists the available repositories.

#### 1. Run Command Raises For Invalid Format Type
- **Test Name**: `test_run_command_raises_for_invalid_format_type`
- **Description**: When an unrecognised format type is passed.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 2. Run Command Pulls All Manifest Repos
- **Test Name**: `test_run_command_pulls_all_manifest_repos`
- **Description**: When `run_command` executes.
- **Expected Outcome**: `pull_all_manifest_repos` is called to refresh all configured manifest repos.

#### 3. Run Command Calls Generate Repo Names
- **Test Name**: `test_run_command_calls_generate_repo_names`
- **Description**: When `run_command` finishes processing the manifest repos.
- **Expected Outcome**: `generate_repo_names` is called.

#### 4. Run Command Raises When Requested Repos Not In Manifest
- **Test Name**: `test_run_command_raises_when_requested_repos_not_in_manifest`
- **Description**: When `--repos` lists names absent from the manifest.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

### TestCollectManifestsFromRepo
Tests `ListReposCommand._collect_manifests_from_repo`, which gathers manifests and repo URLs from a manifest repository.

#### 1. Collect Manifests From Repo Populates Found Manifests
- **Test Name**: `test_collect_manifests_from_repo_populates_found_manifests`
- **Description**: When `_collect_manifests_from_repo` processes a project.
- **Expected Outcome**: An entry keyed by `repo:project` is added to `found_manifests`.

#### 2. Collect Manifests From Repo Collects Repo Urls
- **Test Name**: `test_collect_manifests_from_repo_collects_repo_urls`
- **Description**: When `_collect_manifests_from_repo` processes repo sources.
- **Expected Outcome**: The normalized repo URL is added to `repo_urls`.

### TestGenerateRepoNames
Tests `ListReposCommand.generate_repo_names`, which builds the ordered mapping of repo display names.

#### 1. Generate Repo Names Orders Edk2 And Intel Prefixes First
- **Test Name**: `test_generate_repo_names_orders_edk2_and_intel_prefixes_first`
- **Description**: When `generate_repo_names` builds names for repos whose names begin with `edk2` and `intel`.
- **Expected Outcome**: Names are sorted alphabetically, then `edk2`* and `intel`* names are moved to the front of the ordered mapping.

### TestGetRepoUrl
Tests `ListReposCommand.get_repo_url`, which normalizes a repo URL by stripping the trailing `.git` suffix.

#### 1. Get Repo Url Strips Dot Git Suffix (Lowercase Git)
- **Test Name**: `test_get_repo_url_strips_dot_git_suffix[lowercase_git]`
- **Description**: When `get_repo_url` is given a URL ending in a lowercase `.git` suffix.
- **Expected Outcome**: The trailing `.git` suffix is stripped.

#### 2. Get Repo Url Strips Dot Git Suffix (Uppercase Git)
- **Test Name**: `test_get_repo_url_strips_dot_git_suffix[uppercase_git]`
- **Description**: When `get_repo_url` is given a URL ending in an uppercase `.GIT` suffix.
- **Expected Outcome**: The trailing suffix is stripped case-insensitively.

#### 3. Get Repo Url Strips Dot Git Suffix (No Suffix)
- **Test Name**: `test_get_repo_url_strips_dot_git_suffix[no_suffix]`
- **Description**: When `get_repo_url` is given a URL with no `.git` suffix.
- **Expected Outcome**: The URL is returned unchanged.


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
