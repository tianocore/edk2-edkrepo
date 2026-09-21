# Test Cases for `CreatePinCommand` Class

## Test Cases

### TestRunCommand
Tests `CreatePinCommand.run_command`, which validates the pin file target, prepares its directory, and generates the pin XML.

#### 1. Raises When Pin File Exists
- **Test Name**: `test_run_command_raises_when_pin_file_exists`
- **Description**: When the pin file already exists.
- **Expected Outcome**: `EdkrepoInvalidParametersException` is raised.

#### 2. Creates Directory When Parent Missing
- **Test Name**: `test_run_command_creates_directory_when_parent_missing`
- **Description**: When the pin file's parent directory does not exist.
- **Expected Outcome**: `os.mkdir` is called.

#### 3. Calls Generate Pin Xml
- **Test Name**: `test_run_command_calls_generate_pin_xml`
- **Description**: When `run_command` generates the pin.
- **Expected Outcome**: `generate_pin_xml` is called with the description, current combo, and resolved pin file path.

#### 4. Skips Mkdir When Parent Directory Exists
- **Test Name**: `test_run_command_skips_mkdir_when_parent_directory_exists`
- **Description**: When the pin file's parent directory already exists.
- **Expected Outcome**: `os.mkdir` is not called.

#### 5. Resolves Relative Pin Path To Absolute
- **Test Name**: `test_run_command_resolves_relative_pin_path_to_absolute`
- **Description**: When a relative `PinFileName` is provided.
- **Expected Outcome**: The path is resolved to an absolute path before the pin is written.

### TestGeneratePinData
Tests `CreatePinCommand._generate_pin_data`, which resolves the commit SHA of each repo source when building pin data.

#### 1. Generate Pin Data With Patchset
- **Test Name**: `test_generate_pin_data_with_patchset`
- **Description**: When sources have a patchset.
- **Expected Outcome**: The sources are returned as-is without querying the repository HEAD.

#### 2. Generate Pin Data Missing Repo Raises Workspace Corrupt
- **Test Name**: `test_generate_pin_data_missing_repo_raises_workspace_corrupt`
- **Description**: When a repo source directory is absent from the workspace.
- **Expected Outcome**: `EdkrepoWorkspaceCorruptException` is raised.

#### 3. Generate Pin Data Resolves Commit For Non Patchset Sources (No Patchset)
- **Test Name**: `test_generate_pin_data_resolves_commit_for_non_patchset_sources[no_patchset]`
- **Description**: When none of the sources have a patchset.
- **Expected Outcome**: Each source's commit SHA is resolved from its repository's HEAD.

#### 4. Generate Pin Data Resolves Commit For Non Patchset Sources (Mixed Patchset)
- **Test Name**: `test_generate_pin_data_resolves_commit_for_non_patchset_sources[mixed_patchset]`
- **Description**: When some sources have a patchset and others do not.
- **Expected Outcome**: Sources with a patchset are left untouched; sources without one have their commit SHA resolved from HEAD.

#### 5. Generate Pin Data Verbose Mode Prints Info Msg (No Patchset)
- **Test Name**: `test_generate_pin_data_verbose_mode_prints_info_msg[no_patchset]`
- **Description**: When `verbose` is `True` and the sources have no patchset.
- **Expected Outcome**: `print_info_msg` is called at least once.

#### 6. Generate Pin Data Verbose Mode Prints Info Msg (With Patchset)
- **Test Name**: `test_generate_pin_data_verbose_mode_prints_info_msg[with_patchset]`
- **Description**: When `verbose` is `True` and the sources have a patchset.
- **Expected Outcome**: `print_info_msg` is called at least once.


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
