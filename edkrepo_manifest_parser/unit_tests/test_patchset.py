#!/usr/bin/env python3
#
## @file
# test_patchset.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

ATTRIB_PARENT_SHA = 'parentSha'
ATTRIB_FETCH_BRANCH = 'fetchBranch'
ELEMENT_TAG_PATCHSET = 'edk_manifest.PatchSet'
OTHER_PATCHSET_NAME = 'other_ps'
ID_NAME_MISSING = 'name_missing'
ID_PARENT_SHA_MISSING = 'parent_sha_missing'
ID_FETCH_BRANCH_MISSING = 'fetch_branch_missing'


class TestPatchSet:

    @staticmethod
    def _make_full_element():
        """Build a mock element with all four required patchset attributes."""
        return helpers.make_mock_element({
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            helpers.ATTRIB_NAME: helpers.PATCHSET_NAME,
            ATTRIB_PARENT_SHA: helpers.COMMIT,
            ATTRIB_FETCH_BRANCH: helpers.BRANCH,
        }, tag=ELEMENT_TAG_PATCHSET)

    def test_parse_required_attribs_returns_all_four_when_all_present(self):
        """When all four required attributes are present, must return the four values."""
        element = self._make_full_element()

        remote, name, parent_sha, fetch_branch = edk_manifest._parse_patchset_required_attribs(element)

        assert remote == helpers.REMOTE_NAME
        assert name == helpers.PATCHSET_NAME
        assert parent_sha == helpers.COMMIT
        assert fetch_branch == helpers.BRANCH

    @pytest.mark.parametrize(helpers.PARAM_MISSING_ATTRIB, [
        pytest.param(helpers.ATTRIB_REMOTE, id=helpers.ID_REMOTE_MISSING),
        pytest.param(helpers.ATTRIB_NAME, id=ID_NAME_MISSING),
        pytest.param(ATTRIB_PARENT_SHA, id=ID_PARENT_SHA_MISSING),
        pytest.param(ATTRIB_FETCH_BRANCH, id=ID_FETCH_BRANCH_MISSING),
    ])
    def test_parse_required_attribs_raises_key_error_when_missing(self, missing_attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        full = {
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            helpers.ATTRIB_NAME: helpers.PATCHSET_NAME,
            ATTRIB_PARENT_SHA: helpers.COMMIT,
            ATTRIB_FETCH_BRANCH: helpers.BRANCH,
        }
        del full[missing_attrib]
        element = helpers.make_mock_element(full, tag=ELEMENT_TAG_PATCHSET)
        with pytest.raises(KeyError) as exc_info:
            edk_manifest._parse_patchset_required_attribs(element)
        assert edk_manifest.REQUIRED_ATTRIB_ERROR_MSG.split(helpers.REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_all_fields_from_required_attribs(self):
        """When all required attributes are present, __init__ must set all four fields correctly."""
        element = self._make_full_element()

        ps = edk_manifest._PatchSet(element)

        assert ps.remote == helpers.REMOTE_NAME
        assert ps.name == helpers.PATCHSET_NAME
        assert ps.parentSha == helpers.COMMIT
        assert ps.fetchBranch == helpers.BRANCH

    def test_eq_returns_true_for_equal_patchsets(self):
        """Two edk_manifest._PatchSet instances with identical attributes must compare as equal."""
        ps1 = edk_manifest._PatchSet(self._make_full_element())
        ps2 = edk_manifest._PatchSet(self._make_full_element())

        assert ps1 == ps2

    def test_eq_returns_false_for_different_patchsets(self):
        """Two edk_manifest._PatchSet instances with different attributes must not compare as equal."""
        ps1 = edk_manifest._PatchSet(self._make_full_element())
        ps2 = edk_manifest._PatchSet(helpers.make_mock_element({
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            helpers.ATTRIB_NAME: OTHER_PATCHSET_NAME,
            ATTRIB_PARENT_SHA: helpers.COMMIT,
            ATTRIB_FETCH_BRANCH: helpers.BRANCH,
        }, tag=ELEMENT_TAG_PATCHSET))

        assert ps1 != ps2

    def test_eq_returns_false_for_non_patchset_type(self):
        """Comparing a edk_manifest._PatchSet to a non-edk_manifest._PatchSet object must return False."""
        ps = edk_manifest._PatchSet(self._make_full_element())

        assert ps.__eq__(object()) is False

    def test_tuple_returns_correct_patchset_namedtuple(self):
        """The tuple property must return a edk_manifest.PatchSet namedtuple with the correct field values."""
        ps = edk_manifest._PatchSet(self._make_full_element())

        result = ps.tuple

        assert result == edk_manifest.PatchSet(
            remote=helpers.REMOTE_NAME,
            name=helpers.PATCHSET_NAME,
            parent_sha=helpers.COMMIT,
            fetch_branch=helpers.BRANCH,
        )
