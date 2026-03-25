# Test Cases for `cache_command` Module

## Test Cases

### TestCacheCommand
All unit tests for the private helper functions of the `cache_command` module are
contained in a single test class. Shared constants (remote names, URLs, SHAs, paths,
etc.) are defined as class-level attributes and reused across tests.

#### `_create_cache_json_object`
Converts a list of cache info items into a JSON-serialisable list of dictionaries.

##### 1. Normal Info List — `test_normal_info_list_produces_correct_dicts`
- **Description**: A non-empty list of two items built from `CACHE_REPO1_*` / `CACHE_REPO2_*` constants, each with `path`, `remote`, and `url` attributes, is provided.
- **Expected Outcome**: Returns a list of two dicts each containing the correct `path`, `remote`, and `url` values.

##### 2. Empty Info List — `test_empty_info_list_returns_empty_list`
- **Description**: An empty list is provided.
- **Expected Outcome**: Returns an empty list.

#### `_get_manifest`
Loads and returns a `ManifestXml` for a given project, resolving the manifest file
path either directly or through the manifest index.

##### 1. Project Is an Existing File Path — `test_project_is_existing_file_loads_manifest_directly`
- **Description**: `project` is `MANIFEST_PATH_EXISTING`; `os.path.exists` returns `True`.
- **Expected Outcome**: `ManifestXml` is constructed directly with `MANIFEST_PATH_EXISTING` and returned. `find_project_in_all_indices` is never called.

##### 2. Project Name Found in Indices — `test_project_name_found_in_indices`
- **Description**: `project` is `PROJECT_NAME`; `os.path.exists` returns `False` but `find_project_in_all_indices` resolves `MANIFEST_PATH_RESOLVED`.
- **Expected Outcome**: `ManifestXml` is constructed with `MANIFEST_PATH_RESOLVED` and returned.

##### 3. Project Name Not Found in Indices — `test_project_name_not_found_raises_load_exception`
- **Description**: `project` is `PROJECT_NAME_MISSING`; `os.path.exists` returns `False` and `find_project_in_all_indices` raises an exception.
- **Expected Outcome**: Raises `EdkrepoCacheException` with the `UNABLE_TO_LOAD_MANIFEST` message.

##### 4. Manifest File Cannot Be Parsed — `test_manifest_parse_failure_raises_parse_exception`
- **Description**: `project` is `MANIFEST_PATH_BAD`; `os.path.exists` returns `True` but `ManifestXml` raises an exception.
- **Expected Outcome**: Raises `EdkrepoCacheException` with the `UNABLE_TO_PARSE_MANIFEST` message.

#### `_resolve_manifest`
Returns a `ManifestXml` instance for the current invocation or `None` when no
manifest can be found.

##### 1. Project Argument Provided — `test_project_arg_provided_delegates_to_get_manifest`
- **Description**: `args.project` is set to `PROJECT_NAME` and `args.source_manifest_repo` to `SOURCE_MANIFEST_REPO`.
- **Expected Outcome**: Delegates to `_get_manifest` with `PROJECT_NAME`, the local `config` dict, and `SOURCE_MANIFEST_REPO`, and returns the resulting manifest.

##### 2. No Project Argument, Workspace Manifest Found — `test_no_project_arg_workspace_manifest_found`
- **Description**: `args.project` is `None` and `get_workspace_manifest` succeeds.
- **Expected Outcome**: Returns the manifest returned by `get_workspace_manifest`.

##### 3. No Project Argument, Workspace Manifest Not Found — `test_no_project_arg_workspace_manifest_not_found`
- **Description**: `args.project` is `None` and `get_workspace_manifest` raises an exception.
- **Expected Outcome**: Returns `None` without propagating the exception.

#### `_get_used_refs`
Iterates over all combos and sources in a manifest and builds a map of remote-name
to list-of-refs that are not yet present in the cache.

