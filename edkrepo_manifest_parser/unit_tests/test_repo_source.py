#!/usr/bin/env python3
#
## @file
# test_repo_source.py
#
# Copyright (c) 2025 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

# XML attribute names
ATTRIB_LOCAL_ROOT = 'localRoot'
ATTRIB_BRANCH = 'branch'
ATTRIB_COMMIT = 'commit'
ATTRIB_TAG = 'tag'
ATTRIB_PATCH_SET = 'patchSet'
ATTRIB_SPARSE = 'sparseCheckout'
ATTRIB_ENABLE_SUB = 'enableSubmodule'
ATTRIB_ENABLE_SUB_LEGACY = 'enable_submodule'
ATTRIB_VENV_CFG = 'venv_cfg'
ATTRIB_BLOBLESS = 'blobless'
ATTRIB_TREELESS = 'treeless'

# Element tag
ELEMENT_TAG_SOURCE = 'Source'

# Test data values
LOCAL_ROOT = 'MyRepo'
NESTED_LOCAL_ROOT = 'parent/MyRepo'
TAG = 'v1.0.0'
PATCH_SET = 'ps-debug'
VENV_CFG = 'venv.cfg'
FIELD_SPARSE = 'sparse'
FIELD_ENABLE_SUB = 'enableSub'
FIELD_NESTED_REPO = 'nested_repo'
FIELD_PATCH_SET = 'patch_set'
PARAM_BOOL_FIELD = 'extra, field_name, expected'
PARAM_PATCH_SET_COMBO = 'ref_attrib_key, ref_attrib_val'
PARAM_PARSE_RAISES = 'attrib, remotes'
ID_SPARSE_MISSING = 'sparse_missing'
ID_SPARSE_TRUE = 'sparse_true'
ID_SPARSE_FALSE = 'sparse_false'
ID_ENABLE_SUB_MISSING = 'enable_sub_missing'
ID_ENABLE_SUB_TRUE = 'enable_sub_true'
ID_ENABLE_SUB_FALSE = 'enable_sub_false'
ID_BLOBLESS_MISSING = 'blobless_missing'
ID_BLOBLESS_TRUE = 'blobless_true'
ID_BLOBLESS_FALSE = 'blobless_false'
ID_TREELESS_MISSING = 'treeless_missing'
ID_TREELESS_TRUE = 'treeless_true'
ID_TREELESS_FALSE = 'treeless_false'
ID_NESTED_REPO_TRUE = 'nested_repo_true'
ID_NESTED_REPO_FALSE = 'nested_repo_false'
ID_PATCH_SET_WITH_BRANCH = 'patch_set_with_branch'
ID_PATCH_SET_WITH_COMMIT = 'patch_set_with_commit'
ID_PATCH_SET_WITH_TAG = 'patch_set_with_tag'
ID_COMMIT_PRESENT = 'commit_present'
ID_TAG_PRESENT = 'tag_present'
ID_COMMIT_ABSENT = 'commit_absent'
ID_TAG_ABSENT = 'tag_absent'
ID_PATCH_SET_ABSENT = 'patch_set_absent'
ID_LOCAL_ROOT_MISSING = 'local_root_missing'
ID_REMOTE_ATTRIB_MISSING = 'remote_attrib_missing'
ID_REMOTE_NOT_IN_REMOTES = 'remote_not_in_remotes'
ID_ENABLE_SUB_LEGACY_COMPAT = 'enable_sub_legacy_compat'
ID_VENV_CFG_PRESENT = 'venv_cfg_present'
ID_VENV_CFG_ABSENT = 'venv_cfg_absent'


