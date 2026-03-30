#!/usr/bin/env python3
#
## @file
# test_patchset_operations.py
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
    ELEMENT_TAG_CHERRY_PICK,
    OPS_FILE,
    OPS_SHA,
    OPS_SOURCE_REMOTE,
    OPS_SOURCE_BRANCH,
    OPS_MERGE_STRATEGY,
    ATTRIB_FILE,
    ATTRIB_SHA,
    ATTRIB_SOURCE_REMOTE,
    ATTRIB_SOURCE_BRANCH,
    ATTRIB_MERGE_STRATEGY,
    FIELD_FILE,
    FIELD_SHA,
    FIELD_SOURCE_REMOTE,
    FIELD_SOURCE_BRANCH,
    FIELD_MERGE_STRATEGY,
    PARAMETRIZE_FIELD_NAME,
)
from edkrepo_manifest_parser.edk_manifest import _PatchSetOperations, PatchOperation

DEFAULTS_TO_NONE_IDS = [FIELD_FILE, FIELD_SHA, FIELD_SOURCE_REMOTE, FIELD_SOURCE_BRANCH, FIELD_MERGE_STRATEGY]


class TestPatchSetOperations:

    @staticmethod
    def _make_full_ops():
        """Build and return a _PatchSetOperations instance with all optional attributes present."""
        return _PatchSetOperations(make_mock_element({
            ATTRIB_FILE: OPS_FILE,
            ATTRIB_SHA: OPS_SHA,
            ATTRIB_SOURCE_REMOTE: OPS_SOURCE_REMOTE,
            ATTRIB_SOURCE_BRANCH: OPS_SOURCE_BRANCH,
            ATTRIB_MERGE_STRATEGY: OPS_MERGE_STRATEGY,
        }, tag=ELEMENT_TAG_CHERRY_PICK))

    def test_init_sets_type_from_element_tag(self):
        """__init__ must set self.type to element.tag."""
        element = make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK)

        ops = _PatchSetOperations(element)

        assert ops.type == ELEMENT_TAG_CHERRY_PICK

    def test_init_sets_all_optional_attribs_when_present(self):
        """When all optional attributes are present, __init__ must set each field to its value."""
        ops = self._make_full_ops()

        assert ops.file == OPS_FILE
        assert ops.sha == OPS_SHA
        assert ops.source_remote == OPS_SOURCE_REMOTE
        assert ops.source_branch == OPS_SOURCE_BRANCH
        assert ops.merge_strategy == OPS_MERGE_STRATEGY

    @pytest.mark.parametrize(PARAMETRIZE_FIELD_NAME, [
        FIELD_FILE,
        FIELD_SHA,
        FIELD_SOURCE_REMOTE,
        FIELD_SOURCE_BRANCH,
        FIELD_MERGE_STRATEGY,
    ], ids=DEFAULTS_TO_NONE_IDS)
    def test_init_optional_attrib_defaults_to_none_when_missing(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        ops = _PatchSetOperations(make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK))
        assert getattr(ops, field_name) is None

    def test_tuple_returns_correct_patch_operation_namedtuple(self):
        """The tuple property must return a PatchOperation namedtuple with the correct field values."""
        ops = self._make_full_ops()

        result = ops.tuple

        assert result == PatchOperation(
            type=ELEMENT_TAG_CHERRY_PICK,
            file=OPS_FILE,
            sha=OPS_SHA,
            source_remote=OPS_SOURCE_REMOTE,
            source_branch=OPS_SOURCE_BRANCH,
            merge_strategy=OPS_MERGE_STRATEGY,
        )