##### 1. Source With Uncached Commit — `test_uncached_commit_is_included`
- **Description**: A source with `commit=COMMIT_SHA`; `cache_obj.is_sha_cached` returns `False`.
- **Expected Outcome**: `COMMIT_SHA` is included in `used_refs` under `REMOTE_NAME`.

##### 2. Source With Already-Cached Commit — `test_already_cached_commit_is_excluded`
- **Description**: A source with `commit=COMMIT_SHA`; `cache_obj.is_sha_cached` returns `True`.
- **Expected Outcome**: `REMOTE_NAME` is absent from the result.

##### 3. Source With Uncached Tag — `test_uncached_tag_is_included`
- **Description**: A source with `tag=TAG_NAME`; `cache_obj.is_sha_cached` returns `False`.
- **Expected Outcome**: `TAG_NAME` is included in `used_refs` under `REMOTE_NAME`.

##### 4. Branch With Uncached Head SHA — `test_branch_with_uncached_head_sha_is_included`
- **Description**: A source with `branch=BRANCH_NAME`; `get_latest_sha` returns `SHA_HEAD` which is not yet cached.
- **Expected Outcome**: `BRANCH_NAME` is included in `used_refs` under `REMOTE_NAME`.

##### 5. Branch With Unresolvable Head SHA — `test_branch_with_unresolvable_head_sha_is_included`
- **Description**: A source with `branch=BRANCH_FEATURE`; `get_latest_sha` returns `None`.
- **Expected Outcome**: `BRANCH_FEATURE` is included in `used_refs` under `REMOTE_NAME`.

##### 6. Source With Patchset — `test_source_with_patchset_delegates_to_get_used_refs_patchset`
- **Description**: A source with `patch_set=PATCHSET_NAME`; `_get_used_refs_patchset` returns `{REMOTE_NAME: [SHA_FROM_PATCHSET]}`.
- **Expected Outcome**: `_get_used_refs_patchset` is called once and `SHA_FROM_PATCHSET` is merged into `used_refs` under `REMOTE_NAME`.

#### `_get_used_refs_patchset`
Collects commit SHAs from `CherryPick` and `Revert` patchset operations into a
remote-keyed dict.

##### 1. CherryPick and Revert Operations Collected — `test_cherrypick_and_revert_operations_are_collected`
- **Description**: The patchset contains a `CherryPick` operation with `SHA_CHERRYPICK` and a `Revert` operation with `SHA_REVERT`, both sourced from `REMOTE_NAME`.
- **Expected Outcome**: Both SHAs appear in `used_refs` under `REMOTE_NAME`.

##### 2. Only Unsupported Operation Types Present — `test_unsupported_operation_types_are_ignored`
- **Description**: The patchset contains only an `Apply` operation with `SHA_APPLY`.
- **Expected Outcome**: Returns an empty `defaultdict`; no entries are added.

#### `_get_operation_remote`
Resolves the effective remote for a patchset operation, falling back to the
patchset remote when the operation has none of its own.

##### 1. Operation Has a Source Remote — `test_operation_with_source_remote_returns_source_remote`
- **Description**: A local `operation` mock has `source_remote` set to `REMOTE_EXPLICIT`; a local `patchset` mock has `remote` set to `REMOTE_PATCHSET`.
- **Expected Outcome**: Returns `REMOTE_EXPLICIT`.

##### 2. Operation Has No Source Remote — `test_operation_without_source_remote_returns_patchset_remote`
- **Description**: A local `operation` mock has `source_remote` set to `None`; a local `patchset` mock has `remote` set to `REMOTE_PATCHSET`.
- **Expected Outcome**: Returns `REMOTE_PATCHSET`.

#### `_flatten_list`
Flattens one level of nesting from a list of lists.

##### 1. Nested List — `test_nested_list_is_flattened`
- **Description**: `[[1, 2], [3, 4], [5]]` is provided.
- **Expected Outcome**: Returns `[1, 2, 3, 4, 5]`.

##### 2. Empty List — `test_empty_list_returns_empty_list`
- **Description**: An empty list is provided.
- **Expected Outcome**: Returns an empty list.

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
