# Test Cases for `ManifestXml` Class

## Test Cases

### TestValidateRepoLocalRootOrRaise
Tests `_validate_repo_local_root_or_raise` which raises `ValueError` if a repository local root has only one path component.

#### 1. Raises ValueError for Single-Component Path
- **Test Name**: `test_validate_repo_local_root_raises_for_single_component_path`
- **Description**: When `repo_local_root` consists of only one path component (e.g., `'invalid_path'`).
- **Expected Outcome**: `ValueError` is raised containing `INVALID_REPO_PATH_ERROR`.

#### 2. Does Not Raise for Multi-Component Path
- **Test Name**: `test_validate_repo_local_root_does_not_raise_for_multi_component_path`
- **Description**: When `repo_local_root` has multiple path components (e.g., `'parent_repo/child_repo'`).
- **Expected Outcome**: No exception is raised.

### TestIsPinFile
Tests `is_pin_file` which returns `True` when the parsed XML is a Pin file, `False` otherwise.

#### 1. Returns True When XML Type Is Pin
- **Test Name**: `test_is_pin_file[xml_type_pin]`
- **Description**: When `_xml_type` is set to `'Pin'`.
- **Expected Outcome**: `is_pin_file()` returns `True`.

#### 2. Returns False When XML Type Is Manifest
- **Test Name**: `test_is_pin_file[xml_type_manifest]`
- **Description**: When `_xml_type` is set to `'Manifest'`.
- **Expected Outcome**: `is_pin_file()` returns `False`.

### TestGetRemote
Tests `get_remote` which returns the remote object for a given name, or `None` if absent.

#### 1. Returns Remote Object When Found
- **Test Name**: `test_get_remote_returns_remote_object_when_found`
- **Description**: When `remote_name` is present in `_remotes`.
- **Expected Outcome**: The corresponding remote object is returned.

#### 2. Returns None When Not Found
- **Test Name**: `test_get_remote_returns_none_when_not_found`
- **Description**: When `remote_name` is absent from `_remotes`.
- **Expected Outcome**: `None` is returned.

### TestGetRemotesDict
Tests `get_remotes_dict` which returns a mapping of remote names to URLs.

#### 1. Returns Name-to-URL Mapping
- **Test Name**: `test_get_remotes_dict_returns_name_to_url_mapping`
- **Description**: When `_remotes` contains one or more entries.
- **Expected Outcome**: A dict `{name: url}` is returned for each remote.

### TestGetRepoSources
Tests `get_repo_sources` which returns the `RepoSource` tuples for a given combination name, with fallback for pin-prefixed names and an error for unknown names.

#### 1. Returns Tuple List When Combo Found
- **Test Name**: `test_get_repo_sources_returns_tuple_list_when_combo_found`
- **Description**: When `combo_name` is present in `_combo_sources`.
- **Expected Outcome**: Returns the list of `RepoSource` tuples for that combo.

#### 2. Returns Default Combo Sources for Pin Prefix
- **Test Name**: `test_get_repo_sources_returns_default_combo_sources_for_pin_prefix`
- **Description**: When `combo_name` starts with `'Pin:'`.
- **Expected Outcome**: Returns the sources for the default combo from `general_config`.

#### 3. Raises ValueError When Combo Not Found
- **Test Name**: `test_get_repo_sources_raises_value_error_when_combo_not_found`
- **Description**: When `combo_name` is absent and does not start with `'Pin:'`.
- **Expected Outcome**: `ValueError` is raised containing `COMBO_INVALIDINPUT_ERROR`.

### TestGetParentOfNestedRepo
Tests `get_parent_of_nested_repo` which returns the parent `RepoSource` for a nested repository path, delegating path validation to `_validate_repo_local_root_or_raise`.

#### 1. Raises for Non-Nested Path
- **Test Name**: `test_get_parent_of_nested_repo_raises[non_nested_path]`
- **Description**: When `repo_local_root` has only one path component.
- **Expected Outcome**: `ValueError` is raised containing `INVALID_REPO_PATH_ERROR`.

#### 2. Returns Direct Parent
- **Test Name**: `test_get_parent_of_nested_repo_returns_direct_parent`
- **Description**: When a source in the list matches the direct parent directory.
- **Expected Outcome**: That source object is returned.

#### 3. Raises When No Parent Found
- **Test Name**: `test_get_parent_of_nested_repo_raises[no_parent_found]`
- **Description**: When no source matches any ancestor directory.
- **Expected Outcome**: `ValueError` is raised containing `NO_PARENT_REPO_ERROR`.

### TestGetComboElement
Tests `get_combo_element` which returns a deep copy of the named `<Combination>` element, or raises `ValueError` if absent.

#### 1. Returns Deepcopy When Found
- **Test Name**: `test_get_combo_element_returns_deepcopy_when_found`
- **Description**: When a `<Combination>` with the given name exists in the XML tree.
- **Expected Outcome**: A deepcopy of the element is returned.

#### 2. Raises ValueError When Not Found
- **Test Name**: `test_get_combo_element_raises_value_error_when_not_found`
- **Description**: When no `<Combination>` with the given name exists in the XML tree.
- **Expected Outcome**: `ValueError` is raised containing the combination name.

### TestGetSubmoduleAlternatesForRemote
Tests `get_submodule_alternates_for_remote` which filters alternate remote entries by remote name.

