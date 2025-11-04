# Test Cases for `git_exclude_maintenance` Module

## Test Cases

### TestWriteGitExclude

#### 1. Open Called with Correct Arguments
- **Description**: Verifies that the `.git/info/exclude` file is opened in append mode.
- **Expected Outcome**: The file is opened with the correct path and mode (`"a"`).

#### 2. Write Called with Correct Pattern
- **Description**: Verifies that the correct exclude pattern is written to the file.
- **Expected Outcome**: The exclude pattern is written to the file, followed by a newline.

### TestGenerateExcludePattern

#### 3. Generate Exclude Pattern (Valid Case)
- **Description**: Verifies that the correct relative path is generated for a nested repository.
- **Expected Outcome**: The function returns the relative path from the parent repository to the nested repository, with a trailing slash.

#### 4. Different Drives (Windows)
- **Description**: Verifies that a `ValueError` is raised when the parent and nested repository paths are on different drives (Windows-specific).
- **Expected Outcome**: A `ValueError` is raised.

#### 5. No Common Prefix
- **Description**: Verifies that a `ValueError` is raised when the parent and nested repository paths do not share a common prefix.
- **Expected Outcome**: A `ValueError` is raised.

## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo\common\workspace_maintenance\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.