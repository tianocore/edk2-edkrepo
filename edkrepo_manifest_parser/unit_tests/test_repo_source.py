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
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element,
    make_mock_remotes,
    ATTRIB_REMOTE,
    REMOTE_NAME,
    REMOTE_URL,
    ATTRIB_BOOL_TRUE,
    ATTRIB_BOOL_FALSE,
    REQUIRED_ATTRIB_SPLIT_CHAR,
    ELEMENT_TAG_SOURCE,
    LOCAL_ROOT,
    NESTED_LOCAL_ROOT,
    BRANCH,
    COMMIT,
    TAG,
    PATCH_SET,
    VENV_CFG,
    ATTRIB_LOCAL_ROOT,
    ATTRIB_BRANCH,
    ATTRIB_COMMIT,
    ATTRIB_TAG,
    ATTRIB_PATCH_SET,
    ATTRIB_SPARSE,
    ATTRIB_ENABLE_SUB,
    ATTRIB_ENABLE_SUB_LEGACY,
    ATTRIB_VENV_CFG,
    ATTRIB_BLOBLESS,
    ATTRIB_TREELESS,
    FIELD_SPARSE,
    FIELD_ENABLE_SUB,
    FIELD_NESTED_REPO,
    REPO_SOURCE_BOOL_FIELD_FIELDS,
    REPO_SOURCE_PATCH_SET_COMBO_FIELDS,
    ID_SPARSE_MISSING,
    ID_SPARSE_TRUE,
    ID_SPARSE_FALSE,
    ID_ENABLE_SUB_MISSING,
    ID_ENABLE_SUB_TRUE,
    ID_ENABLE_SUB_FALSE,
    ID_BLOBLESS_MISSING,
    ID_BLOBLESS_TRUE,
    ID_BLOBLESS_FALSE,
    ID_TREELESS_MISSING,
    ID_TREELESS_TRUE,
    ID_TREELESS_FALSE,
)
from edkrepo_manifest_parser.edk_manifest import (
    _RepoSource,
    _parse_repo_source_required_attribs,
    RepoSource,
    REQUIRED_ATTRIB_ERROR_MSG,
    ATTRIBUTE_MISSING_ERROR,
    INVALID_COMBO_DEFINITION_ERROR,
)

BOOL_FIELD_IDS = [
    ID_SPARSE_MISSING,     ID_SPARSE_TRUE,     ID_SPARSE_FALSE,
    ID_ENABLE_SUB_MISSING, ID_ENABLE_SUB_TRUE, ID_ENABLE_SUB_FALSE,
    ID_BLOBLESS_MISSING,   ID_BLOBLESS_TRUE,   ID_BLOBLESS_FALSE,
    ID_TREELESS_MISSING,   ID_TREELESS_TRUE,   ID_TREELESS_FALSE,
]
PATCH_SET_COMBO_IDS = [ATTRIB_BRANCH, ATTRIB_COMMIT, ATTRIB_TAG]