#### 1. Returns Matching Alternates for Remote
- **Test Name**: `test_get_submodule_alternates_for_remote[matching_remote]`
- **Description**: When one or more entries have the matching `remote_name`.
- **Expected Outcome**: A list of the matching tuples is returned.

#### 2. Returns Empty List When No Match
- **Test Name**: `test_get_submodule_alternates_for_remote[no_match]`
- **Description**: When no entry has the requested `remote_name`.
- **Expected Outcome**: An empty list is returned.

### TestGetSubmoduleInitPaths
Tests `get_submodule_init_paths` which returns submodule init tuples filtered by `remote_name` and/or `combo`.

#### 1. Returns All When No Filters
- **Test Name**: `test_get_submodule_init_paths_returns_all_when_no_filters`
- **Description**: When both `remote_name` and `combo` are `None`.
- **Expected Outcome**: Tuples for all entries in `_submodule_init_list` are returned.

#### 2. Filters by Remote Name
- **Test Name**: `test_get_submodule_init_paths_filters_by_remote_name`
- **Description**: When only `remote_name` is provided.
- **Expected Outcome**: Only tuples for entries whose `remote_name` matches are returned.

#### 3. Filters by Combo
- **Test Name**: `test_get_submodule_init_paths_filters_by_combo`
- **Description**: When only `combo` is provided.
- **Expected Outcome**: Tuples for entries whose `combo` matches or is `None` are returned.

#### 4. Filters by Remote Name and Combo
- **Test Name**: `test_get_submodule_init_paths_filters_by_remote_and_combo`
- **Description**: When both `remote_name` and `combo` are provided.
- **Expected Outcome**: Only tuples for entries matching both filters are returned.

### TestGetPatchset
Tests `get_patchset` which returns the `PatchSet` for `(name, remote)`, or raises `KeyError` if not found.

#### 1. Returns PatchSet When Found
- **Test Name**: `test_get_patchset_returns_patchset_when_found`
- **Description**: When `(name, remote)` is present in `_patch_sets`.
- **Expected Outcome**: The corresponding `PatchSet` namedtuple is returned.

#### 2. Raises KeyError When Not Found
- **Test Name**: `test_get_patchset_raises_key_error_when_not_found`
- **Description**: When `(name, remote)` is absent from `_patch_sets`.
- **Expected Outcome**: `KeyError` is raised containing the patchset name.

### TestGetPatchsetsForCombo
Tests `get_patchsets_for_combo` which returns a dict of patchsets for a combo, scanning all combos when `combo=None`.

#### 1. Returns All Patchsets When Combo Is None
- **Test Name**: `test_get_patchsets_for_combo_returns_patchset[combo_none]`
- **Description**: When `combo` is `None`, all combos are scanned.
- **Expected Outcome**: A dict keyed by combo name containing the found patchsets is returned.

#### 2. Returns Matching Patchsets When Combo Is Specified
- **Test Name**: `test_get_patchsets_for_combo_returns_patchset[combo_specified]`
- **Description**: When a specific `combo` is provided and it has patchset sources.
- **Expected Outcome**: A dict keyed by that combo name containing its patchset is returned.

#### 3. Raises KeyError When No Patchsets in Combo
- **Test Name**: `test_get_patchsets_for_combo_raises_key_error_when_no_patchsets_in_combo`
- **Description**: When the specified combo has no sources with a `patchSet` attribute.
- **Expected Outcome**: `KeyError` is raised containing the combo name.

### TestGetPatchsetOperations
Tests `get_patchset_operations` which returns the ordered list of patchset operations, detecting circular dependencies.

#### 1. Returns Operations List When Patchset Found
- **Test Name**: `test_get_patchset_operations_returns_list_when_patchset_found`
- **Description**: When `(name, remote)` is in `_patch_sets` with no circular parent chain.
- **Expected Outcome**: A list containing the operations list is returned.

#### 2. Raises ValueError on Circular Dependency
- **Test Name**: `test_get_patchset_operations_raises_on_circular_dependency`
- **Description**: When `get_parent_patchset_operations` causes a `RecursionError`.
- **Expected Outcome**: `ValueError` is raised with `PATCHSET_PARENT_CIRCULAR_DEPENDENCY`.

#### 3. Raises ValueError When Patchset Not Found
- **Test Name**: `test_get_patchset_operations_raises_value_error_when_not_found`
- **Description**: When `(name, remote)` is absent from `_patch_sets`.
- **Expected Outcome**: `ValueError` is raised containing the patchset name.

### TestInit
Tests `ManifestXml.__init__` which initializes common collections for all manifest types.

#### 1. Common Collections Initialized
- **Test Name**: `test_init_common_collections_initialized`
- **Description**: When a `ManifestXml` instance is created.
- **Expected Outcome**: Collections such as `_remotes`, `_combo_sources`, `_patch_sets`, etc. are initialized to empty containers.

### TestGeneratePinJson
Tests `generate_pin_json` which generates a JSON representation of pin data and optionally writes it to a file.

#### 1. Writes File with JSON Output
- **Test Name**: `test_generate_pin_json_writes_file_with_json_output`
- **Description**: When called with a filename.
- **Expected Outcome**: The JSON representation is written to the specified file.


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
