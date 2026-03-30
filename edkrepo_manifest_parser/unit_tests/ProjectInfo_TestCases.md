# Test Cases for `_ProjectInfo` Class

## Test Cases

### TestParseProjectInfoRequiredFields
Tests `_parse_project_info_required_fields` which reads the `CodeName` and `Description` child elements from a `<ProjectInfo>` XML element.

#### 1. Returns Codename and Descript When Both Present
- **Description**: When `CodeName` and `Description` child elements are present with text content.
- **Expected Outcome**: Returns the tuple `(codename, descript)` with the correct text values.

### TestProjectInfoInit
Tests `_ProjectInfo.__init__` which delegates required-field parsing to `_parse_project_info_required_fields` and treats all other child elements as optional, defaulting to `None` or an empty list when absent.

#### 1. Sets Codename and Descript
- **Description**: When `CodeName` and `Description` children are present.
- **Expected Outcome**: `self.codename` and `self.descript` are set to their respective text values.

#### 2. Builds Lead List From DevLead Children
- **Description**: When one or more `DevLead` children are present.
- **Expected Outcome**: `self.lead_list` contains the text value of each `DevLead` element.

#### 3. Sets Lead List to Empty When No DevLead Children
- **Description**: When `findall('DevLead')` returns an empty list.
- **Expected Outcome**: `self.lead_list` is an empty list `[]`.

#### 4. Sets `org` When Present
- **Description**: When the `Org` child element is present with text content.
- **Expected Outcome**: `self.org` is set to the element's text value.

#### 5. Sets `org` to None When Absent
- **Description**: When the `Org` child element is absent (i.e., `find('Org')` returns `None`).
- **Expected Outcome**: `self.org` is `None`.

#### 6. Sets `short_name` When Present
- **Description**: When the `ShortName` child element is present with text content.
- **Expected Outcome**: `self.short_name` is set to the element's text value.

#### 7. Sets `short_name` to None When Absent
- **Description**: When the `ShortName` child element is absent.
- **Expected Outcome**: `self.short_name` is `None`.

#### 8. Sets Reviewer List From LeadReviewers Children
- **Description**: When the `LeadReviewers` child element is present and contains `Reviewer` sub-elements.
- **Expected Outcome**: `self.reviewer_list` contains the text value of each `Reviewer` element.

#### 9. Sets Reviewer List to None When LeadReviewers Absent
- **Description**: When `find('LeadReviewers')` returns `None`.
- **Expected Outcome**: `self.reviewer_list` is `None`.

### TestProjectInfoTuple
Tests `_ProjectInfo.tuple` which returns a `ProjectInfo` namedtuple with all six field values.

#### 1. Returns Correct ProjectInfo Namedtuple
- **Description**: When all child elements are present.
- **Expected Outcome**: `tuple` returns a `ProjectInfo(codename, description, dev_leads, reviewers, org, short_name)` with the correct values.


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
