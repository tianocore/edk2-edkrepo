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
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element,
    REQUIRED_ATTRIB_SPLIT_CHAR,
    REMOTE_NAME,
)
from edkrepo_manifest_parser.edk_manifest import (
    _PatchSet,
    _parse_patchset_required_attribs,
    PatchSet,
    REQUIRED_ATTRIB_ERROR_MSG,
)

ATTRIB_NAME          = 'name'
ATTRIB_REMOTE        = 'remote'
ATTRIB_PARENT_SHA    = 'parentSha'
ATTRIB_FETCH_BRANCH  = 'fetchBranch'
ELEMENT_TAG_PATCHSET = 'PatchSet'
PATCHSET_NAME        = 'ps_name'
OTHER_PATCHSET_NAME  = 'other_ps'
COMMIT               = 'abc123'
BRANCH               = 'main'

PARAM_MISSING_ATTRIB      = 'missing_attrib'
ID_REMOTE_MISSING         = 'remote_missing'
ID_NAME_MISSING           = 'name_missing'
ID_PARENT_SHA_MISSING     = 'parent_sha_missing'
ID_FETCH_BRANCH_MISSING   = 'fetch_branch_missing'


class TestPatchSet:

    @staticmethod
    def _make_full_element():
        """Build a mock element with all four required patchset attributes."""
        return make_mock_element({
            ATTRIB_REMOTE:       REMOTE_NAME,
            ATTRIB_NAME:         PATCHSET_NAME,
            ATTRIB_PARENT_SHA:   COMMIT,
            ATTRIB_FETCH_BRANCH: BRANCH,
        }, tag=ELEMENT_TAG_PATCHSET)

    def test_parse_required_attribs_returns_all_four_when_all_present(self):
        """When all four required attributes are present, must return the four values."""
        element = self._make_full_element()

        remote, name, parent_sha, fetch_branch = _parse_patchset_required_attribs(element)

        assert remote == REMOTE_NAME
        assert name == PATCHSET_NAME
        assert parent_sha == COMMIT
        assert fetch_branch == BRANCH

    @pytest.mark.parametrize(PARAM_MISSING_ATTRIB, [
        pytest.param(ATTRIB_REMOTE,       id=ID_REMOTE_MISSING),
        pytest.param(ATTRIB_NAME,         id=ID_NAME_MISSING),
        pytest.param(ATTRIB_PARENT_SHA,   id=ID_PARENT_SHA_MISSING),
        pytest.param(ATTRIB_FETCH_BRANCH, id=ID_FETCH_BRANCH_MISSING),
    ])
    def test_parse_required_attribs_raises_key_error_when_missing(self, missing_attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        full = {
            ATTRIB_REMOTE:       REMOTE_NAME,
            ATTRIB_NAME:         PATCHSET_NAME,
            ATTRIB_PARENT_SHA:   COMMIT,
            ATTRIB_FETCH_BRANCH: BRANCH,
        }
        del full[missing_attrib]
        element = make_mock_element(full, tag=ELEMENT_TAG_PATCHSET)
        with pytest.raises(KeyError) as exc_info:
            _parse_patchset_required_attribs(element)
        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_all_fields_from_required_attribs(self):
        """When all required attributes are present, __init__ must set all four fields correctly."""
        element = self._make_full_element()

        ps = _PatchSet(element)

        assert ps.remote == REMOTE_NAME
        assert ps.name == PATCHSET_NAME
        assert ps.parentSha == COMMIT
        assert ps.fetchBranch == BRANCH

    def test_eq_returns_true_for_equal_patchsets(self):
        """Two _PatchSet instances with identical attributes must compare as equal."""
        ps1 = _PatchSet(self._make_full_element())
        ps2 = _PatchSet(self._make_full_element())

        assert ps1 == ps2

    def test_eq_returns_false_for_different_patchsets(self):
        """Two _PatchSet instances with different attributes must not compare as equal."""
        ps1 = _PatchSet(self._make_full_element())
        ps2 = _PatchSet(make_mock_element({
            ATTRIB_REMOTE:       REMOTE_NAME,
            ATTRIB_NAME:         OTHER_PATCHSET_NAME,
            ATTRIB_PARENT_SHA:   COMMIT,
            ATTRIB_FETCH_BRANCH: BRANCH,
        }, tag=ELEMENT_TAG_PATCHSET))

        assert ps1 != ps2

    def test_eq_returns_false_for_non_patchset_type(self):
        """Comparing a _PatchSet to a non-_PatchSet object must return False."""
        ps = _PatchSet(self._make_full_element())

        assert ps.__eq__(object()) is False

    def test_tuple_returns_correct_patchset_namedtuple(self):
        """The tuple property must return a PatchSet namedtuple with the correct field values."""
        ps = _PatchSet(self._make_full_element())

        result = ps.tuple

        assert result == PatchSet(
            remote=REMOTE_NAME,
            name=PATCHSET_NAME,
            parent_sha=COMMIT,
            fetch_branch=BRANCH,
        )
