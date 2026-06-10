#!/usr/bin/env python3
#
## @file
# base_tests.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import json
import os
import xml.etree.ElementTree as ET

import pytest


BRANCH_DEVELOP = 'develop'

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
COMPLETE_MANIFEST_XML = os.path.join(FIXTURES_DIR, 'complete_manifest.xml')
COMPLETE_MANIFEST_JSON = os.path.join(FIXTURES_DIR, 'complete_manifest.json')
MINIMAL_MANIFEST_XML = os.path.join(FIXTURES_DIR, 'minimal_manifest.xml')
INVALID_MANIFEST_XML = os.path.join(FIXTURES_DIR, 'invalid_manifest.xml')
MANIFEST_WITH_INCLUDE_XML = os.path.join(FIXTURES_DIR, 'manifest_with_include.xml')

# Complete manifest project info
COMPLETE_PROJECT_CODENAME = 'CompleteTestProject'
COMPLETE_PROJECT_DESCRIPTION = 'Complete test project with all features for integration testing'
COMPLETE_PROJECT_SHORT_NAME = 'CTP'
COMPLETE_PROJECT_ORG = 'TestOrg'

# Minimal manifest project info
MINIMAL_PROJECT_CODENAME = 'MinimalTestProject'
MINIMAL_PROJECT_DESCRIPTION = 'Minimal test project with only required fields'
MINIMAL_PROJECT_SHORT_NAME = 'MTP'

# Complete manifest combinations
COMBO_NAME_MAIN = 'main'
COMBO_NAME_DEV = 'dev'
COMBO_NAME_ARCHIVED = 'archived'
COMBO_DESC_MAIN = 'Main combination'

# Complete manifest remotes
COMPLETE_REMOTE_ORIGIN = 'origin'
COMPLETE_REMOTE_UPSTREAM = 'upstream'
COMPLETE_REMOTE_ORIGIN_URL = 'https://github.com/test/repo.git'

# Complete manifest repo sources
REPO_ROOT_MAIN = 'MainRepo'
REPO_ROOT_SUB = 'SubRepo'
REPO_ROOT_TEST = 'TestRepo'

# Complete manifest general config
PIN_PATH_VALUE = 'pins'

# Complete manifest patch sets
PATCHSET_NAME_TEST = 'test-patch'
PATCHSET_REMOTE_ORIGIN = 'origin'
PATCHSET_FETCH_REF = 'refs/changes/01/1001/1'
PATCHSET_NAME_NONEXISTENT = 'nonexistent'
PATCHSET_REMOTE_WRONG = 'wrong-remote'

# Complete manifest git hooks
GIT_HOOK_SOURCE = 'hooks/pre-commit'
GIT_HOOK_DEST_PATH = '.git/hooks'

# Expected counts
EXPECTED_COMPLETE_REMOTE_COUNT = 2
EXPECTED_MINIMAL_REMOTE_COUNT = 1
EXPECTED_COMPLETE_COMBO_COUNT = 2
EXPECTED_MINIMAL_COMBO_COUNT = 1
EXPECTED_COMPLETE_REPO_SOURCES_COUNT = 2
EXPECTED_MINIMAL_REPO_SOURCES_COUNT = 1
EXPECTED_ARCHIVED_COMBO_COUNT_WITH_ARCHIVED = 1
EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED = 0
EXPECTED_MINIMUM_SPARSE_DATA_COUNT = 1

# Manifest with include
EXPECTED_INCLUDE_REMOTE_COUNT = 2

PARAM_MANIFEST_FILE_PATH = 'manifest_file'
PARAM_ID_COMPLETE_MANIFEST_XML = 'complete_xml'
PARAM_ID_MINIMAL_MANIFEST_XML = 'minimal_xml'
PARAM_ID_COMPLETE_MANIFEST_JSON = 'complete_json'
PARAM_ID_MANIFEST_WITH_INCLUDE = 'with_include'

# Sparse checkout
SPARSE_BY_DEFAULT_FALSE = False
SPARSE_ALWAYS_INCLUDE_PATH_1 = 'src/core'
SPARSE_ALWAYS_INCLUDE_PATH_2 = 'docs'
EXPECTED_SPARSE_DATA_COUNT = 1
EXPECTED_ALWAYS_INCLUDE_COUNT = 2
EXPECTED_ALWAYS_EXCLUDE_COUNT = 0


class _ManifestFixtureMixin:
    """Shared fixtures providing complete and minimal ManifestXml instances for base test classes."""

    manifest_module: str = None

    @pytest.fixture
    def complete_manifest(self):
        """Return a ManifestXml instance loaded from complete_manifest.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.ManifestXml(COMPLETE_MANIFEST_XML)

    @pytest.fixture
    def minimal_manifest(self):
        """Return a ManifestXml instance loaded from minimal_manifest.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.ManifestXml(MINIMAL_MANIFEST_XML)