class TestRepoSource:

    @staticmethod
    def _make_single_ref_element(ref_key, ref_val):
        """Build a mock element with only the required fields (localRoot, remote) and one ref attribute."""
        return helpers.make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            ref_key: ref_val,
        }, tag=ELEMENT_TAG_SOURCE)

    @pytest.fixture
    def base_attrib(self):
        """Return minimum valid attributes dict (mutable - tests can modify as needed)."""
        return {
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            ATTRIB_BRANCH: helpers.BRANCH,
        }

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry."""
        return helpers.make_mock_remotes()

    @pytest.fixture
    def base_source(self, base_attrib, default_remotes):
        """Return a edk_manifest._RepoSource built from minimum valid attributes."""
        element = helpers.make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        return edk_manifest._RepoSource(element, default_remotes)

    def test_parse_required_attribs_returns_all_three_when_all_present(self, default_remotes):
        """When all required attributes and the remote key are present, must return (root, remote_name, remote_url)."""
        element = helpers.make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
        }, tag=ELEMENT_TAG_SOURCE)

        root, remote_name, remote_url = edk_manifest._parse_repo_source_required_attribs(element, default_remotes)

        assert root == LOCAL_ROOT
        assert remote_name == helpers.REMOTE_NAME
        assert remote_url == helpers.REMOTE_URL

    @pytest.mark.parametrize(PARAM_PARSE_RAISES, [
        pytest.param(
            {helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME}, helpers.make_mock_remotes(),
            id=ID_LOCAL_ROOT_MISSING,
        ),
        pytest.param(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT}, helpers.make_mock_remotes(),
            id=ID_REMOTE_ATTRIB_MISSING,
        ),
        pytest.param(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT, helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME}, {}, id=ID_REMOTE_NOT_IN_REMOTES, ),
    ])
    def test_parse_required_attribs_raises_key_error(self, attrib, remotes):
        """When any required attribute or remote lookup is missing, must raise KeyError with the required-attrib message."""
        element = helpers.make_mock_element(attrib, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(KeyError) as exc_info:
            edk_manifest._parse_repo_source_required_attribs(element, remotes)

        assert edk_manifest.REQUIRED_ATTRIB_ERROR_MSG.split(helpers.REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_all_required_fields(self, base_source):
        """When all required attributes are present, __init__ must set root, remote_name, and remote_url correctly."""
        assert base_source.root == LOCAL_ROOT
        assert base_source.remote_name == helpers.REMOTE_NAME
        assert base_source.remote_url == helpers.REMOTE_URL

    def test_init_sets_branch_when_present(self, base_source):
        """When the branch attribute is present, __init__ must set self.branch to its value."""
        assert base_source.branch == helpers.BRANCH

    def test_init_sets_branch_to_none_when_absent(self):
        """When the branch attribute is absent, __init__ must set self.branch to None."""
        element = self._make_single_ref_element(ATTRIB_COMMIT, helpers.COMMIT)
        assert edk_manifest._RepoSource(element, helpers.make_mock_remotes()).branch is None

    @pytest.mark.parametrize(helpers.PARAM_ATTRIB_VAL_FIELD_EXPECTED, [
        pytest.param(ATTRIB_COMMIT, helpers.COMMIT, ATTRIB_COMMIT, helpers.COMMIT, id=ID_COMMIT_PRESENT),
        pytest.param(ATTRIB_TAG, TAG, ATTRIB_TAG, TAG, id=ID_TAG_PRESENT),
        pytest.param(ATTRIB_ENABLE_SUB_LEGACY, helpers.ATTRIB_BOOL_TRUE, FIELD_ENABLE_SUB, True, id=ID_ENABLE_SUB_LEGACY_COMPAT),
        pytest.param(ATTRIB_VENV_CFG, VENV_CFG, ATTRIB_VENV_CFG, VENV_CFG, id=ID_VENV_CFG_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, base_attrib, default_remotes, attrib_key, attrib_val, field_name, expected):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        base_attrib[attrib_key] = attrib_val
        element = helpers.make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = edk_manifest._RepoSource(element, default_remotes)
        assert getattr(rs, field_name) == expected

    @pytest.mark.parametrize(helpers.PARAM_FIELD_NAME, [
        pytest.param(ATTRIB_COMMIT, id=ID_COMMIT_ABSENT),
        pytest.param(ATTRIB_TAG, id=ID_TAG_ABSENT),
        pytest.param(FIELD_PATCH_SET, id=ID_PATCH_SET_ABSENT),
        pytest.param(ATTRIB_VENV_CFG, id=ID_VENV_CFG_ABSENT),
    ])
    def test_init_sets_optional_field_to_none_when_absent(self, base_source, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        assert getattr(base_source, field_name) is None

    def test_init_sets_patch_set_when_present(self):
        """When the patchSet attribute is present and no other ref is given, __init__ must set self.patch_set to its value."""
        element = self._make_single_ref_element(ATTRIB_PATCH_SET, PATCH_SET)
        assert edk_manifest._RepoSource(element, helpers.make_mock_remotes()).patch_set == PATCH_SET

    @pytest.mark.parametrize(PARAM_BOOL_FIELD, [
        pytest.param({}, FIELD_SPARSE, False, id=ID_SPARSE_MISSING),
        pytest.param({ATTRIB_SPARSE: helpers.ATTRIB_BOOL_TRUE}, FIELD_SPARSE, True, id=ID_SPARSE_TRUE),
        pytest.param({ATTRIB_SPARSE: helpers.ATTRIB_BOOL_FALSE}, FIELD_SPARSE, False, id=ID_SPARSE_FALSE),
        pytest.param({}, FIELD_ENABLE_SUB, False, id=ID_ENABLE_SUB_MISSING),
        pytest.param({ATTRIB_ENABLE_SUB: helpers.ATTRIB_BOOL_TRUE}, FIELD_ENABLE_SUB, True, id=ID_ENABLE_SUB_TRUE),
        pytest.param({ATTRIB_ENABLE_SUB: helpers.ATTRIB_BOOL_FALSE}, FIELD_ENABLE_SUB, False, id=ID_ENABLE_SUB_FALSE),
        pytest.param({}, ATTRIB_BLOBLESS, False, id=ID_BLOBLESS_MISSING),
        pytest.param({ATTRIB_BLOBLESS: helpers.ATTRIB_BOOL_TRUE}, ATTRIB_BLOBLESS, True, id=ID_BLOBLESS_TRUE),
        pytest.param({ATTRIB_BLOBLESS: helpers.ATTRIB_BOOL_FALSE}, ATTRIB_BLOBLESS, False, id=ID_BLOBLESS_FALSE),
        pytest.param({}, ATTRIB_TREELESS, False, id=ID_TREELESS_MISSING),
        pytest.param({ATTRIB_TREELESS: helpers.ATTRIB_BOOL_TRUE}, ATTRIB_TREELESS, True, id=ID_TREELESS_TRUE),
        pytest.param({ATTRIB_TREELESS: helpers.ATTRIB_BOOL_FALSE}, ATTRIB_TREELESS, False, id=ID_TREELESS_FALSE),
        pytest.param({ATTRIB_LOCAL_ROOT: NESTED_LOCAL_ROOT}, FIELD_NESTED_REPO, True, id=ID_NESTED_REPO_TRUE),
        pytest.param({}, FIELD_NESTED_REPO, False, id=ID_NESTED_REPO_FALSE),
    ])
    def test_init_sets_bool_field(self, base_attrib, extra, field_name, expected):
        """Each boolean attribute must default to False when absent and map 'true'/'false' to True/False correctly."""
        base_attrib.update(extra)
        element = helpers.make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = edk_manifest._RepoSource(element, helpers.make_mock_remotes())
        assert getattr(rs, field_name) is expected

    def test_init_raises_key_error_when_no_ref_specified(self):
        """When none of branch, commit, tag, or patchSet is specified, __init__ must raise KeyError."""
        element = helpers.make_mock_element({ATTRIB_LOCAL_ROOT: LOCAL_ROOT, helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME}, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(KeyError) as exc_info:
            edk_manifest._RepoSource(element, helpers.make_mock_remotes())

        assert exc_info.value.args[0] == edk_manifest.ATTRIBUTE_MISSING_ERROR

    @pytest.mark.parametrize(PARAM_PATCH_SET_COMBO, [
        pytest.param(ATTRIB_BRANCH, helpers.BRANCH, id=ID_PATCH_SET_WITH_BRANCH),
        pytest.param(ATTRIB_COMMIT, helpers.COMMIT, id=ID_PATCH_SET_WITH_COMMIT),
        pytest.param(ATTRIB_TAG, TAG, id=ID_PATCH_SET_WITH_TAG),
    ])
    def test_init_raises_value_error_when_patch_set_combined_with_ref(self, default_remotes, ref_attrib_key, ref_attrib_val):
        """When patchSet is specified alongside any other ref attribute, __init__ must raise ValueError."""
        element = helpers.make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            ATTRIB_PATCH_SET: PATCH_SET,
            ref_attrib_key: ref_attrib_val,
        }, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(ValueError) as exc_info:
            edk_manifest._RepoSource(element, default_remotes)

        assert str(exc_info.value) == edk_manifest.INVALID_COMBO_DEFINITION_ERROR

    def test_tuple_returns_correct_repo_source_namedtuple(self, base_attrib, default_remotes):
        """The tuple property must return a edk_manifest.RepoSource namedtuple with all field values correct."""
        base_attrib.update({
            ATTRIB_COMMIT:     helpers.COMMIT,
            ATTRIB_SPARSE:     helpers.ATTRIB_BOOL_TRUE,
            ATTRIB_ENABLE_SUB: helpers.ATTRIB_BOOL_FALSE,
            ATTRIB_VENV_CFG:   VENV_CFG,
            ATTRIB_BLOBLESS:   helpers.ATTRIB_BOOL_FALSE,
            ATTRIB_TREELESS:   helpers.ATTRIB_BOOL_FALSE,
        })
        element = helpers.make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = edk_manifest._RepoSource(element, default_remotes)

        result = rs.tuple

        assert result == edk_manifest.RepoSource(
            root=LOCAL_ROOT,
            remote_name=helpers.REMOTE_NAME,
            remote_url=helpers.REMOTE_URL,
            branch=helpers.BRANCH,
            commit=helpers.COMMIT,
            sparse=True,
            enable_submodule=False,
            tag=None,
            venv_cfg=VENV_CFG,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False,
        )
