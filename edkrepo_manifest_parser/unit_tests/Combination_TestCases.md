# Test Cases for `_Combination` Class

## Test Cases

### TestParseCombinationRequiredAttribs
Tests `_parse_combination_required_attribs(element)` which validates that the required `name` attribute is present and returns it.

#### 1. Returns name When name Attribute Present
- **Description**: When the element has a `name` attribute.
- **Expected Outcome**: Returns the `name` attribute value as a string.

#### 2. Raises KeyError When name Attribute Absent
- **Description**: When the element has no `name` attribute.
- **Expected Outcome**: Raises `KeyError` whose string representation contains the expected `REQUIRED_ATTRIB_ERROR_MSG` prefix.

### TestCombinationInit
Tests `_Combination.__init__` which parses a `<Combination>` XML element for the required `name` and several optional attributes including boolean flags.

#### 1. Sets name From Required Attribute
- **Description**: When the element has a valid `name` attribute.
- **Expected Outcome**: `self.name` equals the `name` attribute value.

#### 2. Sets description When description Attribute Present
- **Description**: When the element has a `description` attribute.
- **Expected Outcome**: `self.description` is set to the `description` attribute value.

#### 3. Sets description to None When description Attribute Absent
- **Description**: When the element has no `description` attribute.
- **Expected Outcome**: `self.description` is `None`.

#### 4. Sets archived to True When archived Attribute is "true" (lowercase)
- **Description**: When the element has an `archived` attribute with value `"true"`.
- **Expected Outcome**: `self.archived` is `True`.

#### 5. Sets archived to False When archived Attribute is "false" (lowercase)
- **Description**: When the element has an `archived` attribute with value `"false"`.
- **Expected Outcome**: `self.archived` is `False`.

#### 6. Sets archived to False When archived Attribute is Absent
- **Description**: When the element has no `archived` attribute.
- **Expected Outcome**: `self.archived` is `False`.

#### 7. Sets archived to True When archived Attribute is "TRUE" (uppercase)
- **Description**: When the element has an `archived` attribute with value `"TRUE"` (testing case-sensitivity or lack thereof).
- **Expected Outcome**: `self.archived` reflects the truthiness check against the `"true"` literal.

#### 8. Sets venv_enable to True When venv_enable Attribute is "true"
- **Description**: When the element has a `venv_enable` attribute with value `"true"`.
- **Expected Outcome**: `self.venv_enable` is `True`.

#### 9. Sets venv_enable to False When venv_enable Attribute is "false"
- **Description**: When the element has a `venv_enable` attribute with value `"false"`.
- **Expected Outcome**: `self.venv_enable` is `False`.

#### 10. Sets venv_enable to False When venv_enable Attribute is Absent
- **Description**: When the element has no `venv_enable` attribute.
- **Expected Outcome**: `self.venv_enable` is `False`.

### TestCombinationTuple
Tests `_Combination.tuple` which returns a `Combination` namedtuple.

#### 1. Returns Correct Combination Namedtuple
- **Description**: When all attributes are present.
- **Expected Outcome**: `tuple` returns a `Combination` namedtuple with all fields correctly populated.


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
