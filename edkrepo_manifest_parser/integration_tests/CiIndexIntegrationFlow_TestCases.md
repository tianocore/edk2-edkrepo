# Test Cases for `CiIndexIntegrationFlow` Integration Tests

## Test Cases

### TestCiIndexIntegrationFlow
Integration tests for CI index and manifest integration.

#### 1. All Projects Indexed By Name
- **Test Name**: `test_load_ci_index_with_multiple_projects`
- **Description**: When loading a CI index XML containing multiple active and archived project entries.
- **Expected Outcome**: All active projects are indexed by name in the project list; archived projects appear in the archived project list.

#### 2. Returns Correct Manifest Path For Project
- **Test Name**: `test_resolve_project_manifest_from_ci_index[Project1]`
- **Description**: When resolving manifest path for Project1 from the CI index (parametrized case).
- **Expected Outcome**: Returns the correct manifest path for Project1.

#### 3. Returns Correct Manifest Path For Project
- **Test Name**: `test_resolve_project_manifest_from_ci_index[Project2]`
- **Description**: When resolving manifest path for Project2 from the CI index (parametrized case).
- **Expected Outcome**: Returns the correct manifest path for Project2.

#### 4. Returns Correct Manifest Path For Project
- **Test Name**: `test_resolve_project_manifest_from_ci_index[Project3]`
- **Description**: When resolving manifest path for Project3 (archived) from the CI index (parametrized case).
- **Expected Outcome**: Returns the correct manifest path for Project3.

#### 5. Archived Project Not In Active List
- **Test Name**: `test_ci_index_project_with_archived_manifest`
- **Description**: When querying the CI index for a project marked as archived.
- **Expected Outcome**: Project name appears in archived list but not in active list; manifest path is still retrievable.

#### 6. Empty Index Contains No Projects
- **Test Name**: `test_ci_index_empty`
- **Description**: When loading a CI index XML with no project entries.
- **Expected Outcome**: Both project list and archived project list are empty.

#### 7. Raises ValueError When Project Not Found
- **Test Name**: `test_ci_index_project_not_found`
- **Description**: When querying the CI index for a project name that does not exist.
- **Expected Outcome**: Raises ValueError containing the nonexistent project name.

#### 8. Multiple Indexes Merge Correctly
- **Test Name**: `test_multiple_ci_indexes_merge`
- **Description**: When loading and merging multiple CI index files with different project sets.
- **Expected Outcome**: Combined project lists contain all projects from both indexes; active and archived counts are correct.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\integration_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
