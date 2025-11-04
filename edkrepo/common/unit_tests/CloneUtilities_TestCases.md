# Test Cases for `clone_utilities` Module

## Test Cases

### TestGenerateCloneOrder
Tests the `generate_clone_order` method which ensures that nested repositories are only cloned after their parent repository exists in the workspace.

#### 1. No Nested Repositories
- **Description**: With repositories that are not nested.
- **Expected Outcome**: The clone order matches the input repository sources.

#### 2. With Nested Repositories
- **Description**: With repositories that include nested repositories.
- **Expected Outcome**: The clone order respects the nesting hierarchy, ensuring parent repositories are cloned before their nested repositories.

### TestCalculateSourceManifestRepoDirectory
Determines the source manifest repository's directory.

#### 3. Source Manifest Repo Found in Config (No Flag)
- **Description**: When the source manifest repository is found in the configuration file and no flag is provided.
- **Expected Outcome**: The function returns the path to the manifest repository from the configuration file.

#### 4. Source Manifest Repo Found in Config (With Flag)
- **Description**: When the source manifest repository is found in the configuration file and the source manifest repo flag is provided.
- **Expected Outcome**: The function returns the path to the manifest repository from the configuration file.

#### 5. Source Manifest Repo Found in User Config (No Flag)
- **Description**: When the source manifest repository is found in the user configuration file and no flag is provided.
- **Expected Outcome**: The function returns the path to the manifest repository from the user configuration file.

#### 6. Source Manifest Repo Found in User Config (With Flag)
- **Description**: When the source manifest repository is found in the user configuration file and the source manifest repo flag is provided.
- **Expected Outcome**: The function returns the path to the manifest repository from the user configuration file.

#### 7. Found Manifest Repo Not in Config
- **Description**: When the found manifest repository is not present in the configuration file.
- **Expected Outcome**: The function returns `None`.

#### 8. Source Manifest Repo Not Found (With Flag)
- **Description**: When the source manifest repository is not found and the source manifest repo flag is provided.
- **Expected Outcome**: The function returns `None`.

#### 9. Source Manifest Repo Not Found
- **Description**: When the source manifest repository is not found and no flag is provided.
- **Expected Outcome**: The function returns `None`.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo\common\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.