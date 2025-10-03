# Test Cases for `ManifestXml` Class

## TestGetParentOfNestedRepo
Tests the `get_parent_of_nested_repo` method which determines the parent repository of a nested repository.

### 1. Not Nested Repository
- **Description**: When the provided repository path is not nested.
- **Expected Outcome**: A `ValueError` is raised with the message `INVALID_REPO_PATH_ERROR`.

### 2. One-Level Nested Repository
- **Description**: For a repository that is nested one level deep.
- **Expected Outcome**: The method returns the parent repository's `RepoSource` object.

### 3. Multiple-Level Nested Repository
- **Description**: For a repository that is nested multiple levels deep.
- **Expected Outcome**: The method returns the immediate parent repository's `RepoSource` object.

### 4. Invalid Repository Path
- **Description**: With an invalid repository path.
- **Expected Outcome**: A `ValueError` is raised with the message `INVALID_REPO_PATH_ERROR`.

### 5. No Parent Repository Found
- **Description**: When no parent repository is found for the given path.
- **Expected Outcome**: A `ValueError` is raised with the message `NO_PARENT_REPO_ERROR`.

### Notes
- The `INVALID_REPO_PATH_ERROR` and `NO_PARENT_REPO_ERROR` strings are defined in the `edk_manifest.py` file and are used to validate the input path and parent repository existence, respectively.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