class TestRepoSource:

    @staticmethod
    def _make_base_attrib():
        """Build the minimum valid attrib dict with required fields plus a branch ref."""
        return {
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_BRANCH: BRANCH,
        }

    @staticmethod
    def _make_required_element(**extra):
        """Build a mock element with the minimum valid attributes plus any extras."""
        attrib = TestRepoSource._make_base_attrib()
        attrib.update(extra)
        return make_mock_element(attrib, tag=ELEMENT_TAG_SOURCE)

    @staticmethod
    def _make_single_ref_element(ref_key, ref_val):
        """Build a mock element with only the required fields (localRoot, remote) and one ref attribute."""
        return make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ref_key: ref_val,
        }, tag=ELEMENT_TAG_SOURCE)

    @staticmethod
    def _assert_bool_field(extra, field_name, expected):
        """Build a _RepoSource adding extra to the base attrib and assert field_name matches expected."""
        attrib = TestRepoSource._make_base_attrib()
        attrib.update(extra)
        element = make_mock_element(attrib, tag=ELEMENT_TAG_SOURCE)
        remotes = make_mock_remotes()
        rs = _RepoSource(element, remotes)
        assert getattr(rs, field_name) is expected

    @staticmethod
    def _assert_optional_field(extra_key, extra_val, field_name, expected):
        """Build a _RepoSource adding {extra_key: extra_val} to the base attrib and assert field_name equals expected."""
        element = TestRepoSource._make_required_element(**{extra_key: extra_val})
        remotes = make_mock_remotes()
        rs = _RepoSource(element, remotes)
        assert getattr(rs, field_name) == expected

    @staticmethod
    def _assert_parse_raises_key_error(attrib, remotes):
        """Build a mock element from attrib and assert _parse_repo_source_required_attribs raises KeyError with the required-attrib message prefix."""
        element = make_mock_element(attrib, tag=ELEMENT_TAG_SOURCE)
        with pytest.raises(KeyError) as exc_info:
            _parse_repo_source_required_attribs(element, remotes)
        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry using the class-level constants."""
        return make_mock_remotes()

    @pytest.fixture
    def base_source(self, default_remotes):
        """Return a _RepoSource built from the minimum valid element and the default remotes."""
        return _RepoSource(self._make_required_element(), default_remotes)

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

    def test_parse_required_attribs_raises_key_error_when_local_root_missing(self, default_remotes):
        """When localRoot is absent, must raise KeyError with the required-attrib message."""
        self._assert_parse_raises_key_error({ATTRIB_REMOTE: REMOTE_NAME}, default_remotes)

    def test_parse_required_attribs_raises_key_error_when_remote_attrib_missing(self, default_remotes):
        """When the remote attribute is absent from the element, must raise KeyError."""
        self._assert_parse_raises_key_error({ATTRIB_LOCAL_ROOT: LOCAL_ROOT}, default_remotes)

    def test_parse_required_attribs_raises_key_error_when_remote_not_in_remotes(self):
        """When the remote attribute value is not a key in remotes, must raise KeyError."""
        self._assert_parse_raises_key_error(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT, ATTRIB_REMOTE: REMOTE_NAME},
            {},
        )

    def test_init_sets_all_required_fields(self, base_source):
        """When all required attributes are present, __init__ must set root, remote_name, and remote_url correctly."""
        assert base_source.root == LOCAL_ROOT
        assert base_source.remote_name == REMOTE_NAME
        assert base_source.remote_url == REMOTE_URL

    def test_init_sets_branch_when_present(self, base_source):
        """When the branch attribute is present, __init__ must set BRANCH to its value."""
        assert base_source.branch == BRANCH

    def test_init_sets_branch_to_none_when_absent(self):
        """When the branch attribute is absent, __init__ must set BRANCH to None."""
        element = self._make_single_ref_element(ATTRIB_COMMIT, COMMIT)
        assert _RepoSource(element, make_mock_remotes()).branch is None

    def test_init_sets_commit_when_present(self):
        """When the commit attribute is present, __init__ must set COMMIT to its value."""
        self._assert_optional_field(ATTRIB_COMMIT, COMMIT, ATTRIB_COMMIT, COMMIT)

    def test_init_sets_commit_to_none_when_absent(self, base_source):
        """When the commit attribute is absent, __init__ must set COMMIT to None."""
        assert base_source.commit is None

    def test_init_sets_tag_when_present(self):
        """When the tag attribute is present, __init__ must set TAG to its value."""
        self._assert_optional_field(ATTRIB_TAG, TAG, ATTRIB_TAG, TAG)

    def test_init_sets_tag_to_none_when_absent(self, base_source):
        """When the tag attribute is absent, __init__ must set TAG to None."""
        assert base_source.tag is None

    def test_init_sets_patch_set_when_present(self):
        """When the patchSet attribute is present and no other ref is given, __init__ must set PATCH_SET to its value."""
        element = self._make_single_ref_element(ATTRIB_PATCH_SET, PATCH_SET)
        assert _RepoSource(element, make_mock_remotes()).patch_set == PATCH_SET

    def test_init_sets_patch_set_to_none_when_absent(self, base_source):
        """When the patchSet attribute is absent, __init__ must set PATCH_SET to None."""
        assert base_source.patch_set is None

    @pytest.mark.parametrize(REPO_SOURCE_BOOL_FIELD_FIELDS, [
        ({},                                    FIELD_SPARSE,     False),
        ({ATTRIB_SPARSE:      ATTRIB_BOOL_TRUE},  FIELD_SPARSE,     True),
        ({ATTRIB_SPARSE:      ATTRIB_BOOL_FALSE}, FIELD_SPARSE,     False),
        ({},                                    FIELD_ENABLE_SUB, False),
        ({ATTRIB_ENABLE_SUB:  ATTRIB_BOOL_TRUE},  FIELD_ENABLE_SUB, True),
        ({ATTRIB_ENABLE_SUB:  ATTRIB_BOOL_FALSE}, FIELD_ENABLE_SUB, False),
        ({},                                    ATTRIB_BLOBLESS,   False),
        ({ATTRIB_BLOBLESS:    ATTRIB_BOOL_TRUE},  ATTRIB_BLOBLESS,   True),
        ({ATTRIB_BLOBLESS:    ATTRIB_BOOL_FALSE}, ATTRIB_BLOBLESS,   False),
        ({},                                    ATTRIB_TREELESS,   False),
        ({ATTRIB_TREELESS:    ATTRIB_BOOL_TRUE},  ATTRIB_TREELESS,   True),
        ({ATTRIB_TREELESS:    ATTRIB_BOOL_FALSE}, ATTRIB_TREELESS,   False),
    ], ids=BOOL_FIELD_IDS)
    def test_init_bool_field(self, extra, field_name, expected):
        """Each boolean attribute must default to False when absent, and map 'true'/'false' correctly."""
        self._assert_bool_field(extra, field_name, expected)

    def test_init_enable_submodule_backwards_compat_with_legacy_attr(self):
        """When enableSubmodule is absent but enable_submodule is 'true', __init__ must set self.enableSub to True."""
        self._assert_optional_field(ATTRIB_ENABLE_SUB_LEGACY, ATTRIB_BOOL_TRUE, FIELD_ENABLE_SUB, True)

    def test_init_venv_cfg_when_present(self):
        """When the venv_cfg attribute is present, __init__ must set VENV_CFG to its value."""
        self._assert_optional_field(ATTRIB_VENV_CFG, VENV_CFG, ATTRIB_VENV_CFG, VENV_CFG)

    def test_init_venv_cfg_to_none_when_absent(self, base_source):
        """When the venv_cfg attribute is absent, __init__ must set VENV_CFG to None."""
        assert base_source.venv_cfg is None

    def test_init_raises_key_error_when_no_ref_specified(self):
        """When none of branch, commit, tag, or patchSet is specified, __init__ must raise KeyError."""
        element = make_mock_element({ATTRIB_LOCAL_ROOT: LOCAL_ROOT, ATTRIB_REMOTE: REMOTE_NAME}, tag=ELEMENT_TAG_SOURCE)
        with pytest.raises(KeyError) as exc_info:
            _RepoSource(element, make_mock_remotes())
        assert exc_info.value.args[0] == ATTRIBUTE_MISSING_ERROR

    @pytest.mark.parametrize(REPO_SOURCE_PATCH_SET_COMBO_FIELDS, [
        (ATTRIB_BRANCH, BRANCH),
        (ATTRIB_COMMIT, COMMIT),
        (ATTRIB_TAG,    TAG),
    ], ids=PATCH_SET_COMBO_IDS)
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

    def test_init_nested_repo_true_for_deep_path(self):
        """When localRoot has more than one path component, __init__ must set self.nested_repo to True."""
        self._assert_bool_field({ATTRIB_LOCAL_ROOT: NESTED_LOCAL_ROOT}, FIELD_NESTED_REPO, True)

    def test_init_nested_repo_false_for_single_component_path(self, base_source):
        """When localRoot has only one path component, __init__ must set self.nested_repo to False."""
        assert base_source.nested_repo is False

    def test_tuple_returns_correct_repo_source_namedtuple(self, default_remotes):
        """The tuple property must return a RepoSource namedtuple with all field values correct."""
        element = self._make_required_element(
            **{
                ATTRIB_COMMIT: COMMIT,
                ATTRIB_SPARSE: ATTRIB_BOOL_TRUE,
                ATTRIB_ENABLE_SUB: ATTRIB_BOOL_FALSE,
                ATTRIB_VENV_CFG: VENV_CFG,
                ATTRIB_BLOBLESS: ATTRIB_BOOL_FALSE,
                ATTRIB_TREELESS: ATTRIB_BOOL_FALSE,
            }
        )
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
