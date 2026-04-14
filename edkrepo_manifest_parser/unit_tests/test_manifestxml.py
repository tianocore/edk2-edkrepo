#!/usr/bin/env python3
#
## @file
# test_manifestxml.py
#
# Copyright (c) 2025 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import (
    CiIndexXml,
    ManifestXml,
    _validate_repo_local_root_or_raise,
    PatchSet,
    INVALID_REPO_PATH_ERROR,
    NO_PARENT_REPO_ERROR,
    COMBO_INVALIDINPUT_ERROR,
    NO_PATCHSET_IN_COMBO,
    PATCHSET_UNKNOWN_ERROR,
    PATCHSET_PARENT_CIRCULAR_DEPENDENCY,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    MANIFEST_PATH,
    REMOTE_NAME,
    REMOTE_URL,
)

ATTRIB_NAME               = 'name'
ELEMENT_TAG_MANIFEST      = 'Manifest'
ELEMENT_TAG_PIN           = 'Pin'
PARAM_IS_PIN_FILE         = 'xml_type, expected'
ID_XML_TYPE_PIN           = 'xml_type_pin'
ID_XML_TYPE_MANIFEST      = 'xml_type_manifest'
PARAM_SUBMODULE_ALTS      = 'alt_remote, query_remote, expect_match'
ID_ALT_MATCHING           = 'matching_remote'
ID_ALT_NO_MATCH           = 'no_match'
PARAM_NESTED_REPO_RAISES  = 'sources, path, expected_error'
ID_NON_NESTED_PATH        = 'non_nested_path'
ID_NO_PARENT_FOUND        = 'no_parent_found'
PARAM_COMBO_ARG           = 'combo_arg'
ID_COMBO_NONE             = 'combo_none'
ID_COMBO_SPECIFIED        = 'combo_specified'
COMBO_NAME           = 'default'
CHILD_DEFAULT_COMBO  = 'main'
PIN_PREFIX_COMBO     = 'Pin:main'
UNKNOWN_COMBO        = 'unknown_combo'
UNKNOWN_REMOTE       = 'upstream'
PATCHSET_NAME        = 'ps_name'
UNKNOWN_PATCHSET     = 'unknown_ps'
PARENT_REPO          = 'parent'
NESTED_REPO          = 'parent/child'
INVALID_REPO_PATH    = 'singlecomponent'


