#!/usr/bin/env python3
#
## @file
# test_repo_source.py
#
# Copyright (c) 2025 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from edk_manifest import ATTRIBUTE_MISSING_ERROR
from edk_manifest import RepoSource
from edk_manifest import _RepoSource

from edkrepo_manifest_parser.edk_manifest import ATTRIBUTE_MISSING_ERROR
from edkrepo_manifest_parser.edk_manifest import INVALID_COMBO_DEFINITION_ERROR
from edkrepo_manifest_parser.edk_manifest import REQUIRED_ATTRIB_ERROR_MSG
from edkrepo_manifest_parser.edk_manifest import RepoSource
from edkrepo_manifest_parser.edk_manifest import _parse_repo_source_required_attribs
from edkrepo_manifest_parser.edk_manifest import _RepoSource
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    REMOTE_NAME,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import REMOTE_URL
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    REQUIRED_ATTRIB_SPLIT_CHAR,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_remotes,
)

# XML attribute names
ATTRIB_LOCAL_ROOT        = 'localRoot'
ATTRIB_REMOTE            = 'remote'
ATTRIB_BRANCH            = 'branch'
ATTRIB_COMMIT            = 'commit'
ATTRIB_TAG               = 'tag'
ATTRIB_PATCH_SET         = 'patchSet'
ATTRIB_SPARSE            = 'sparseCheckout'
ATTRIB_ENABLE_SUB        = 'enableSubmodule'
ATTRIB_ENABLE_SUB_LEGACY = 'enable_submodule'
ATTRIB_VENV_CFG          = 'venv_cfg'
ATTRIB_BLOBLESS          = 'blobless'
ATTRIB_TREELESS          = 'treeless'
ATTRIB_BOOL_TRUE         = 'true'
ATTRIB_BOOL_FALSE        = 'false'

# Element tag
ELEMENT_TAG_SOURCE       = 'Source'

# Test data values
LOCAL_ROOT               = 'MyRepo'
NESTED_LOCAL_ROOT        = 'parent/MyRepo'
BRANCH                   = 'main'
COMMIT                   = 'abc123'
TAG                      = 'v1.0.0'
PATCH_SET                = 'ps-debug'
VENV_CFG                 = 'venv.cfg'
FIELD_SPARSE             = 'sparse'
FIELD_ENABLE_SUB         = 'enableSub'
FIELD_NESTED_REPO        = 'nested_repo'
FIELD_COMMIT             = 'commit'
FIELD_TAG                = 'tag'
FIELD_PATCH_SET          = 'patch_set'
FIELD_VENV_CFG           = 'venv_cfg'
FIELD_BLOBLESS           = 'blobless'
FIELD_TREELESS           = 'treeless'
PARAM_BOOL_FIELD         = 'extra, field_name, expected'
PARAM_PATCH_SET_COMBO    = 'ref_attrib_key, ref_attrib_val'
PARAM_OPTIONAL_REF       = 'attrib_key, attrib_val, field_name, expected'
PARAM_PARSE_RAISES       = 'attrib, remotes'
PARAM_ABSENT_REF         = 'field_name'
ID_SPARSE_MISSING        = 'sparse_missing'
ID_SPARSE_TRUE           = 'sparse_true'
ID_SPARSE_FALSE          = 'sparse_false'
ID_ENABLE_SUB_MISSING    = 'enable_sub_missing'
ID_ENABLE_SUB_TRUE       = 'enable_sub_true'
ID_ENABLE_SUB_FALSE      = 'enable_sub_false'
ID_BLOBLESS_MISSING      = 'blobless_missing'
ID_BLOBLESS_TRUE         = 'blobless_true'
ID_BLOBLESS_FALSE        = 'blobless_false'
ID_TREELESS_MISSING      = 'treeless_missing'
ID_TREELESS_TRUE         = 'treeless_true'
ID_TREELESS_FALSE        = 'treeless_false'
ID_NESTED_REPO_TRUE      = 'nested_repo_true'
ID_NESTED_REPO_FALSE     = 'nested_repo_false'
ID_PATCH_SET_WITH_BRANCH = 'patch_set_with_branch'
ID_PATCH_SET_WITH_COMMIT = 'patch_set_with_commit'
ID_PATCH_SET_WITH_TAG    = 'patch_set_with_tag'
ID_COMMIT_PRESENT        = 'commit_present'
ID_TAG_PRESENT           = 'tag_present'
ID_COMMIT_ABSENT         = 'commit_absent'
ID_TAG_ABSENT            = 'tag_absent'
ID_PATCH_SET_ABSENT      = 'patch_set_absent'
ID_LOCAL_ROOT_MISSING        = 'local_root_missing'
ID_REMOTE_ATTRIB_MISSING     = 'remote_attrib_missing'
ID_REMOTE_NOT_IN_REMOTES     = 'remote_not_in_remotes'
ID_ENABLE_SUB_LEGACY_COMPAT  = 'enable_sub_legacy_compat'
ID_VENV_CFG_PRESENT          = 'venv_cfg_present'
ID_VENV_CFG_ABSENT           = 'venv_cfg_absent'


