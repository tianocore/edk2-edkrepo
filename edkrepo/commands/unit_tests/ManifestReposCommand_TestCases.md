# Test Cases for `manifest_repos_command` Module

## Test Structure

Both test classes (`TestListManifestRepos` and `TestListManifestReposJson`) use pytest parameterization to consolidate multiple test scenarios into single test methods. Each parameterized test executes multiple test cases with different inputs, making the tests more maintainable and reducing code duplication.

## Test Cases

### TestListManifestRepos
Tests the `_list_manifest_repos` method of the ManifestRepos class which displays manifest repository information in text format, with optional verbose output showing repository paths.

**Implementation**: Single parameterized test method (`test_list_manifest_repos`) with 6 test scenarios.

#### 1. Non-Verbose Output with CFG Repos Only
- **Test ID**: `non_verbose_cfg_only`
- **Description**: Display only global configuration repositories without verbose details.
- **Test Data**: `cfg_repos=['repo1', 'repo2']`, `user_cfg_repos=[]`, `verbose=False`
- **Verification**: 
  - Verifies `print_info_msg` is called with correct message format for each cfg repo
  - Verifies repository paths are NOT retrieved (performance optimization)
  - Verifies correct message strings from `humble.CFG_LIST_ENTRY` are used

#### 2. Non-Verbose Output with User CFG Repos Only
- **Test ID**: `non_verbose_user_cfg_only`
- **Description**: Display only user configuration repositories without verbose details.
- **Test Data**: `cfg_repos=[]`, `user_cfg_repos=['user_repo1', 'user_repo2']`, `verbose=False`
- **Verification**: 
  - Verifies `print_info_msg` is called with correct message format for each user cfg repo
  - Verifies repository paths are NOT retrieved
  - Verifies correct message strings from `humble.USER_CFG_LIST_ENTRY` are used

#### 3. Empty Repository Lists
- **Test ID**: `empty_lists`
- **Description**: Handle the case where no repositories are configured.
- **Test Data**: `cfg_repos=[]`, `user_cfg_repos=[]`, `verbose=False`
- **Verification**: 
  - Verifies no calls to `print_info_msg`
  - Verifies no calls to path retrieval functions

#### 4. Verbose Output with CFG Repos Only
- **Test ID**: `verbose_cfg_only`
- **Description**: Display global configuration repositories with verbose details showing paths.
- **Test Data**: `cfg_repos=['repo1', 'repo2']`, `user_cfg_repos=[]`, `verbose=True`
- **Verification**: 
  - Verifies repository paths are retrieved for each repo
  - Verifies normalized paths are displayed
  - Verifies correct verbose message strings from `humble.CFG_LIST_ENTRY_VERBOSE` are used

#### 5. Verbose Output with User CFG Repos Only
- **Test ID**: `verbose_user_cfg_only`
- **Description**: Display user configuration repositories with verbose details showing paths.
- **Test Data**: `cfg_repos=[]`, `user_cfg_repos=['user_repo1', 'user_repo2']`, `verbose=True`
- **Verification**: 
  - Verifies repository paths are retrieved for each repo
  - Verifies normalized paths are displayed
  - Verifies correct verbose message strings from `humble.USER_CFG_LIST_ENTRY_VERBOSE` are used

#### 6. Verbose Output with Both CFG and User CFG Repos
- **Test ID**: `verbose_both`
- **Description**: Display both global and user configuration repositories with verbose details.
- **Test Data**: `cfg_repos=['repo1', 'repo2']`, `user_cfg_repos=['user_repo1']`, `verbose=True`
- **Verification**: 
  - Verifies repository paths are retrieved for all repos
  - Verifies both cfg and user cfg repos are displayed with normalized paths
  - Verifies correct message formats for both cfg and user cfg repos


### TestListManifestReposJson
Tests the `_list_manifest_repos_json` method of the ManifestRepos class which generates JSON-formatted output of manifest repository information.

**Implementation**: Single parameterized test method (`test_list_manifest_repos_json`) with 4 test scenarios.

#### 1. JSON Output with CFG Repos Only
- **Test ID**: `cfg_only`
- **Description**: Generate JSON output containing only global configuration repositories.
- **Test Data**: `cfg_repos=['repo1', 'repo2']`, `user_cfg_repos=[]`
- **Verification**: 
  - Verifies exact JSON string output with `indent=2` formatting
  - Verifies `edkrepo_cfg.manifest_repositories` contains 2 entries with correct names and normalized paths
  - Verifies `edkrepo_user_cfg.manifest_repositories` is empty array
  - Verifies output is valid JSON and matches expected structure

#### 2. JSON Output with User CFG Repos Only
- **Test ID**: `user_cfg_only`
- **Description**: Generate JSON output containing only user configuration repositories.
- **Test Data**: `cfg_repos=[]`, `user_cfg_repos=['user_repo1', 'user_repo2']`
- **Verification**: 
  - Verifies exact JSON string output with `indent=2` formatting
  - Verifies `edkrepo_cfg.manifest_repositories` is empty array
  - Verifies `edkrepo_user_cfg.manifest_repositories` contains 2 entries with correct names and normalized paths
  - Verifies output is valid JSON and matches expected structure

#### 3. JSON Output with Both CFG and User CFG Repos
- **Test ID**: `both`
- **Description**: Generate JSON output containing both global and user configuration repositories.
- **Test Data**: `cfg_repos=['repo1', 'repo2']`, `user_cfg_repos=['user_repo1']`
- **Verification**: 
  - Verifies exact JSON string output with `indent=2` formatting
  - Verifies both repository arrays are populated with their respective repositories
  - Verifies all entries have correct names and normalized paths
  - Verifies output is valid JSON and matches expected structure

#### 4. JSON Output with Empty Repository Lists
- **Test ID**: `empty_lists`
- **Description**: Generate JSON output when no repositories are configured.
- **Test Data**: `cfg_repos=[]`, `user_cfg_repos=[]`
- **Verification**: 
  - Verifies exact JSON string output with `indent=2` formatting
  - Verifies both repository arrays are empty
  - Verifies JSON structure is maintained
  - Verifies output is valid JSON


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - `edkrepo_manifest_parser`
   - `colorama`
   - `GitPython`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run All Tests**:
   From the `edkrepo\commands\unit_tests\` directory, run:
   ```bash
   python3 -m pytest test_manifest_repos_command.py
   ```
   
   To run with verbose output:
   ```bash
   python3 -m pytest test_manifest_repos_command.py -v
   ```

3. **Run Specific Test Classes**:
   ```bash
   python3 -m pytest test_manifest_repos_command.py::TestListManifestRepos
   python3 -m pytest test_manifest_repos_command.py::TestListManifestReposJson
   ```

4. **Run Specific Parameterized Test Cases**:
   You can run individual parameterized scenarios using their test IDs:
   ```bash
   # Run only non-verbose cfg tests
   python3 -m pytest test_manifest_repos_command.py::TestListManifestRepos::test_list_manifest_repos[non_verbose_cfg_only]
   
   # Run only JSON output with both repos
   python3 -m pytest test_manifest_repos_command.py::TestListManifestReposJson::test_list_manifest_repos_json[both]
   ```

5. **Additional pytest Options**:
   - Show all test IDs: `pytest --collect-only test_manifest_repos_command.py`
   - Run tests matching a pattern: `pytest -k "verbose" test_manifest_repos_command.py`
   - See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for more options.