class TestManifestXml:

    @pytest.fixture
    def mock_et(self):
        """Patch ET.ElementTree to prevent real file I/O; yields the mock class."""
        with patch('edkrepo_manifest_parser.edk_manifest.ET.ElementTree') as mock_et_cls:
            mock_tree = MagicMock()
            mock_et_cls.return_value = mock_tree
            mock_tree.getroot.return_value.tag = ELEMENT_TAG_MANIFEST
            mock_tree.iter.return_value = []
            yield mock_et_cls

    @pytest.fixture
    def manifest_instance(self, mock_et):
        """Return a ManifestXml with cleared internal collections ready for per-test configuration."""
        instance = ManifestXml(MANIFEST_PATH)
        instance._combo_sources = {}
        instance._combinations = {}
        instance._remotes = {}
        instance._patch_sets = {}
        instance._patch_set_operations = {}
        instance._submodule_init_list = []
        instance._submodule_alternate_remotes = []
        instance._xml_type = ELEMENT_TAG_MANIFEST
        return instance

    @staticmethod
    def _make_mock_source(patch_set=None, remote_name=None):
        """Build and return a mock RepoSource-like object with configurable patch_set and remote_name."""
        src = MagicMock()
        src.patch_set = patch_set
        src.remote_name = remote_name if remote_name is not None else REMOTE_NAME
        return src

    @staticmethod
    def _make_mock_submodule_entry(remote_name, combo=None):
        """Build and return a mock _SubmoduleInitEntry-like object with remote_name and combo."""
        entry = MagicMock()
        entry.remote_name = remote_name
        entry.combo = combo
        return entry

    @staticmethod
    def _make_patchset_tuple(name, remote, parent_sha='orphan', fetch_branch='main'):
        """Build and return a PatchSet namedtuple with the given fields."""
        return PatchSet(remote=remote, name=name, parent_sha=parent_sha, fetch_branch=fetch_branch)

    @staticmethod
    def _make_mock_remote(name=None, url=None):
        """Build and return a mock remote object; optionally set tuple.name and tuple.url."""
        remote = MagicMock()
        if name is not None:
            remote.tuple.name = name
        if url is not None:
            remote.tuple.url = url
        return remote

    @staticmethod
    def _make_mock_alt(remote_name):
        """Build and return a mock submodule alternate with the given remote_name."""
        alt = MagicMock()
        alt.remote_name = remote_name
        return alt

    @staticmethod
    def _make_combo_root(elements):
        """Build and return a mock combo root whose iter() yields the given elements."""
        combo_root = MagicMock()
        combo_root.iter.return_value = elements
        return combo_root

    @staticmethod
    def _setup_combo_with_patchset(manifest_instance):
        """Populate manifest_instance with one combo and one patchset; return the PatchSet tuple."""
        ps = TestManifestXml._make_patchset_tuple(
            PATCHSET_NAME, REMOTE_NAME
        )
        mock_src = TestManifestXml._make_mock_source(
            patch_set=PATCHSET_NAME,
            remote_name=REMOTE_NAME,
        )
        manifest_instance._combo_sources = {COMBO_NAME: [mock_src]}
        manifest_instance._patch_sets = {(PATCHSET_NAME, REMOTE_NAME): ps}
        return ps

    @staticmethod
    def _setup_patchset_with_ops(manifest_instance, operations):
        """Populate manifest_instance with one patchset and given operations; return the PatchSet tuple."""
        ps = TestManifestXml._make_patchset_tuple(
            PATCHSET_NAME, REMOTE_NAME
        )
        manifest_instance._patch_sets = {(PATCHSET_NAME, REMOTE_NAME): ps}
        manifest_instance._patch_set_operations = {
            (PATCHSET_NAME, REMOTE_NAME): operations
        }
        return ps

    def test_validate_repo_local_root_raises_for_single_component_path(self):
        """When repo_local_root has only one path component, must raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _validate_repo_local_root_or_raise(INVALID_REPO_PATH)
        assert str(exc_info.value) == INVALID_REPO_PATH_ERROR.format(INVALID_REPO_PATH)

    def test_validate_repo_local_root_does_not_raise_for_multi_component_path(self):
        """When repo_local_root has multiple path components, must not raise."""
        _validate_repo_local_root_or_raise(NESTED_REPO)

    @pytest.mark.parametrize(PARAM_IS_PIN_FILE, [
        pytest.param(ELEMENT_TAG_PIN,      True,  id=ID_XML_TYPE_PIN),
        pytest.param(ELEMENT_TAG_MANIFEST, False, id=ID_XML_TYPE_MANIFEST),
    ])
    def test_is_pin_file(self, manifest_instance, xml_type, expected):
        """When _xml_type is set to the given value, is_pin_file must return the expected boolean."""
        manifest_instance._xml_type = xml_type
        assert manifest_instance.is_pin_file() is expected

    def test_get_remote_returns_remote_object_when_found(self, manifest_instance):
        """When remote_name exists in _remotes, must return the corresponding remote object."""
        mock_remote = self._make_mock_remote()
        manifest_instance._remotes = {REMOTE_NAME: mock_remote}
        assert manifest_instance.get_remote(REMOTE_NAME) is mock_remote

    def test_get_remote_returns_none_when_not_found(self, manifest_instance):
        """When remote_name is not in _remotes, must return None."""
        assert manifest_instance.get_remote(UNKNOWN_REMOTE) is None

    def test_get_remotes_dict_returns_name_to_url_mapping(self, manifest_instance):
        """Must return a dict mapping each remote name to its URL."""
        mock_remote = self._make_mock_remote(name=REMOTE_NAME, url=REMOTE_URL)
        manifest_instance._remotes = {REMOTE_NAME: mock_remote}
        result = manifest_instance.get_remotes_dict()
        assert result == {REMOTE_NAME: REMOTE_URL}

    def test_get_repo_sources_returns_tuple_list_when_combo_found(self, manifest_instance):
        """When combo_name is in _combo_sources, must return tuples of that combo's sources."""
        mock_src = self._make_mock_source()
        manifest_instance._combo_sources = {COMBO_NAME: [mock_src]}
        result = manifest_instance.get_repo_sources(COMBO_NAME)
        assert result == [mock_src.tuple]

    def test_get_repo_sources_returns_default_combo_sources_for_pin_prefix(self, manifest_instance):
        """When combo_name starts with 'Pin:', must return sources of the default combo."""
        mock_src = self._make_mock_source()
        manifest_instance._combo_sources = {CHILD_DEFAULT_COMBO: [mock_src]}
        manifest_instance._general_config = MagicMock()
        manifest_instance._general_config.tuple.default_combo = CHILD_DEFAULT_COMBO
        result = manifest_instance.get_repo_sources(PIN_PREFIX_COMBO)
        assert result == [mock_src.tuple]

    def test_get_repo_sources_raises_value_error_when_combo_not_found(self, manifest_instance):
        """When combo_name is not in _combo_sources and not a Pin prefix, must raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_repo_sources(UNKNOWN_COMBO)
        assert str(exc_info.value) == COMBO_INVALIDINPUT_ERROR.format(UNKNOWN_COMBO)

    @pytest.mark.parametrize(PARAM_NESTED_REPO_RAISES, [
        pytest.param([], INVALID_REPO_PATH, INVALID_REPO_PATH_ERROR.format(INVALID_REPO_PATH), id=ID_NON_NESTED_PATH),
        pytest.param([], NESTED_REPO,       NO_PARENT_REPO_ERROR.format(NESTED_REPO),          id=ID_NO_PARENT_FOUND),
    ])
    def test_get_parent_of_nested_repo_raises(self, manifest_instance, sources, path, expected_error):
        """When path is non-nested or no parent source is found, must raise ValueError with the expected message."""
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_parent_of_nested_repo(sources, path)
        assert str(exc_info.value) == expected_error

    def test_get_parent_of_nested_repo_returns_direct_parent(self, manifest_instance):
        """When a source matches the direct parent directory, must return that source."""
        mock_src = MagicMock()
        mock_src.root = PARENT_REPO
        result = manifest_instance.get_parent_of_nested_repo([mock_src], NESTED_REPO)
        assert result is mock_src

    def test_get_combo_element_returns_deepcopy_when_found(self, manifest_instance, mock_et):
        """When a Combination with the given name exists in the tree, must return a deepcopy."""
        mock_elem = MagicMock()
        mock_elem.attrib = {ATTRIB_NAME: COMBO_NAME}
        mock_et.return_value.find.return_value = self._make_combo_root([mock_elem])
        with patch('edkrepo_manifest_parser.edk_manifest.copy.deepcopy', return_value=mock_elem):
            result = manifest_instance.get_combo_element(COMBO_NAME)
        assert result is mock_elem

    def test_get_combo_element_raises_value_error_when_not_found(self, manifest_instance, mock_et):
        """When no Combination with the given name exists in the tree, must raise ValueError."""
        mock_et.return_value.find.return_value = self._make_combo_root([])
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_combo_element(UNKNOWN_COMBO)
        assert UNKNOWN_COMBO in str(exc_info.value)

    @pytest.mark.parametrize(PARAM_SUBMODULE_ALTS, [
        pytest.param(REMOTE_NAME,    REMOTE_NAME, True,  id=ID_ALT_MATCHING),
        pytest.param(UNKNOWN_REMOTE, REMOTE_NAME, False, id=ID_ALT_NO_MATCH),
    ])
    def test_get_submodule_alternates_for_remote(self, manifest_instance, alt_remote, query_remote, expect_match):
        """When an alternate's remote_name matches the query, its tuple is returned; otherwise an empty list."""
        mock_alt = self._make_mock_alt(alt_remote)
        manifest_instance._submodule_alternate_remotes = [mock_alt]
        result = manifest_instance.get_submodule_alternates_for_remote(query_remote)
        assert result == ([mock_alt.tuple] if expect_match else [])

    def test_get_submodule_init_paths_returns_all_when_no_filters(self, manifest_instance):
        """When both remote_name and combo are None, must return tuples for all submodule entries."""
        e1 = self._make_mock_submodule_entry(REMOTE_NAME)
        manifest_instance._submodule_init_list = [e1]
        result = manifest_instance.get_submodule_init_paths()
        assert result == [e1.tuple]

    def test_get_submodule_init_paths_filters_by_remote_name(self, manifest_instance):
        """When only remote_name is given, must return tuples only for entries matching that remote."""
        e1 = self._make_mock_submodule_entry(REMOTE_NAME)
        e2 = self._make_mock_submodule_entry(UNKNOWN_REMOTE)
        manifest_instance._submodule_init_list = [e1, e2]
        result = manifest_instance.get_submodule_init_paths(remote_name=REMOTE_NAME)
        assert result == [e1.tuple]

    def test_get_submodule_init_paths_filters_by_combo(self, manifest_instance):
        """When only combo is given, must return tuples for entries matching that combo or with no combo."""
        e_match = self._make_mock_submodule_entry(REMOTE_NAME, combo=COMBO_NAME)
        e_no_combo = self._make_mock_submodule_entry(REMOTE_NAME, combo=None)
        e_other = self._make_mock_submodule_entry(REMOTE_NAME, combo=UNKNOWN_COMBO)
        manifest_instance._submodule_init_list = [e_match, e_no_combo, e_other]
        result = manifest_instance.get_submodule_init_paths(combo=COMBO_NAME)
        assert e_match.tuple in result
        assert e_no_combo.tuple in result
        assert e_other.tuple not in result

    def test_get_submodule_init_paths_filters_by_remote_and_combo(self, manifest_instance):
        """When both remote_name and combo are given, must return entries matching both filters."""
        e_match = self._make_mock_submodule_entry(REMOTE_NAME, combo=COMBO_NAME)
        e_wrong_remote = self._make_mock_submodule_entry(UNKNOWN_REMOTE, combo=COMBO_NAME)
        manifest_instance._submodule_init_list = [e_match, e_wrong_remote]
        result = manifest_instance.get_submodule_init_paths(
            remote_name=REMOTE_NAME, combo=COMBO_NAME
        )
        assert result == [e_match.tuple]

    def test_get_patchset_returns_patchset_when_found(self, manifest_instance):
        """When (name, remote) exists in _patch_sets, must return the corresponding PatchSet."""
        ps = self._make_patchset_tuple(PATCHSET_NAME, REMOTE_NAME)
        manifest_instance._patch_sets = {(PATCHSET_NAME, REMOTE_NAME): ps}
        result = manifest_instance.get_patchset(PATCHSET_NAME, REMOTE_NAME)
        assert result == ps

    def test_get_patchset_raises_key_error_when_not_found(self, manifest_instance):
        """When (name, remote) does not exist in _patch_sets, must raise KeyError."""
        with pytest.raises(KeyError) as exc_info:
            manifest_instance.get_patchset(UNKNOWN_PATCHSET, REMOTE_NAME)
        assert UNKNOWN_PATCHSET in str(exc_info.value)

    @pytest.mark.parametrize(PARAM_COMBO_ARG, [
        pytest.param(None,       id=ID_COMBO_NONE),
        pytest.param(COMBO_NAME, id=ID_COMBO_SPECIFIED),
    ])
    def test_get_patchsets_for_combo_returns_patchset(self, manifest_instance, combo_arg):
        """When combo is None or a valid name, get_patchsets_for_combo must return the patchset for that combo."""
        ps = self._setup_combo_with_patchset(manifest_instance)
        result = manifest_instance.get_patchsets_for_combo(combo=combo_arg)
        assert result[COMBO_NAME] == ps

    def test_get_patchsets_for_combo_raises_key_error_when_no_patchsets_in_combo(self, manifest_instance):
        """When the specified combo has no sources with a patchset, must raise KeyError."""
        mock_src = self._make_mock_source(patch_set=None)
        manifest_instance._combo_sources = {COMBO_NAME: [mock_src]}
        with pytest.raises(KeyError) as exc_info:
            manifest_instance.get_patchsets_for_combo(combo=COMBO_NAME)
        assert NO_PATCHSET_IN_COMBO.format(COMBO_NAME) in str(exc_info.value)

    def test_get_patchset_operations_returns_list_when_patchset_found(self, manifest_instance):
        """When (name, remote) is in _patch_sets and there is no circular parent, must return a list containing the operations."""
        mock_ops = [MagicMock()]
        self._setup_patchset_with_ops(manifest_instance, mock_ops)
        result = manifest_instance.get_patchset_operations(PATCHSET_NAME, REMOTE_NAME)
        assert mock_ops in result

    def test_get_patchset_operations_raises_on_circular_dependency(self, manifest_instance):
        """When get_parent_patchset_operations raises RecursionError, must raise ValueError."""
        self._setup_patchset_with_ops(manifest_instance, [])
        manifest_instance.get_parent_patchset_operations = MagicMock(side_effect=RecursionError)
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_patchset_operations(PATCHSET_NAME, REMOTE_NAME)
        assert str(exc_info.value) == PATCHSET_PARENT_CIRCULAR_DEPENDENCY

    def test_get_patchset_operations_raises_value_error_when_not_found(self, manifest_instance):
        """When (name, remote) is not in _patch_sets, must raise ValueError with the patchset name."""
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_patchset_operations(UNKNOWN_PATCHSET, REMOTE_NAME)
        assert str(exc_info.value) == PATCHSET_UNKNOWN_ERROR.format(UNKNOWN_PATCHSET, MANIFEST_PATH)


class TestCiIndexXml:

    def test_project_lists_filter_archived_projects(self, tmp_path):
        """Must return active and archived project names in the expected lists."""
        xml_path = tmp_path / 'CiIndex.xml'
        xml_path.write_text(
            """<ProjectList>
  <Project name="ActiveProject" xmlPath="active.xml" />
  <Project name="ArchivedProject" xmlPath="archived.xml" archived="true" />
  <Project name="ImplicitActiveProject" xmlPath="implicit.xml" />
</ProjectList>
""",
            encoding='utf-8'
        )

        ci_index = CiIndexXml(str(xml_path))

        assert ci_index.project_list == ['ActiveProject', 'ImplicitActiveProject']
        assert ci_index.archived_project_list == ['ArchivedProject']