class TestRepoSource:

    @staticmethod
    def _make_single_ref_element(ref_key, ref_val):
        """Build a mock element with only the required fields (localRoot, remote) and one ref attribute."""
        return make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ref_key: ref_val,
        }, tag=ELEMENT_TAG_SOURCE)

    @pytest.fixture
    def base_attrib(self):
        """Return minimum valid attributes dict (mutable - tests can modify as needed)."""
        return {
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_BRANCH: BRANCH,
        }

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry."""
        return make_mock_remotes()

    @pytest.fixture
    def base_source(self, base_attrib, default_remotes):
        """Return a _RepoSource built from minimum valid attributes."""
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        return _RepoSource(element, default_remotes)

    def test_parse_required_attribs_returns_all_three_when_all_present(self, default_remotes):
        """When all required attributes and the remote key are present, must return (root, remote_name, remote_url)."""
        element = make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
        }, tag=ELEMENT_TAG_SOURCE)

        root, remote_name, remote_url = _parse_repo_source_required_attribs(element, default_remotes)

        assert root == LOCAL_ROOT
        assert remote_name == REMOTE_NAME
        assert remote_url == REMOTE_URL

    @pytest.mark.parametrize(PARAM_PARSE_RAISES, [
        pytest.param(
            {ATTRIB_REMOTE: REMOTE_NAME},
            make_mock_remotes(),
            id=ID_LOCAL_ROOT_MISSING,
        ),
        pytest.param(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT},
            make_mock_remotes(),
            id=ID_REMOTE_ATTRIB_MISSING,
        ),
        pytest.param(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT, ATTRIB_REMOTE: REMOTE_NAME},
            {},
            id=ID_REMOTE_NOT_IN_REMOTES,
        ),
    ])
    def test_parse_required_attribs_raises_key_error(self, attrib, remotes):
        """When any required attribute or remote lookup is missing, must raise KeyError with the required-attrib message."""
        element = make_mock_element(attrib, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(KeyError) as exc_info:
            _parse_repo_source_required_attribs(element, remotes)

        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_all_required_fields(self, base_source):
        """When all required attributes are present, __init__ must set root, remote_name, and remote_url correctly."""
        assert base_source.root == LOCAL_ROOT
        assert base_source.remote_name == REMOTE_NAME
        assert base_source.remote_url == REMOTE_URL

    def test_init_sets_branch_when_present(self, base_source):
        """When the branch attribute is present, __init__ must set self.branch to its value."""
        assert base_source.branch == BRANCH

    def test_init_sets_branch_to_none_when_absent(self):
        """When the branch attribute is absent, __init__ must set self.branch to None."""
        element = self._make_single_ref_element(ATTRIB_COMMIT, COMMIT)
        assert _RepoSource(element, make_mock_remotes()).branch is None

    @pytest.mark.parametrize(PARAM_OPTIONAL_REF, [
        pytest.param(ATTRIB_COMMIT,            COMMIT,           FIELD_COMMIT,     COMMIT,   id=ID_COMMIT_PRESENT),
        pytest.param(ATTRIB_TAG,               TAG,              FIELD_TAG,        TAG,      id=ID_TAG_PRESENT),
        pytest.param(ATTRIB_ENABLE_SUB_LEGACY, ATTRIB_BOOL_TRUE, FIELD_ENABLE_SUB, True,     id=ID_ENABLE_SUB_LEGACY_COMPAT),
        pytest.param(ATTRIB_VENV_CFG,          VENV_CFG,         FIELD_VENV_CFG,   VENV_CFG, id=ID_VENV_CFG_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, base_attrib, default_remotes, attrib_key, attrib_val, field_name, expected):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        base_attrib[attrib_key] = attrib_val
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = _RepoSource(element, default_remotes)
        assert getattr(rs, field_name) == expected

    @pytest.mark.parametrize(PARAM_ABSENT_REF, [
        pytest.param(FIELD_COMMIT,    id=ID_COMMIT_ABSENT),
        pytest.param(FIELD_TAG,       id=ID_TAG_ABSENT),
        pytest.param(FIELD_PATCH_SET, id=ID_PATCH_SET_ABSENT),
        pytest.param(FIELD_VENV_CFG,  id=ID_VENV_CFG_ABSENT),
    ])
    def test_init_sets_optional_field_to_none_when_absent(self, base_source, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        assert getattr(base_source, field_name) is None

    def test_init_sets_patch_set_when_present(self):
        """When the patchSet attribute is present and no other ref is given, __init__ must set self.patch_set to its value."""
        element = self._make_single_ref_element(ATTRIB_PATCH_SET, PATCH_SET)
        assert _RepoSource(element, make_mock_remotes()).patch_set == PATCH_SET

    @pytest.mark.parametrize(PARAM_BOOL_FIELD, [
        pytest.param({},                                      FIELD_SPARSE,      False, id=ID_SPARSE_MISSING),
        pytest.param({ATTRIB_SPARSE:      ATTRIB_BOOL_TRUE},  FIELD_SPARSE,      True,  id=ID_SPARSE_TRUE),
        pytest.param({ATTRIB_SPARSE:      ATTRIB_BOOL_FALSE}, FIELD_SPARSE,      False, id=ID_SPARSE_FALSE),
        pytest.param({},                                      FIELD_ENABLE_SUB,  False, id=ID_ENABLE_SUB_MISSING),
        pytest.param({ATTRIB_ENABLE_SUB:  ATTRIB_BOOL_TRUE},  FIELD_ENABLE_SUB,  True,  id=ID_ENABLE_SUB_TRUE),
        pytest.param({ATTRIB_ENABLE_SUB:  ATTRIB_BOOL_FALSE}, FIELD_ENABLE_SUB,  False, id=ID_ENABLE_SUB_FALSE),
        pytest.param({},                                      FIELD_BLOBLESS,    False, id=ID_BLOBLESS_MISSING),
        pytest.param({ATTRIB_BLOBLESS:    ATTRIB_BOOL_TRUE},  FIELD_BLOBLESS,    True,  id=ID_BLOBLESS_TRUE),
        pytest.param({ATTRIB_BLOBLESS:    ATTRIB_BOOL_FALSE}, FIELD_BLOBLESS,    False, id=ID_BLOBLESS_FALSE),
        pytest.param({},                                      FIELD_TREELESS,    False, id=ID_TREELESS_MISSING),
        pytest.param({ATTRIB_TREELESS:    ATTRIB_BOOL_TRUE},  FIELD_TREELESS,    True,  id=ID_TREELESS_TRUE),
        pytest.param({ATTRIB_TREELESS:    ATTRIB_BOOL_FALSE}, FIELD_TREELESS,    False, id=ID_TREELESS_FALSE),
        pytest.param({ATTRIB_LOCAL_ROOT:  NESTED_LOCAL_ROOT}, FIELD_NESTED_REPO, True,  id=ID_NESTED_REPO_TRUE),
        pytest.param({},                                      FIELD_NESTED_REPO, False, id=ID_NESTED_REPO_FALSE),
    ])
    def test_init_sets_bool_field(self, base_attrib, extra, field_name, expected):
        """Each boolean attribute must default to False when absent and map 'true'/'false' to True/False correctly."""
        base_attrib.update(extra)
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = _RepoSource(element, make_mock_remotes())
        assert getattr(rs, field_name) is expected

    def test_init_raises_key_error_when_no_ref_specified(self):
        """When none of branch, commit, tag, or patchSet is specified, __init__ must raise KeyError."""
        element = make_mock_element({ATTRIB_LOCAL_ROOT: LOCAL_ROOT, ATTRIB_REMOTE: REMOTE_NAME}, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(KeyError) as exc_info:
            _RepoSource(element, make_mock_remotes())

        assert exc_info.value.args[0] == ATTRIBUTE_MISSING_ERROR

    @pytest.mark.parametrize(PARAM_PATCH_SET_COMBO, [
        pytest.param(ATTRIB_BRANCH, BRANCH, id=ID_PATCH_SET_WITH_BRANCH),
        pytest.param(ATTRIB_COMMIT, COMMIT, id=ID_PATCH_SET_WITH_COMMIT),
        pytest.param(ATTRIB_TAG,    TAG,    id=ID_PATCH_SET_WITH_TAG),
    ])
    def test_init_raises_value_error_when_patch_set_combined_with_ref(self, default_remotes, ref_attrib_key, ref_attrib_val):
        """When patchSet is specified alongside any other ref attribute, __init__ must raise ValueError."""
        element = make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_PATCH_SET: PATCH_SET,
            ref_attrib_key: ref_attrib_val,
        }, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(ValueError) as exc_info:
            _RepoSource(element, default_remotes)

        assert str(exc_info.value) == INVALID_COMBO_DEFINITION_ERROR

    def test_tuple_returns_correct_repo_source_namedtuple(self, base_attrib, default_remotes):
        """The tuple property must return a RepoSource namedtuple with all field values correct."""
        base_attrib.update({
            ATTRIB_COMMIT:     COMMIT,
            ATTRIB_SPARSE:     ATTRIB_BOOL_TRUE,
            ATTRIB_ENABLE_SUB: ATTRIB_BOOL_FALSE,
            ATTRIB_VENV_CFG:   VENV_CFG,
            ATTRIB_BLOBLESS:   ATTRIB_BOOL_FALSE,
            ATTRIB_TREELESS:   ATTRIB_BOOL_FALSE,
        })
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = _RepoSource(element, default_remotes)

        result = rs.tuple

        assert result == RepoSource(
            root=LOCAL_ROOT,
            remote_name=REMOTE_NAME,
            remote_url=REMOTE_URL,
            branch=BRANCH,
            commit=COMMIT,
            sparse=True,
            enable_submodule=False,
            tag=None,
            venv_cfg=VENV_CFG,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False,
        )