class BaseTestManifestParsingFlow(_ManifestFixtureMixin):

    @pytest.fixture
    def json_manifest(self):
        """Return a ManifestXml instance loaded from complete_manifest.json."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.ManifestXml(COMPLETE_MANIFEST_JSON)

    @pytest.fixture
    def manifest_with_include(self):
        """Return a ManifestXml instance loaded from manifest_with_include.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.ManifestXml(MANIFEST_WITH_INCLUDE_XML)

    def test_invalid_manifest_raises_type_error(self):
        """When loading an invalid manifest, ManifestXml must raise TypeError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(TypeError):
            manifest_mod.ManifestXml(INVALID_MANIFEST_XML)

    def test_complete_manifest_has_project_info(self, complete_manifest):
        """When loading a complete manifest, project_info property must return ProjectInfo with correct values."""
        project_info = complete_manifest.project_info
        assert project_info is not None
        assert project_info.codename == COMPLETE_PROJECT_CODENAME
        assert project_info.description == COMPLETE_PROJECT_DESCRIPTION
        assert project_info.short_name == COMPLETE_PROJECT_SHORT_NAME
        assert project_info.org == COMPLETE_PROJECT_ORG

    def test_minimal_manifest_has_project_info(self, minimal_manifest):
        """When loading a minimal manifest, project_info property must return ProjectInfo with required fields."""
        project_info = minimal_manifest.project_info
        assert project_info is not None
        assert project_info.codename == MINIMAL_PROJECT_CODENAME
        assert project_info.description == MINIMAL_PROJECT_DESCRIPTION
        assert project_info.short_name == MINIMAL_PROJECT_SHORT_NAME

    def test_complete_manifest_has_general_config(self, complete_manifest):
        """When loading a complete manifest, general_config property must return GeneralConfig with correct values."""
        general_config = complete_manifest.general_config
        assert general_config is not None
        assert general_config.default_combo == COMBO_NAME_MAIN
        assert general_config.current_combo == COMBO_NAME_DEV
        assert general_config.pin_path == PIN_PATH_VALUE

    def test_minimal_manifest_has_general_config(self, minimal_manifest):
        """When loading a minimal manifest, general_config property must return GeneralConfig with required values."""
        general_config = minimal_manifest.general_config
        assert general_config is not None
        assert general_config.default_combo == COMBO_NAME_MAIN
        assert general_config.current_combo == COMBO_NAME_MAIN

    def test_complete_manifest_has_remotes(self, complete_manifest):
        """When loading a complete manifest with remotes, remotes property must return list of RemoteRepo tuples."""
        remotes = complete_manifest.remotes
        assert len(remotes) == EXPECTED_COMPLETE_REMOTE_COUNT
        remote_names = [r.name for r in remotes]
        assert COMPLETE_REMOTE_ORIGIN in remote_names
        assert COMPLETE_REMOTE_UPSTREAM in remote_names

    def test_minimal_manifest_has_remotes(self, minimal_manifest):
        """When loading a minimal manifest with one remote, remotes property must return list with one RemoteRepo."""
        remotes = minimal_manifest.remotes
        assert len(remotes) == EXPECTED_MINIMAL_REMOTE_COUNT
        assert remotes[LIST_INDEX_FIRST].name == COMPLETE_REMOTE_ORIGIN
        assert remotes[LIST_INDEX_FIRST].url == COMPLETE_REMOTE_ORIGIN_URL

    def test_complete_manifest_has_combinations(self, complete_manifest):
        """When loading a complete manifest, combinations property must return list of non-archived combinations."""
        combinations = complete_manifest.combinations
        assert len(combinations) == EXPECTED_COMPLETE_COMBO_COUNT
        combo_names = [c.name for c in combinations]
        assert COMBO_NAME_MAIN in combo_names
        assert COMBO_NAME_DEV in combo_names
        assert COMBO_NAME_ARCHIVED not in combo_names

    def test_minimal_manifest_has_combinations(self, minimal_manifest):
        """When loading a minimal manifest, combinations property must return list with required combination."""
        combinations = minimal_manifest.combinations
        assert len(combinations) == EXPECTED_MINIMAL_COMBO_COUNT
        assert combinations[LIST_INDEX_FIRST].name == COMBO_NAME_MAIN
        assert combinations[LIST_INDEX_FIRST].description == COMBO_DESC_MAIN

    def test_complete_manifest_get_repo_sources_for_main_combo(self, complete_manifest):
        """When requesting sources for main combination, get_repo_sources must return correct sources."""
        sources = complete_manifest.get_repo_sources(COMBO_NAME_MAIN)
        assert len(sources) == EXPECTED_COMPLETE_REPO_SOURCES_COUNT
        source_roots = [s.root for s in sources]
        assert REPO_ROOT_MAIN in source_roots
        assert REPO_ROOT_SUB in source_roots

    def test_complete_manifest_get_repo_sources_for_dev_combo(self, complete_manifest):
        """When requesting sources for dev combination, get_repo_sources must return correct sources."""
        sources = complete_manifest.get_repo_sources(COMBO_NAME_DEV)
        assert len(sources) == EXPECTED_COMPLETE_REPO_SOURCES_COUNT
        for source in sources:
            if source.root == REPO_ROOT_MAIN:
                assert source.branch == BRANCH_DEVELOP
            elif source.root == REPO_ROOT_SUB:
                assert source.branch == BRANCH_DEVELOP

    def test_minimal_manifest_get_repo_sources_for_main_combo(self, minimal_manifest):
        """When requesting sources for main combination in minimal manifest, get_repo_sources must return one source."""
        sources = minimal_manifest.get_repo_sources(COMBO_NAME_MAIN)
        assert len(sources) == EXPECTED_MINIMAL_REPO_SOURCES_COUNT
        assert sources[LIST_INDEX_FIRST].root == REPO_ROOT_TEST
        assert sources[LIST_INDEX_FIRST].remote_name == COMPLETE_REMOTE_ORIGIN
        assert sources[LIST_INDEX_FIRST].branch == COMBO_NAME_MAIN

    def test_complete_manifest_has_sparse_settings(self, complete_manifest):
        """When loading a manifest with sparse checkout settings, sparse_settings property must return SparseSettings."""
        sparse_settings = complete_manifest.sparse_settings
        assert sparse_settings is not None
        assert sparse_settings.sparse_by_default is SPARSE_BY_DEFAULT_FALSE

    def test_complete_manifest_has_sparse_data(self, complete_manifest):
        """When loading a manifest with sparse data, sparse_data property must return list of SparseData."""
        sparse_data = complete_manifest.sparse_data
        assert len(sparse_data) > EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED
        main_sparse = [sd for sd in sparse_data if sd.combination == COMBO_NAME_MAIN]
        assert len(main_sparse) >= EXPECTED_MINIMUM_SPARSE_DATA_COUNT

    def test_complete_manifest_has_patch_sets(self, complete_manifest):
        """When loading a manifest with patch sets, get_patchset method must return PatchSet for valid name and remote."""
        patch_set = complete_manifest.get_patchset(PATCHSET_NAME_TEST, PATCHSET_REMOTE_ORIGIN)
        assert patch_set is not None
        assert patch_set.name == PATCHSET_NAME_TEST
        assert patch_set.remote == PATCHSET_REMOTE_ORIGIN
        assert patch_set.fetch_branch == PATCHSET_FETCH_REF

    def test_complete_manifest_has_folder_mappings(self, complete_manifest):
        """When loading a manifest with folder mappings, folder_to_folder_mappings property must return list of mappings."""
        mappings = complete_manifest.folder_to_folder_mappings
        assert len(mappings) > EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED
        assert mappings[LIST_INDEX_FIRST].project1 == REPO_ROOT_MAIN
        assert mappings[LIST_INDEX_FIRST].project2 == REPO_ROOT_SUB

    def test_complete_manifest_has_client_git_hooks(self, complete_manifest):
        """When loading a manifest with git hooks, repo_hooks property must return list of hooks."""
        hooks = complete_manifest.repo_hooks
        assert len(hooks) > EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED
        assert hooks[LIST_INDEX_FIRST].source == GIT_HOOK_SOURCE
        assert hooks[LIST_INDEX_FIRST].dest_path == GIT_HOOK_DEST_PATH

    def test_json_manifest_parses_project_info_correctly(self, json_manifest):
        """When loading a JSON manifest, project_info property must return correct ProjectInfo."""
        project_info = json_manifest.project_info
        assert project_info is not None
        assert project_info.codename == COMPLETE_PROJECT_CODENAME

    def test_json_manifest_parses_combinations_correctly(self, json_manifest):
        """When loading a JSON manifest, combinations property must return correct combinations."""
        combinations = json_manifest.combinations
        assert len(combinations) == EXPECTED_COMPLETE_COMBO_COUNT

    def test_complete_manifest_get_archived_combinations(self, complete_manifest):
        """When requesting archived combinations, archived_combinations property must return archived entries."""
        archived = complete_manifest.archived_combinations
        assert len(archived) == EXPECTED_ARCHIVED_COMBO_COUNT_WITH_ARCHIVED
        archived_names = [c.name for c in archived]
        assert COMBO_NAME_ARCHIVED in archived_names

    def test_minimal_manifest_has_no_archived_combinations(self, minimal_manifest):
        """When loading a minimal manifest without archived combinations, archived_combinations property must return empty list."""
        archived = minimal_manifest.archived_combinations
        assert len(archived) == EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED

    def test_manifest_with_include_merges_remotes(self, manifest_with_include):
        """When loading a manifest with includes, remotes property must include remotes from included file."""
        remotes = manifest_with_include.remotes
        assert len(remotes) >= EXPECTED_INCLUDE_REMOTE_COUNT

    @pytest.mark.parametrize(PARAM_MANIFEST_FILE_PATH, [
        pytest.param(COMPLETE_MANIFEST_XML, id=PARAM_ID_COMPLETE_MANIFEST_XML),
        pytest.param(MINIMAL_MANIFEST_XML, id=PARAM_ID_MINIMAL_MANIFEST_XML),
        pytest.param(COMPLETE_MANIFEST_JSON, id=PARAM_ID_COMPLETE_MANIFEST_JSON),
        pytest.param(MANIFEST_WITH_INCLUDE_XML, id=PARAM_ID_MANIFEST_WITH_INCLUDE),
    ])
    def test_manifest_loads_successfully(self, manifest_file):
        """When loading any supported manifest file, ManifestXml must initialize without error."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        manifest = manifest_mod.ManifestXml(manifest_file)
        assert manifest is not None


