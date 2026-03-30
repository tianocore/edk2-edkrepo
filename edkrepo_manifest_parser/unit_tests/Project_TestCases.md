# Test Cases for `_Project` Class

## Test Cases

### TestParseProjectRequiredAttribs
Tests `_parse_project_required_attribs` which extracts the required `name` and `xmlPath` attributes from a `<Project>` XML element, raising `KeyError` if either is missing.

#### 1. Returns Name and XmlPath When Both Present
- **Description**: When `name` and `xmlPath` are both present in the element's attributes.
- **Expected Outcome**: Returns a tuple `(name, xmlPath)` with the correct values and no exception is raised.

#### 2. Raises KeyError When Name Is Missing
- **Description**: When the `name` attribute is absent from the element.
- **Expected Outcome**: Raises `KeyError` containing the required-attribute error message.

#### 3. Raises KeyError When XmlPath Is Missing
- **Description**: When the `xmlPath` attribute is absent from the element.
- **Expected Outcome**: Raises `KeyError` containing the required-attribute error message.

### TestProjectInit
Tests `_Project.__init__` which parses required (`name`, `xmlPath`) and optional (`archived`) attributes from a `<Project>` XML element.

#### 1. Sets Name and XmlPath from Required Attributes
- **Description**: When all required attributes are present in the element.
- **Expected Outcome**: `self.name` and `self.xmlPath` are set to the values from the element's attributes.

#### 2. Sets Archived to True When Flag Is Lowercase True
- **Description**: When the `archived` attribute is set to the string `'true'`.
- **Expected Outcome**: `self.archived` is `True`.

#### 3. Sets Archived to False When Flag Is Lowercase False
- **Description**: When the `archived` attribute is set to the string `'false'`.
- **Expected Outcome**: `self.archived` is `False`.

#### 4. Defaults Archived to False When Attribute Is Missing
- **Description**: When the `archived` attribute is absent from the element.
- **Expected Outcome**: `self.archived` defaults to `False`.

#### 5. Sets Archived to True When Flag Is Uppercase (Case Insensitive)
- **Description**: When the `archived` attribute is set to `'TRUE'` (uppercase).
- **Expected Outcome**: `self.archived` is `True`, confirming case-insensitive comparison.


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
