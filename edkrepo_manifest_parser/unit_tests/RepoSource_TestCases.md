# Test Cases for `RepoSource` Class

## Test Cases

### 1. Valid Data with Branch, Commit, and Tag
- **Description**: Tests the initialization of a `RepoSource` object with valid data containing `branch`, `commit`, and `tag` attributes.
- **Expected Outcome**: The object is initialized successfully, and all attributes are set correctly.

### 2. Valid Data with Only Branch
- **Description**: Tests the initialization of a `RepoSource` object with only the `branch` attribute provided.
- **Expected Outcome**: The object is initialized successfully, and `branch` is set while `commit` and `tag` are `None`.

### 3. Valid Data with Only Commit
- **Description**: Tests the initialization of a `RepoSource` object with only the `commit` attribute provided.
- **Expected Outcome**: The object is initialized successfully, and `commit` is set while `branch` and `tag` are `None`.

### 4. Valid Data with Only Tag
- **Description**: Tests the initialization of a `RepoSource` object with only the `tag` attribute provided.
- **Expected Outcome**: The object is initialized successfully, and `tag` is set while `branch` and `commit` are `None`.

### 5. Invalid Data with None of Branch, Commit, or Tag
- **Description**: Tests the initialization of a `RepoSource` object with none of `branch`, `commit`, or `tag` provided.
- **Expected Outcome**: A `KeyError` is raised with the message `ATTRIBUTE_MISSING_ERROR`.

### 6. Nested Repository (nested_repo = True)
- **Description**: Tests the initialization of a `RepoSource` object with a `localRoot` path indicating a nested repository.
- **Expected Outcome**: The `nested_repo` attribute is set to `True`.

### 7. Non-Nested Repository (nested_repo = False)
- **Description**: Tests the initialization of a `RepoSource` object with a `localRoot` path indicating a non-nested repository.
- **Expected Outcome**: The `nested_repo` attribute is set to `False`.

### 8. Mutual Exclusivity of PatchSet and Branch/Commit/Tag
- **Description**: Tests the initialization of a `RepoSource` object to ensure that `patchSet` is mutually exclusive with `branch`, `commit`, and `tag`.
- **Expected Outcome**: If `patchSet` is provided, `branch`, `commit`, and `tag` must be `None`. If not, an exception is raised.

## Notes
- The `ATTRIBUTE_MISSING_ERROR` string is defined in the `edk_manifest.py` file and is used to validate the presence of at least one of `branch`, `commit`, or `tag`.

## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\unit_tests\` directory run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options