ATTRIB_ROOT = 'root'
ATTRIB_REMOTE_NAME = 'remote_name'
ATTRIB_BRANCH = 'branch'
PARAM_ATTR_EXPECTED = 'attr,expected'


class BaseTestCombinationResolutionFlow(_ManifestFixtureMixin):

    def test_combination_has_description(self, complete_manifest):
        """When retrieving combination, combination object must have description attribute."""
        combinations = complete_manifest.combinations
        main_combo = [c for c in combinations if c.name == COMBO_NAME_MAIN][EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert main_combo.description == COMBO_DESC_MAIN

    def test_minimal_manifest_default_and_current_same(self, minimal_manifest):
        """When loading minimal manifest, default_combo and current_combo must be identical."""
        general_config = minimal_manifest.general_config
        assert general_config.default_combo == general_config.current_combo
        assert general_config.default_combo == COMBO_NAME_MAIN

    def test_combination_sources_have_required_fields(self, complete_manifest):
        """When retrieving sources for combination, each source must have root, remote_name, and branch."""
        sources = complete_manifest.get_repo_sources(COMBO_NAME_MAIN)
        for source in sources:
            assert hasattr(source, ATTRIB_ROOT)
            assert hasattr(source, ATTRIB_REMOTE_NAME)
            assert hasattr(source, ATTRIB_BRANCH)
            assert source.root is not None
            assert source.remote_name is not None
            assert source.branch is not None


ATTRIB_REMOTE = 'remote'
ATTRIB_FETCH_BRANCH = 'fetch_branch'
PARAM_PATCHSET_INVALID_LOOKUP = 'name,remote'
PARAM_ID_NONEXISTENT_PATCHSET = 'nonexistent_name'
PARAM_ID_WRONG_REMOTE_PATCHSET = 'wrong_remote'


class BaseTestPatchSetResolutionFlow(_ManifestFixtureMixin):

    def test_get_patchset_by_name_and_remote(self, complete_manifest):
        """When requesting patchset by name and remote, get_patchset must return matching PatchSet."""
        patch_set = complete_manifest.get_patchset(PATCHSET_NAME_TEST, PATCHSET_REMOTE_ORIGIN)
        assert patch_set is not None
        assert patch_set.name == PATCHSET_NAME_TEST

    @pytest.mark.parametrize(PARAM_ATTR_EXPECTED, [
        pytest.param(ATTRIB_REMOTE, PATCHSET_REMOTE_ORIGIN, id=ATTRIB_REMOTE),
        pytest.param(ATTRIB_FETCH_BRANCH, PATCHSET_FETCH_REF, id=ATTRIB_FETCH_BRANCH),
    ])
    def test_patchset_has_attribute(self, complete_manifest, attr, expected):
        """When retrieving patchset, required attribute must be present with correct value."""
        patch_set = complete_manifest.get_patchset(PATCHSET_NAME_TEST, PATCHSET_REMOTE_ORIGIN)
        assert hasattr(patch_set, attr)
        assert getattr(patch_set, attr) == expected

    @pytest.mark.parametrize(PARAM_PATCHSET_INVALID_LOOKUP, [
        pytest.param(PATCHSET_NAME_NONEXISTENT, PATCHSET_REMOTE_ORIGIN, id=PARAM_ID_NONEXISTENT_PATCHSET),
        pytest.param(PATCHSET_NAME_TEST, PATCHSET_REMOTE_WRONG, id=PARAM_ID_WRONG_REMOTE_PATCHSET),
    ])
    def test_invalid_patchset_lookup_raises_key_error(self, complete_manifest, name, remote):
        """When requesting patchset with nonexistent name or wrong remote, get_patchset must raise KeyError."""
        with pytest.raises(KeyError):
            complete_manifest.get_patchset(name, remote)


ATTRIB_SPARSE_BY_DEFAULT = 'sparse_by_default'
ATTRIB_COMBINATION = 'combination'
ATTRIB_ALWAYS_INCLUDE = 'always_include'
ATTRIB_ALWAYS_EXCLUDE = 'always_exclude'
PARAM_ATTR_EXPECTED_COUNT = 'attr,expected_count'


class BaseTestSparseCheckoutFlow(_ManifestFixtureMixin):

    def test_get_sparse_settings_from_manifest(self, complete_manifest):
        """When loading manifest with sparse settings, sparse_settings property must return SparseSettings object."""
        sparse_settings = complete_manifest.sparse_settings
        assert sparse_settings is not None

    def test_sparse_settings_has_sparse_by_default_attribute(self, complete_manifest):
        """When retrieving sparse settings, sparse_by_default attribute must be present and correct."""
        sparse_settings = complete_manifest.sparse_settings
        assert hasattr(sparse_settings, ATTRIB_SPARSE_BY_DEFAULT)
        assert sparse_settings.sparse_by_default == SPARSE_BY_DEFAULT_FALSE

    def test_get_sparse_data_from_manifest(self, complete_manifest):
        """When loading manifest with sparse data, sparse_data property must return list of SparseData objects."""
        sparse_data = complete_manifest.sparse_data
        assert isinstance(sparse_data, list)
        assert len(sparse_data) == EXPECTED_SPARSE_DATA_COUNT

    def test_sparse_data_always_include_contains_correct_paths(self, complete_manifest):
        """When retrieving sparse data, always_include list must contain configured paths."""
        sparse_data = complete_manifest.sparse_data
        first_data = sparse_data[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert SPARSE_ALWAYS_INCLUDE_PATH_1 in first_data.always_include
        assert SPARSE_ALWAYS_INCLUDE_PATH_2 in first_data.always_include

    def test_filter_sparse_data_by_combination(self, complete_manifest):
        """When filtering sparse data by combination, only matching entries must be returned."""
        sparse_data = complete_manifest.sparse_data
        main_sparse = [sd for sd in sparse_data if sd.combination == COMBO_NAME_MAIN]
        assert len(main_sparse) >= EXPECTED_MINIMUM_SPARSE_DATA_COUNT
        for sd in main_sparse:
            assert sd.combination == COMBO_NAME_MAIN

    def test_filter_sparse_data_by_remote(self, complete_manifest):
        """When filtering sparse data by remote, only matching entries must be returned."""
        sparse_data = complete_manifest.sparse_data
        origin_sparse = [sd for sd in sparse_data if sd.remote_name == COMPLETE_REMOTE_ORIGIN]
        assert len(origin_sparse) >= EXPECTED_MINIMUM_SPARSE_DATA_COUNT
        for sd in origin_sparse:
            assert sd.remote_name == COMPLETE_REMOTE_ORIGIN

    @pytest.mark.parametrize(PARAM_ATTR_EXPECTED, [
        pytest.param(ATTRIB_COMBINATION, COMBO_NAME_MAIN, id=ATTRIB_COMBINATION),
        pytest.param(ATTRIB_REMOTE_NAME, COMPLETE_REMOTE_ORIGIN, id=ATTRIB_REMOTE_NAME),
    ])
    def test_sparse_data_has_attribute(self, complete_manifest, attr, expected):
        """When retrieving sparse data, specified attribute must be present and match configured value."""
        sparse_data = complete_manifest.sparse_data
        first_data = sparse_data[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_data, attr)
        assert getattr(first_data, attr) == expected

    @pytest.mark.parametrize(PARAM_ATTR_EXPECTED_COUNT, [
        pytest.param(ATTRIB_ALWAYS_INCLUDE, EXPECTED_ALWAYS_INCLUDE_COUNT, id=ATTRIB_ALWAYS_INCLUDE),
        pytest.param(ATTRIB_ALWAYS_EXCLUDE, EXPECTED_ALWAYS_EXCLUDE_COUNT, id=ATTRIB_ALWAYS_EXCLUDE),
    ])
    def test_sparse_data_has_list_attribute(self, complete_manifest, attr, expected_count):
        """When retrieving sparse data, list attribute must be present and have correct item count."""
        sparse_data = complete_manifest.sparse_data
        first_data = sparse_data[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_data, attr)
        assert isinstance(getattr(first_data, attr), list)
        assert len(getattr(first_data, attr)) == expected_count


FOLDER_MAPPING_PROJECT1_FOLDER = 'shared/lib'
FOLDER_MAPPING_PROJECT2_FOLDER = 'vendor/lib'
FOLDER_MAPPING_EXCLUDE_PATH = '*.tmp'
EXPECTED_FOLDER_MAPPING_COUNT = 1
EXPECTED_FOLDER_COUNT_IN_MAPPING = 1
EXPECTED_EXCLUDE_COUNT_IN_FOLDER = 1

ATTRIB_PROJECT1 = 'project1'
ATTRIB_PROJECT2 = 'project2'
ATTRIB_FOLDERS = 'folders'
ATTRIB_PROJECT1_FOLDER = 'project1_folder'
ATTRIB_PROJECT2_FOLDER = 'project2_folder'
ATTRIB_EXCLUDES = 'excludes'
ATTRIB_PATH = 'path'


class BaseTestFolderMappingFlow(_ManifestFixtureMixin):

    def test_get_folder_mappings_from_manifest(self, complete_manifest):
        """When loading manifest with folder mappings, folder_to_folder_mappings property must return list."""
        mappings = complete_manifest.folder_to_folder_mappings
        assert isinstance(mappings, list)
        assert len(mappings) == EXPECTED_FOLDER_MAPPING_COUNT

    def test_folder_mapping_has_folders_list(self, complete_manifest):
        """When retrieving folder mapping, folders attribute must be a list of folder objects."""
        mappings = complete_manifest.folder_to_folder_mappings
        first_mapping = mappings[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_mapping, ATTRIB_FOLDERS)
        assert isinstance(first_mapping.folders, list)
        assert len(first_mapping.folders) == EXPECTED_FOLDER_COUNT_IN_MAPPING

    def test_folder_has_excludes_list(self, complete_manifest):
        """When retrieving folder from mapping, excludes attribute must be a list."""
        mappings = complete_manifest.folder_to_folder_mappings
        first_mapping = mappings[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        first_folder = first_mapping.folders[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_folder, ATTRIB_EXCLUDES)
        assert isinstance(first_folder.excludes, list)
        assert len(first_folder.excludes) == EXPECTED_EXCLUDE_COUNT_IN_FOLDER

    def test_folder_exclude_has_path_attribute(self, complete_manifest):
        """When retrieving exclude from folder, path attribute must match configured pattern."""
        mappings = complete_manifest.folder_to_folder_mappings
        first_mapping = mappings[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        first_folder = first_mapping.folders[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        first_exclude = first_folder.excludes[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_exclude, ATTRIB_PATH)
        assert first_exclude.path == FOLDER_MAPPING_EXCLUDE_PATH

    def test_filter_folder_mappings_by_project(self, complete_manifest):
        """When filtering folder mappings by project, only matching entries must be returned."""
        mappings = complete_manifest.folder_to_folder_mappings
        main_mappings = [m for m in mappings if m.project1 == REPO_ROOT_MAIN]
        assert len(main_mappings) >= EXPECTED_FOLDER_MAPPING_COUNT
        for mapping in main_mappings:
            assert mapping.project1 == REPO_ROOT_MAIN

    @pytest.mark.parametrize(PARAM_ATTR_EXPECTED, [
        pytest.param(ATTRIB_PROJECT1, REPO_ROOT_MAIN, id=ATTRIB_PROJECT1),
        pytest.param(ATTRIB_PROJECT2, REPO_ROOT_SUB, id=ATTRIB_PROJECT2),
        pytest.param(ATTRIB_REMOTE_NAME, COMPLETE_REMOTE_ORIGIN, id=ATTRIB_REMOTE_NAME),
    ])
    def test_folder_mapping_has_attribute(self, complete_manifest, attr, expected):
        """When retrieving folder mapping, specified attribute must be present and match configured value."""
        mappings = complete_manifest.folder_to_folder_mappings
        first_mapping = mappings[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_mapping, attr)
        assert getattr(first_mapping, attr) == expected

    @pytest.mark.parametrize(PARAM_ATTR_EXPECTED, [
        pytest.param(ATTRIB_PROJECT1_FOLDER, FOLDER_MAPPING_PROJECT1_FOLDER, id=ATTRIB_PROJECT1_FOLDER),
        pytest.param(ATTRIB_PROJECT2_FOLDER, FOLDER_MAPPING_PROJECT2_FOLDER, id=ATTRIB_PROJECT2_FOLDER),
    ])
    def test_folder_has_project_folder_attribute(self, complete_manifest, attr, expected):
        """When retrieving folder from mapping, specified project folder attribute must match configured path."""
        mappings = complete_manifest.folder_to_folder_mappings
        first_mapping = mappings[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        first_folder = first_mapping.folders[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert hasattr(first_folder, attr)
        assert getattr(first_folder, attr) == expected


VALIDATION_TYPE_PARSING = 'PARSING'
VALIDATION_TYPE_CODENAME = 'CODENAME'
VALIDATION_STATUS_SUCCESS = True
VALIDATION_STATUS_FAILURE = False
VALIDATION_RESULT_INDEX_TYPE = 0
VALIDATION_RESULT_INDEX_STATUS = 1
VALIDATION_RESULT_INDEX_MESSAGE = 2
RSPLIT_MAXSPLIT_ONE = 1
LIST_INDEX_FIRST = 0
VALIDATION_MODULE_SUFFIX = '.edk_manifest_validation'
PARAM_MANIFEST_PATH = 'manifest_path'
PARAM_ID_COMPLETE_MANIFEST = 'complete'
PARAM_ID_MINIMAL_MANIFEST = 'minimal'


class BaseTestValidationFlow:

    manifest_module: str = None

    @pytest.fixture
    def complete_manifest_path(self):
        """Return path to complete manifest XML file."""
        return COMPLETE_MANIFEST_XML

    @pytest.fixture
    def invalid_manifest_path(self):
        """Return path to invalid manifest XML file."""
        return INVALID_MANIFEST_XML

    @pytest.fixture
    def _validation_mod(self):
        """Return the validation module derived from the manifest module."""
        validation_module_name = self.__class__.manifest_module.rsplit('.', RSPLIT_MAXSPLIT_ONE)[LIST_INDEX_FIRST] + VALIDATION_MODULE_SUFFIX
        return importlib.import_module(validation_module_name)

    @pytest.fixture
    def validator_class(self, _validation_mod):
        """Return ValidateManifest class from the manifest module."""
        return _validation_mod.ValidateManifest

    def test_validate_invalid_manifest_fails_parsing(self, invalid_manifest_path, validator_class):
        """When validating invalid manifest, parsing validation must fail."""
        validator = validator_class(invalid_manifest_path)
        result = validator.validate_parsing()
        assert result[VALIDATION_RESULT_INDEX_TYPE] == VALIDATION_TYPE_PARSING
        assert result[VALIDATION_RESULT_INDEX_STATUS] == VALIDATION_STATUS_FAILURE
        assert result[VALIDATION_RESULT_INDEX_MESSAGE] is not None

    def test_validate_codename_matches_project(self, complete_manifest_path, validator_class):
        """When validating codename against matching project name, validation must pass."""
        validator = validator_class(complete_manifest_path)
        validator.validate_parsing()
        result = validator.validate_codename(COMPLETE_PROJECT_CODENAME)
        assert result[VALIDATION_RESULT_INDEX_TYPE] == VALIDATION_TYPE_CODENAME
        assert result[VALIDATION_RESULT_INDEX_STATUS] == VALIDATION_STATUS_SUCCESS
        assert result[VALIDATION_RESULT_INDEX_MESSAGE] is None

    def test_validate_codename_mismatches_project(self, complete_manifest_path, validator_class):
        """When validating codename against non-matching project name, validation must fail."""
        validator = validator_class(complete_manifest_path)
        validator.validate_parsing()
        result = validator.validate_codename(MINIMAL_PROJECT_CODENAME)
        assert result[VALIDATION_RESULT_INDEX_TYPE] == VALIDATION_TYPE_CODENAME
        assert result[VALIDATION_RESULT_INDEX_STATUS] == VALIDATION_STATUS_FAILURE
        assert result[VALIDATION_RESULT_INDEX_MESSAGE] is not None

    def test_validate_codename_before_parsing_fails(self, complete_manifest_path, validator_class):
        """When validating codename before parsing, validation must fail gracefully."""
        validator = validator_class(complete_manifest_path)
        result = validator.validate_codename(COMPLETE_PROJECT_CODENAME)
        assert result[VALIDATION_RESULT_INDEX_TYPE] == VALIDATION_TYPE_CODENAME
        assert result[VALIDATION_RESULT_INDEX_STATUS] == VALIDATION_STATUS_FAILURE
        assert result[VALIDATION_RESULT_INDEX_MESSAGE] is not None

    def test_validate_manifestfiles_returns_results_dict(self, complete_manifest_path, _validation_mod):
        """When validating list of manifest files, must return dictionary with results."""
        results = _validation_mod.validate_manifestfiles([complete_manifest_path])
        assert isinstance(results, dict)
        assert complete_manifest_path in results
        assert isinstance(results[complete_manifest_path], list)
        assert len(results[complete_manifest_path]) > EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED

    @pytest.mark.parametrize(PARAM_MANIFEST_PATH, [
        pytest.param(COMPLETE_MANIFEST_XML, id=PARAM_ID_COMPLETE_MANIFEST),
        pytest.param(MINIMAL_MANIFEST_XML, id=PARAM_ID_MINIMAL_MANIFEST),
    ])
    def test_valid_manifest_parses_successfully(self, manifest_path, validator_class):
        """When validating a valid manifest, parsing validation must pass without errors."""
        validator = validator_class(manifest_path)
        result = validator.validate_parsing()
        assert result[VALIDATION_RESULT_INDEX_TYPE] == VALIDATION_TYPE_PARSING
        assert result[VALIDATION_RESULT_INDEX_STATUS] == VALIDATION_STATUS_SUCCESS
        assert result[VALIDATION_RESULT_INDEX_MESSAGE] is None


CI_INDEX_MULTIPLE_PROJECTS_XML = os.path.join(FIXTURES_DIR, 'ci_index_multiple_projects.xml')
CI_INDEX_EMPTY_XML = os.path.join(FIXTURES_DIR, 'ci_index_empty.xml')
CI_INDEX_SET_A_XML = os.path.join(FIXTURES_DIR, 'ci_index_set_a.xml')
CI_INDEX_SET_B_XML = os.path.join(FIXTURES_DIR, 'ci_index_set_b.xml')

CI_PROJECT_NAME_PROJECT1 = 'Project1'
CI_PROJECT_NAME_PROJECT2 = 'Project2'
CI_PROJECT_NAME_PROJECT3 = 'Project3'
CI_PROJECT_NAME_PROJECTA = 'ProjectA'
CI_PROJECT_NAME_PROJECTB = 'ProjectB'
CI_PROJECT_NAME_PROJECTC = 'ProjectC'
CI_PROJECT_NAME_PROJECTD = 'ProjectD'
CI_PROJECT_NAME_NONEXISTENT = 'NonExistentProject'

CI_XML_PATH_PROJECT1 = 'manifests/project1.xml'
CI_XML_PATH_PROJECT2 = 'manifests/project2.xml'
CI_XML_PATH_PROJECT3 = 'manifests/project3.xml'

PARAM_CI_PROJECT_MANIFEST_PATH = 'project,expected_path'

EXPECTED_MULTIPLE_PROJECTS_ACTIVE_COUNT = 2
EXPECTED_MULTIPLE_PROJECTS_ARCHIVED_COUNT = 1
EXPECTED_EMPTY_PROJECT_COUNT = 0
EXPECTED_SET_A_PROJECT_COUNT = 2
EXPECTED_SET_B_ACTIVE_COUNT = 1
EXPECTED_SET_B_ARCHIVED_COUNT = 1
EXPECTED_MERGED_ACTIVE_COUNT = 3
EXPECTED_MERGED_ARCHIVED_COUNT = 1
EXPECTED_MERGED_TOTAL_COUNT = 4


class BaseTestCiIndexIntegrationFlow:

    manifest_module: str = None

    @pytest.fixture
    def ci_index_multiple_projects(self):
        """Return a CiIndexXml instance loaded from ci_index_multiple_projects.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.CiIndexXml(CI_INDEX_MULTIPLE_PROJECTS_XML)

    @pytest.fixture
    def ci_index_empty(self):
        """Return a CiIndexXml instance loaded from ci_index_empty.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.CiIndexXml(CI_INDEX_EMPTY_XML)

    @pytest.fixture
    def ci_index_set_a(self):
        """Return a CiIndexXml instance loaded from ci_index_set_a.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.CiIndexXml(CI_INDEX_SET_A_XML)

    @pytest.fixture
    def ci_index_set_b(self):
        """Return a CiIndexXml instance loaded from ci_index_set_b.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.CiIndexXml(CI_INDEX_SET_B_XML)

    def test_load_ci_index_with_multiple_projects(self, ci_index_multiple_projects):
        """When loading CI index with multiple projects, all projects must be indexed by name."""
        projects = ci_index_multiple_projects.project_list
        archived_projects = ci_index_multiple_projects.archived_project_list

        assert len(projects) == EXPECTED_MULTIPLE_PROJECTS_ACTIVE_COUNT

        assert len(archived_projects) == EXPECTED_MULTIPLE_PROJECTS_ARCHIVED_COUNT

        assert CI_PROJECT_NAME_PROJECT1 in projects
        assert CI_PROJECT_NAME_PROJECT2 in projects
        assert CI_PROJECT_NAME_PROJECT3 not in projects

        assert CI_PROJECT_NAME_PROJECT3 in archived_projects

    def test_ci_index_project_with_archived_manifest(self, ci_index_multiple_projects):
        """When loading CI index with archived projects, archived status must be correctly reflected."""
        projects = ci_index_multiple_projects.project_list
        archived_projects = ci_index_multiple_projects.archived_project_list

        assert CI_PROJECT_NAME_PROJECT3 not in projects

        assert CI_PROJECT_NAME_PROJECT3 in archived_projects

        manifest_path = ci_index_multiple_projects.get_project_xml(CI_PROJECT_NAME_PROJECT3)
        assert manifest_path == CI_XML_PATH_PROJECT3

    def test_ci_index_empty(self, ci_index_empty):
        """When loading empty CI index, no projects should be present."""
        projects = ci_index_empty.project_list
        archived_projects = ci_index_empty.archived_project_list

        assert len(projects) == EXPECTED_EMPTY_PROJECT_COUNT
        assert len(archived_projects) == EXPECTED_EMPTY_PROJECT_COUNT

    def test_ci_index_project_not_found(self, ci_index_multiple_projects):
        """When querying CI index for nonexistent project, ValueError must be raised."""
        with pytest.raises(ValueError) as exc_info:
            ci_index_multiple_projects.get_project_xml(CI_PROJECT_NAME_NONEXISTENT)

        assert CI_PROJECT_NAME_NONEXISTENT in str(exc_info.value)

    def test_multiple_ci_indexes_merge(self, ci_index_set_a, ci_index_set_b):
        """When loading multiple CI indexes, projects from all indexes must be accessible."""
        projects_a = ci_index_set_a.project_list
        assert len(projects_a) == EXPECTED_SET_A_PROJECT_COUNT
        assert CI_PROJECT_NAME_PROJECTA in projects_a
        assert CI_PROJECT_NAME_PROJECTB in projects_a

        projects_b = ci_index_set_b.project_list
        archived_b = ci_index_set_b.archived_project_list
        assert len(projects_b) == EXPECTED_SET_B_ACTIVE_COUNT
        assert len(archived_b) == EXPECTED_SET_B_ARCHIVED_COUNT
        assert CI_PROJECT_NAME_PROJECTC in projects_b
        assert CI_PROJECT_NAME_PROJECTD in archived_b

        all_active_projects = set(projects_a + projects_b)
        all_archived_projects = set(archived_b)

        assert len(all_active_projects) == EXPECTED_MERGED_ACTIVE_COUNT
        assert len(all_archived_projects) == EXPECTED_MERGED_ARCHIVED_COUNT
        assert len(all_active_projects) + len(all_archived_projects) == EXPECTED_MERGED_TOTAL_COUNT

    @pytest.mark.parametrize(PARAM_CI_PROJECT_MANIFEST_PATH, [
        pytest.param(CI_PROJECT_NAME_PROJECT1, CI_XML_PATH_PROJECT1, id=CI_PROJECT_NAME_PROJECT1),
        pytest.param(CI_PROJECT_NAME_PROJECT2, CI_XML_PATH_PROJECT2, id=CI_PROJECT_NAME_PROJECT2),
        pytest.param(CI_PROJECT_NAME_PROJECT3, CI_XML_PATH_PROJECT3, id=CI_PROJECT_NAME_PROJECT3),
    ])
    def test_resolve_project_manifest_from_ci_index(self, ci_index_multiple_projects, project, expected_path):
        """When resolving a project from CI index, the correct manifest path must be returned."""
        manifest_path = ci_index_multiple_projects.get_project_xml(project)
        assert manifest_path == expected_path


NO_SUBMODULES_MANIFEST_XML = os.path.join(FIXTURES_DIR, 'no_submodules_manifest.xml')
SUBMODULE_PATH_CORE = 'submodules/core'
SUBMODULE_PATH_UTILS = 'submodules/utils'
SUBMODULE_PATH_PLATFORM = 'submodules/platform'
SUBMODULE_PATH_SHARED = 'submodules/shared'
SUBMODULE_REMOTE_ORIGIN = 'origin'
SUBMODULE_COMBO_MAIN = 'main'
SUBMODULE_RECURSIVE_TRUE = True
SUBMODULE_RECURSIVE_FALSE = False
SUBMODULE_ORIGINAL_URL = 'https://github.com/original/repo.git'
SUBMODULE_ALTERNATE_URL = 'https://mirror.example.com/repo.git'
EXPECTED_SUBMODULE_COUNT_FOR_ORIGIN = 3
EXPECTED_SUBMODULE_COUNT_FOR_MAIN_COMBO = 3
EXPECTED_SUBMODULE_COUNT_FOR_ORIGIN_MAIN = 3
EXPECTED_SUBMODULE_COUNT_NO_SUBMODULES = 0
EXPECTED_ALTERNATE_REMOTE_COUNT = 1
EXPECTED_SUBMODULE_COUNT_ALL_COMBOS = 4

PARAM_SUBMODULE_PATH_RECURSIVE = 'path,expected_recursive'


class BaseTestSubmoduleFlow(_ManifestFixtureMixin):

    @pytest.fixture
    def no_submodules_manifest(self):
        """Return a ManifestXml instance loaded from no_submodules_manifest.xml."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.ManifestXml(NO_SUBMODULES_MANIFEST_XML)

    def test_get_submodule_init_paths_for_combo(self, complete_manifest):
        """When requesting submodule paths for specific combo, only matching paths must be returned."""
        submodules = complete_manifest.get_submodule_init_paths(combo=SUBMODULE_COMBO_MAIN)

        assert len(submodules) == EXPECTED_SUBMODULE_COUNT_FOR_MAIN_COMBO

        paths = [sub.path for sub in submodules]
        assert SUBMODULE_PATH_CORE in paths
        assert SUBMODULE_PATH_UTILS in paths
        assert SUBMODULE_PATH_SHARED in paths

    def test_filter_submodules_by_remote(self, complete_manifest):
        """When filtering submodules by remote name, only matching entries must be returned."""
        submodules = complete_manifest.get_submodule_init_paths(remote_name=SUBMODULE_REMOTE_ORIGIN)

        assert len(submodules) == EXPECTED_SUBMODULE_COUNT_FOR_ORIGIN

        for sub in submodules:
            assert sub.remote_name == SUBMODULE_REMOTE_ORIGIN

        paths = [sub.path for sub in submodules]
        assert SUBMODULE_PATH_CORE in paths
        assert SUBMODULE_PATH_UTILS in paths
        assert SUBMODULE_PATH_SHARED in paths

    def test_filter_submodules_by_remote_and_combo(self, complete_manifest):
        """When filtering by both remote and combo, only matching entries must be returned."""
        submodules = complete_manifest.get_submodule_init_paths(
            remote_name=SUBMODULE_REMOTE_ORIGIN,
            combo=SUBMODULE_COMBO_MAIN
        )

        assert len(submodules) == EXPECTED_SUBMODULE_COUNT_FOR_ORIGIN_MAIN

        for sub in submodules:
            assert sub.remote_name == SUBMODULE_REMOTE_ORIGIN
            assert sub.combo == SUBMODULE_COMBO_MAIN or sub.combo is None

    def test_get_submodule_alternate_remotes(self, complete_manifest):
        """When retrieving alternate remotes, must return configured alternates."""
        alternates = complete_manifest.submodule_alternate_remotes

        assert len(alternates) == EXPECTED_ALTERNATE_REMOTE_COUNT

        first_alternate = alternates[EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert first_alternate.remote_name == SUBMODULE_REMOTE_ORIGIN
        assert first_alternate.original_url == SUBMODULE_ORIGINAL_URL
        assert first_alternate.alternate_url == SUBMODULE_ALTERNATE_URL

        origin_alternates = complete_manifest.get_submodule_alternates_for_remote(SUBMODULE_REMOTE_ORIGIN)
        assert len(origin_alternates) == EXPECTED_ALTERNATE_REMOTE_COUNT

    def test_no_submodules_configured(self, no_submodules_manifest):
        """When manifest has no submodules, must return empty list gracefully."""
        submodules = no_submodules_manifest.get_submodule_init_paths()

        assert len(submodules) == EXPECTED_SUBMODULE_COUNT_NO_SUBMODULES
        assert isinstance(submodules, list)

        alternates = no_submodules_manifest.submodule_alternate_remotes
        assert len(alternates) == EXPECTED_SUBMODULE_COUNT_NO_SUBMODULES

    def test_submodule_init_paths_all_combos(self, complete_manifest):
        """When retrieving all submodule paths, must return union of all paths."""
        all_submodules = complete_manifest.get_submodule_init_paths()

        assert len(all_submodules) == EXPECTED_SUBMODULE_COUNT_ALL_COMBOS

        paths = [sub.path for sub in all_submodules]
        assert SUBMODULE_PATH_CORE in paths
        assert SUBMODULE_PATH_UTILS in paths
        assert SUBMODULE_PATH_PLATFORM in paths
        assert SUBMODULE_PATH_SHARED in paths

    @pytest.mark.parametrize(PARAM_SUBMODULE_PATH_RECURSIVE, [
        pytest.param(SUBMODULE_PATH_CORE, SUBMODULE_RECURSIVE_TRUE, id=SUBMODULE_PATH_CORE),
        pytest.param(SUBMODULE_PATH_UTILS, SUBMODULE_RECURSIVE_FALSE, id=SUBMODULE_PATH_UTILS),
    ])
    def test_submodule_has_recursive_config(self, complete_manifest, path, expected_recursive):
        """When accessing the recursive flag of a submodule, it must match the value configured in the manifest."""
        submodules = complete_manifest.get_submodule_init_paths(combo=SUBMODULE_COMBO_MAIN)
        submodule = [sub for sub in submodules if sub.path == path][EXPECTED_ARCHIVED_COMBO_COUNT_WITHOUT_ARCHIVED]
        assert submodule.recursive == expected_recursive


PIN_DESCRIPTION_TEST = 'Test pin file generated for integration testing'
PIN_COMBO_MAIN = 'main'
PIN_COMBO_DEV = 'dev'
PIN_FILENAME_XML = 'test_pin.xml'
PIN_FILENAME_JSON = 'test_pin.json'
PIN_COMMIT_SHA_1 = 'abc123def456789012345678901234567890abcd'
PIN_COMMIT_SHA_2 = 'def456abc789012345678901234567890123cdef'
PIN_REMOTE_ORIGIN = 'origin'
PIN_REMOTE_UPSTREAM = 'upstream'
PIN_EXPECTED_SOURCE_COUNT_MAIN = 2
PIN_EXPECTED_SOURCE_COUNT_DEV = 2
PIN_EXPECTED_REMOTE_COUNT_MAIN = 2
PIN_TAG_PIN = 'Pin'
PIN_TAG_COMBINATION = 'Combination'
PIN_TAG_SOURCE = 'Source'
PIN_TAG_REMOTE = 'Remote'
PIN_TAG_PROJECT_INFO = 'ProjectInfo'
PIN_ATTRIB_COMMIT = 'commit'
PIN_ATTRIB_NAME = 'name'
EXPECTED_MIN_JSON_KEYS = 1
PIN_TAG_CODENAME = 'CodeName'
PIN_TAG_DESCRIPTION = 'Description'
PIN_TAG_REMOTELIST = 'RemoteList'
PIN_TAG_PATCHSETS = 'PatchSets'
PIN_COMMIT_SHA_LENGTH = 40
PIN_HEX_CHARS = '0123456789abcdefABCDEF'
PIN_MIN_COMMIT_LENGTH = 0
FILE_MODE_READ = 'r'


class BaseTestPinGenerationFlow(_ManifestFixtureMixin):

    @pytest.fixture
    def pin_repo_sources(self, complete_manifest):
        """Return a list of RepoSource tuples with commit SHAs for pin generation."""
        sources = complete_manifest.get_repo_sources(PIN_COMBO_MAIN)
        pin_sources = []
        commit_shas = [PIN_COMMIT_SHA_1, PIN_COMMIT_SHA_2]
        for idx, src in enumerate(sources):
            pin_src = src._replace(commit=commit_shas[idx % len(commit_shas)])
            pin_sources.append(pin_src)
        return pin_sources

    def test_generate_pin_xml_from_manifest(self, complete_manifest, pin_repo_sources, tmp_path):
        """When generating pin XML from manifest, pin file must be created with correct structure."""
        pin_file = tmp_path / PIN_FILENAME_XML

        complete_manifest.generate_pin_xml(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_MAIN,
            pin_repo_sources,
            filename=str(pin_file)
        )

        assert pin_file.exists()

        tree = ET.parse(str(pin_file))
        root = tree.getroot()

        assert root.tag == PIN_TAG_PIN

        project_info = root.find(PIN_TAG_PROJECT_INFO)
        assert project_info is not None

        combination = root.find(PIN_TAG_COMBINATION)
        assert combination is not None
        sources = list(combination.findall(PIN_TAG_SOURCE))
        assert len(sources) == PIN_EXPECTED_SOURCE_COUNT_MAIN

    def test_generate_pin_json_from_manifest(self, complete_manifest, pin_repo_sources, tmp_path):
        """When generating pin JSON from manifest, JSON file must be created with same data as XML pin."""
        pin_file = tmp_path / PIN_FILENAME_JSON

        complete_manifest.generate_pin_json(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_MAIN,
            pin_repo_sources,
            filename=str(pin_file)
        )

        assert pin_file.exists()

        with open(str(pin_file), FILE_MODE_READ) as f:
            pin_data = json.load(f)

        assert isinstance(pin_data, dict)
        assert len(pin_data) >= EXPECTED_MIN_JSON_KEYS
        assert PIN_ATTRIB_NAME in pin_data
        assert pin_data[PIN_ATTRIB_NAME] == PIN_TAG_PIN

    def test_pin_file_preserves_manifest_metadata(self, complete_manifest, pin_repo_sources, tmp_path):
        """When generating pin, manifest metadata (project info, remotes) must be preserved."""
        pin_file = tmp_path / PIN_FILENAME_XML

        complete_manifest.generate_pin_xml(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_MAIN,
            pin_repo_sources,
            filename=str(pin_file)
        )

        tree = ET.parse(str(pin_file))
        root = tree.getroot()

        project_info = root.find(PIN_TAG_PROJECT_INFO)
        assert project_info is not None
        codename = project_info.find(PIN_TAG_CODENAME)
        assert codename is not None
        assert codename.text == COMPLETE_PROJECT_CODENAME

        description = project_info.find(PIN_TAG_DESCRIPTION)
        assert description is not None
        assert description.text == PIN_DESCRIPTION_TEST

        remote_list = root.find(PIN_TAG_REMOTELIST)
        assert remote_list is not None
        remotes = list(remote_list.findall(PIN_TAG_REMOTE))
        assert len(remotes) == PIN_EXPECTED_REMOTE_COUNT_MAIN

        remote_names = [r.attrib[PIN_ATTRIB_NAME] for r in remotes]
        assert PIN_REMOTE_ORIGIN in remote_names
        assert PIN_REMOTE_UPSTREAM in remote_names

    def test_pin_file_replaces_branches_with_commits(self, complete_manifest, pin_repo_sources, tmp_path):
        """When generating pin, branch references must be replaced with commit SHAs."""
        pin_file = tmp_path / PIN_FILENAME_XML

        complete_manifest.generate_pin_xml(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_MAIN,
            pin_repo_sources,
            filename=str(pin_file)
        )

        tree = ET.parse(str(pin_file))
        root = tree.getroot()

        combination = root.find(PIN_TAG_COMBINATION)
        sources = list(combination.findall(PIN_TAG_SOURCE))

        for source in sources:
            assert PIN_ATTRIB_COMMIT in source.attrib
            assert len(source.attrib[PIN_ATTRIB_COMMIT]) > PIN_MIN_COMMIT_LENGTH

            commit_sha = source.attrib[PIN_ATTRIB_COMMIT]
            assert len(commit_sha) == PIN_COMMIT_SHA_LENGTH
            assert all(c in PIN_HEX_CHARS for c in commit_sha)

    def test_generate_pin_for_specific_combination(self, complete_manifest, tmp_path):
        """When generating pin for specific combination, pin must contain only repos for that combo."""
        pin_file = tmp_path / PIN_FILENAME_XML

        dev_sources = complete_manifest.get_repo_sources(PIN_COMBO_DEV)
        pin_sources = []
        for src in dev_sources:
            pin_src = src._replace(commit=PIN_COMMIT_SHA_1)
            pin_sources.append(pin_src)

        complete_manifest.generate_pin_xml(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_DEV,
            pin_sources,
            filename=str(pin_file)
        )

        tree = ET.parse(str(pin_file))
        root = tree.getroot()

        combination = root.find(PIN_TAG_COMBINATION)
        assert combination is not None
        assert combination.attrib[PIN_ATTRIB_NAME] == PIN_COMBO_DEV

        sources = list(combination.findall(PIN_TAG_SOURCE))
        assert len(sources) == PIN_EXPECTED_SOURCE_COUNT_DEV

    def test_pin_file_includes_patchsets(self, complete_manifest, pin_repo_sources, tmp_path):
        """When generating pin from manifest with patchsets, pin must include patchset information."""
        pin_file = tmp_path / PIN_FILENAME_XML

        complete_manifest.generate_pin_xml(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_MAIN,
            pin_repo_sources,
            filename=str(pin_file)
        )

        tree = ET.parse(str(pin_file))
        root = tree.getroot()

        patchsets = root.find(PIN_TAG_PATCHSETS)
        if patchsets is not None:
            assert patchsets.tag == PIN_TAG_PATCHSETS

    def test_load_and_validate_generated_pin(self, complete_manifest, pin_repo_sources, tmp_path):
        """When loading a generated pin file, it must be parseable and recognized as a pin."""
        pin_file = tmp_path / PIN_FILENAME_XML

        complete_manifest.generate_pin_xml(
            PIN_DESCRIPTION_TEST,
            PIN_COMBO_MAIN,
            pin_repo_sources,
            filename=str(pin_file)
        )

        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        pin_manifest = manifest_mod.ManifestXml(str(pin_file))

        assert pin_manifest.is_pin_file() is True

        project_info = pin_manifest.project_info
        assert project_info is not None
        assert project_info.codename == COMPLETE_PROJECT_CODENAME

        sources = pin_manifest.get_repo_sources(PIN_COMBO_MAIN)
        assert len(sources) == PIN_EXPECTED_SOURCE_COUNT_MAIN

        for source in sources:
            assert source.commit is not None
