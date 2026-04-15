# Test Cases for `_RepoSource` Class

## Test Cases

### TestParseRepoSourceRequiredAttribs
Tests `_parse_repo_source_required_attribs(element, remotes)` which validates required attributes `localRoot` and `remote`, raising `KeyError` for any missing required data.

#### 1. Returns root, remote_name, and remote_url When All Required Data Present
- **Description**: When the element has a `localRoot` attribute and a `remote` attribute that matches a key in the remotes dict.
- **Expected Outcome**: Returns `(root, remote_name, remote_url)` with correct values.

#### 2. Raises KeyError When localRoot Attribute Absent
- **Description**: When the element has no `localRoot` attribute.
- **Expected Outcome**: Raises `KeyError` whose string representation contains the expected `REQUIRED_ATTRIB_ERROR_MSG` prefix.

#### 3. Raises KeyError When remote Attribute Absent
- **Description**: When the element has no `remote` attribute.
- **Expected Outcome**: Raises `KeyError` whose string representation contains the expected `REQUIRED_ATTRIB_ERROR_MSG` prefix.

#### 4. Raises KeyError When remote Does Not Match Any Key in Remotes
- **Description**: When the element has a `remote` attribute that does not correspond to any key in the remotes dict.
- **Expected Outcome**: Raises `KeyError`.

### TestRepoSourceInit
Tests `_RepoSource.__init__` which parses a `<Source>` XML element including required fields, optional reference fields, boolean flags, and mutual-exclusivity guards.

#### 1. Sets root and remote_name and remote_url From Required Attributes
- **Description**: When the element has valid `localRoot` and `remote` attributes with a matching remotes entry.
- **Expected Outcome**: `self.root`, `self.remote_name`, and `self.remote_url` are set correctly.

#### 2. Sets branch When branch Attribute Present
- **Description**: When the element has a `branch` attribute.
- **Expected Outcome**: `self.branch` is set to the `branch` attribute value.

#### 3. Sets branch to None When branch Attribute Absent
- **Description**: When the element has no `branch` attribute.
- **Expected Outcome**: `self.branch` is `None`.

#### 4. Sets commit When commit Attribute Present
- **Description**: When the element has a `commit` attribute.
- **Expected Outcome**: `self.commit` is set to the `commit` attribute value.

#### 5. Sets tag When tag Attribute Present
- **Description**: When the element has a `tag` attribute.
- **Expected Outcome**: `self.tag` is set to the `tag` attribute value.

#### 6. Sets enableSub From Legacy enable_submodule Attribute
- **Description**: When the element uses the legacy `enable_submodule` attribute (underscore form) with value `"true"`.
- **Expected Outcome**: `self.enableSub` is `True`.

#### 7. Sets venv_cfg When venv_cfg Attribute Present
- **Description**: When the element has a `venv_cfg` attribute.
- **Expected Outcome**: `self.venv_cfg` is set to the `venv_cfg` attribute value.

#### 8. Sets commit to None When commit Attribute Absent
- **Description**: When the element has no `commit` attribute.
- **Expected Outcome**: `self.commit` is `None`.

#### 9. Sets tag to None When tag Attribute Absent
- **Description**: When the element has no `tag` attribute.
- **Expected Outcome**: `self.tag` is `None`.

#### 10. Sets patch_set to None When patchSet Attribute Absent
- **Description**: When the element has no `patchSet` attribute.
- **Expected Outcome**: `self.patch_set` is `None`.

#### 11. Sets venv_cfg to None When venv_cfg Attribute Absent
- **Description**: When the element has no `venv_cfg` attribute.
- **Expected Outcome**: `self.venv_cfg` is `None`.

#### 12. Sets patch_set When patchSet Attribute Present
- **Description**: When the element has a `patchSet` attribute (without branch/commit/tag).
- **Expected Outcome**: `self.patch_set` is set to the `patchSet` attribute value.

#### 13. Sets sparse to False When sparseCheckout Attribute Absent
- **Description**: When the element has no `sparseCheckout` attribute.
- **Expected Outcome**: `self.sparse` is `False`.

