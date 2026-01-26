# Test Cases for `config_factory` Module

## Test Cases

### TestGetCheckedOutPinFile
Loads a pin file and returns the ManifestXml object with commit SHAs.

#### 1. From Manifest Repo Pin Folder
- **Description**: When a pin file exists in the manifest repository's pin folder.
- **Expected Outcome**: The function returns the pin file from the manifest repo pin folder.

#### 2. From Workspace Root
- **Description**: When a pin file does not exist in the manifest repo but exists in the workspace root.
- **Expected Outcome**: The function returns the pin file from the workspace root.

#### 3. Pin File Not Found
- **Description**: When the pin file does not exist in either location.
- **Expected Outcome**: The function raises an `EdkrepoPinFileNotFoundException`.

#### 4. No Pin Path in Config
- **Description**: When the pin_path is not configured in the manifest's general_config.
- **Expected Outcome**: The function loads the pin file from the workspace root.

#### 5. Prefers Manifest Repo Over Workspace
- **Description**: When a pin file exists in both locations.
- **Expected Outcome**: The function returns the pin file from the manifest repo pin folder.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - `edkrepo_manifest_parser`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo\config\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
