# Test Cases for `CiIndexXml` Class

## Test Cases

### TestCiIndexXmlInit
Tests `CiIndexXml.__init__` which parses a CiIndex XML file and builds the internal `_projects` map from all `<Project>` elements in the tree.

#### 1. Empty Tree Results in Empty Project Map
- **Description**: When the XML tree contains no `<Project>` elements.
- **Expected Outcome**: `self._projects` is an empty dictionary and `_Project` is never constructed.

#### 2. Single Project Populates Map with Correct Key
- **Description**: When the tree contains exactly one `<Project>` element.
- **Expected Outcome**: `_projects` contains one entry whose key is the project name and value is the corresponding `_Project` instance.

#### 3. Multiple Projects All Keyed by Name
- **Description**: When the tree contains multiple `<Project>` elements.
- **Expected Outcome**: `_projects` contains one entry per project, each keyed by its name.

### TestProjectList
Tests the `project_list` property which returns the names of all non-archived projects.

#### 1. Returns Only Active Project Names
- **Description**: When the projects map contains a mix of active and archived projects.
- **Expected Outcome**: Only the names of non-archived projects are returned.

#### 2. Returns Empty List When All Projects Are Archived
- **Description**: When every project in the map has `archived` set to `True`.
- **Expected Outcome**: Returns an empty list.

#### 3. Returns All Names When No Projects Are Archived
- **Description**: When every project in the map has `archived` set to `False`.
- **Expected Outcome**: All project names are returned.

### TestArchivedProjectList
Tests the `archived_project_list` property which returns the names of all archived projects.

#### 1. Returns Only Archived Project Names
- **Description**: When the projects map contains a mix of active and archived projects.
- **Expected Outcome**: Only the names of archived projects are returned.

#### 2. Returns Empty List When No Projects Are Archived
- **Description**: When every project in the map has `archived` set to `False`.
- **Expected Outcome**: Returns an empty list.

#### 3. Returns All Names When All Projects Are Archived
- **Description**: When every project in the map has `archived` set to `True`.
- **Expected Outcome**: All project names are returned.

### TestGetProjectXml
Tests `get_project_xml` which returns the XML path for a project or raises `ValueError` if the project is not found.

#### 1. Returns XmlPath When Project Found
- **Description**: When the requested project name exists in the internal projects map.
- **Expected Outcome**: Returns the `xmlPath` attribute of the corresponding `_Project`.

#### 2. Raises ValueError When Project Not Found
- **Description**: When the requested project name does not exist in the internal projects map.
- **Expected Outcome**: Raises `ValueError` containing the project name.


## Running the Tests

1. **Required Dependencies**:
   Ensure that the following third-party Python libraries are installed:
   - `pytest`
   - To generate HTML report output, `pytest-html` must be installed.

2. **Run the Tests**:
   From the `edkrepo_manifest_parser\unit_tests\` directory, run:
   ```bash
   python3 -m pytest
   ```
   See the official `pytest` documentation at: https://docs.pytest.org/en/latest/how-to/usage.html for additional command line options.