#### 14. Sets sparse to True When sparseCheckout Attribute is "true"
- **Description**: When the element has a `sparseCheckout` attribute with value `"true"`.
- **Expected Outcome**: `self.sparse` is `True`.

#### 15. Sets sparse to False When sparseCheckout Attribute is "false"
- **Description**: When the element has a `sparseCheckout` attribute with value `"false"`.
- **Expected Outcome**: `self.sparse` is `False`.

#### 16. Sets enableSub to False When enableSubmodule Attribute Absent
- **Description**: When the element has neither `enableSubmodule` nor `enable_submodule` attribute.
- **Expected Outcome**: `self.enableSub` is `False`.

#### 17. Sets enableSub to True When enableSubmodule Attribute is "true"
- **Description**: When the element has an `enableSubmodule` attribute with value `"true"`.
- **Expected Outcome**: `self.enableSub` is `True`.

#### 18. Sets enableSub to False When enableSubmodule Attribute is "false"
- **Description**: When the element has an `enableSubmodule` attribute with value `"false"`.
- **Expected Outcome**: `self.enableSub` is `False`.

#### 19. Sets blobless to False When blobless Attribute Absent
- **Description**: When the element has no `blobless` attribute.
- **Expected Outcome**: `self.blobless` is `False`.

#### 20. Sets blobless to True When blobless Attribute is "true"
- **Description**: When the element has a `blobless` attribute with value `"true"`.
- **Expected Outcome**: `self.blobless` is `True`.

#### 21. Sets blobless to False When blobless Attribute is "false"
- **Description**: When the element has a `blobless` attribute with value `"false"`.
- **Expected Outcome**: `self.blobless` is `False`.

#### 22. Sets treeless to False When treeless Attribute Absent
- **Description**: When the element has no `treeless` attribute.
- **Expected Outcome**: `self.treeless` is `False`.

#### 23. Sets treeless to True When treeless Attribute is "true"
- **Description**: When the element has a `treeless` attribute with value `"true"`.
- **Expected Outcome**: `self.treeless` is `True`.

#### 24. Sets treeless to False When treeless Attribute is "false"
- **Description**: When the element has a `treeless` attribute with value `"false"`.
- **Expected Outcome**: `self.treeless` is `False`.

#### 25. Sets nested_repo to True When localRoot Contains a Path Separator
- **Description**: When the `localRoot` value contains a `/` path separator (nested directory).
- **Expected Outcome**: `self.nested_repo` is `True`.

#### 26. Sets nested_repo to False When localRoot Is a Simple Name
- **Description**: When the `localRoot` value is a plain name with no path separator.
- **Expected Outcome**: `self.nested_repo` is `False`.

#### 27. Raises KeyError When No Reference Attribute Provided
- **Description**: When the element has no `branch`, `commit`, `tag`, or `patchSet` attribute.
- **Expected Outcome**: Raises `KeyError` indicating that a reference attribute is required.

#### 28. Raises ValueError When patchSet and branch Are Both Present
- **Description**: When the element has both a `patchSet` attribute and a `branch` attribute.
- **Expected Outcome**: Raises `ValueError` indicating mutual exclusivity violation.

#### 29. Raises ValueError When patchSet and commit Are Both Present
- **Description**: When the element has both a `patchSet` attribute and a `commit` attribute.
- **Expected Outcome**: Raises `ValueError` indicating mutual exclusivity violation.

#### 30. Raises ValueError When patchSet and tag Are Both Present
- **Description**: When the element has both a `patchSet` attribute and a `tag` attribute.
- **Expected Outcome**: Raises `ValueError` indicating mutual exclusivity violation.

### TestRepoSourceTuple
Tests `_RepoSource.tuple` which returns a `RepoSource` namedtuple.

#### 1. Returns Correct RepoSource Namedtuple
- **Description**: When all required attributes are present and a `branch` is set.
- **Expected Outcome**: `tuple` returns a `RepoSource` namedtuple with all fields correctly populated.


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

