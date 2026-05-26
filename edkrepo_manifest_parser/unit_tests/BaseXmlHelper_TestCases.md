# Test Cases for `BaseXmlHelper` Class

## Test Cases

### TestInit
Tests `BaseXmlHelper.__init__` which loads and validates the file (XML or JSON), raising `TypeError` if the file is invalid or its root tag is not in `xml_types`.

#### 1. Valid File — Root Tag in xml_types (Manifest)
- **Test Name**: `test_init_valid_root_tag_sets_attributes[manifest_type]`
- **Description**: `_load_tree` returns a tree whose root tag (`Manifest`) is a member of the provided `xml_types` list.
- **Expected Outcome**: Instance is created successfully; `_fileref`, `_tree`, and `_xml_type` are set correctly.

#### 2. Root Tag Not in xml_types Raises TypeError
- **Test Name**: `test_root_tag_not_in_xml_types_raises_typeerror`
- **Description**: `_load_tree` returns a tree whose root tag is not in the provided `xml_types` list.
- **Expected Outcome**: `TypeError` is raised.

#### 3. _load_tree Raises TypeError — Propagates
- **Test Name**: `test_load_tree_raises_typeerror_propagates`
- **Description**: `_load_tree` raises a `TypeError` (e.g., the file cannot be parsed).
- **Expected Outcome**: The `TypeError` propagates out of `__init__` unchanged.

#### 4. Valid File — Root Tag in xml_types (Pin)
- **Test Name**: `test_init_valid_root_tag_sets_attributes[pin_type]`
- **Description**: `_load_tree` returns a tree whose root tag (`Pin`) is in `xml_types`.
- **Expected Outcome**: Instance is created successfully with `_xml_type` set to `Pin`.

### TestJsonToXml
Tests `_json_to_xml` which reads a JSON file, converts it to an `ElementTree` via `_build_etree_node` and `_pretty_format`, and returns the tree.

#### 1. Valid JSON File — Returns Converted ElementTree and Calls Pretty Format
- **Test Name**: `test_valid_json_returns_converted_element_tree`
- **Description**: `open` and `json.load` are mocked to supply a valid JSON dict; `ET.Element` and `ET.ElementTree` are fully mocked to return mock objects; `_build_etree_node` appends a mock `SubElement`; `_pretty_format` is a no-op mock.
- **Expected Outcome**: The returned tree's root tag matches the element appended by the mock `_build_etree_node` and `_pretty_format` is called exactly once.

### TestBuildEtreeNode
Tests `_build_etree_node` which builds an `ElementTree SubElement` from a dict and attaches it as a child of parent, recursing into children. All ET operations are fully mocked.

#### 1. Dict With All Optional Fields
- **Test Name**: `test_dict_with_all_optional_fields`
- **Description**: The input dict contains `name`, `attrib`, `text`, `tail`, and a single child dict with `name` only. `ET.SubElement` is mocked to return mock elements.
- **Expected Outcome**: The mock `SubElement` is created with the correct tag, attributes, text, and tail; a nested mock `SubElement` is created for the child.

#### 2. Dict With Name Only
- **Test Name**: `test_dict_with_name_only`
- **Description**: The input dict contains only the `name` key. `ET.SubElement` is mocked to return mock elements.
- **Expected Outcome**: The mock `SubElement` is created with the correct tag, empty `attrib` dict, `None` text, `None` tail, and no children.

### TestPrettyFormat
Tests `_pretty_format` which recursively adds indentation whitespace to all nodes in the `ElementTree` for human-readable formatting. All elements are fully mocked.

#### 1. Called With Parent and index=0 — Sets parent.text
- **Test Name**: `test_pretty_format_parent_text_by_index[index_zero]`
- **Description**: A leaf element is passed along with its parent and `index=0` at a specific depth.
- **Expected Outcome**: `parent.text` is set to a newline followed by the correct number of two-space indents for the given depth.

#### 2. Called With Parent and index != 0 — Does Not Modify parent.text
- **Test Name**: `test_pretty_format_parent_text_by_index[index_nonzero]`
- **Description**: A leaf element is passed along with its parent and `index=1`.
- **Expected Outcome**: `parent.text` is not modified.

#### 3. Called Without Parent — Completes Without Error
- **Test Name**: `test_no_parent_completes_without_error`
- **Description**: `_pretty_format` is called on the root element with the default `parent=None`.
- **Expected Outcome**: The call completes without raising any exception.

#### 4. Recurses Into Children — Sets Indentation at Every Level
- **Test Name**: `test_pretty_format_recurses_into_children`
- **Description**: `_pretty_format` is called on a root that has a child which itself has a grandchild.
- **Expected Outcome**: `root.text` and `child.text` are each set to the correct newline-plus-indent string for their respective depths.

### TestLoadTree
Tests `_load_tree` which loads an `ElementTree` from a `.xml` or `.json` file, raising `TypeError` if the extension is unsupported or parsing fails.

#### 1. XML Extension — Returns ElementTree
- **Test Name**: `test_xml_extension_returns_element_tree`
- **Description**: `fileref` has a `.xml` extension; `ET.ElementTree` is patched to return a mock tree.
- **Expected Outcome**: `ET.ElementTree` is called with `file=fileref` and its return value is returned.

#### 2. JSON Extension — Delegates to _json_to_xml
- **Test Name**: `test_json_extension_delegates_to_json_to_xml`
- **Description**: `fileref` has a `.json` extension; `_json_to_xml` is mocked on the instance.
- **Expected Outcome**: `self._json_to_xml` is called with `fileref` and its return value is returned.

#### 3. Unsupported Extension — Raises TypeError
- **Test Name**: `test_unsupported_extension_raises_typeerror`
- **Description**: `fileref` has an extension other than `.xml` or `.json` (e.g., `.xyz`).
- **Expected Outcome**: `TypeError` is raised.

#### 4. File Parse Error — Raises TypeError
- **Test Name**: `test_file_parse_error_raises_typeerror`
- **Description**: `ET.ElementTree` is patched to raise an `Exception` during parsing.
- **Expected Outcome**: The exception is caught and re-raised as a `TypeError`.

#### 5. JSON Parse Error — Raises TypeError
- **Test Name**: `test_json_parse_error_raises_typeerror`
- **Description**: `_json_to_xml` is mocked to raise an `Exception` during JSON parsing.
- **Expected Outcome**: The exception is caught and re-raised as a `TypeError`.


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
