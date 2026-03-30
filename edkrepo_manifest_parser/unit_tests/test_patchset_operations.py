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
)
from edkrepo_manifest_parser.edk_manifest import _PatchSetOperations, PatchOperation

ELEMENT_TAG_CHERRY_PICK  = 'CherryPick'
ATTRIB_FILE              = 'file'
ATTRIB_SHA               = 'sha'
ATTRIB_SOURCE_REMOTE     = 'sourceRemote'
ATTRIB_SOURCE_BRANCH     = 'sourceBranch'
ATTRIB_MERGE_STRATEGY    = 'mergeStrategy'
OPS_FILE                 = 'some_file.patch'
OPS_SHA                  = 'aabbcc'
OPS_SOURCE_REMOTE        = 'upstream'
OPS_SOURCE_BRANCH        = 'dev'
OPS_MERGE_STRATEGY       = 'ours'
FIELD_SOURCE_REMOTE      = 'source_remote'
FIELD_SOURCE_BRANCH      = 'source_branch'
FIELD_MERGE_STRATEGY     = 'merge_strategy'
PARAM_FIELD_NAME         = 'field_name'


class TestPatchSetOperations:

    @pytest.fixture
    def full_ops(self):
        """Return a _PatchSetOperations instance with all optional attributes present."""
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

    def test_init_sets_all_optional_attribs_when_present(self, full_ops):
        """When all optional attributes are present, __init__ must set each field to its value."""
        assert full_ops.file == OPS_FILE
        assert full_ops.sha == OPS_SHA
        assert full_ops.source_remote == OPS_SOURCE_REMOTE
        assert full_ops.source_branch == OPS_SOURCE_BRANCH
        assert full_ops.merge_strategy == OPS_MERGE_STRATEGY

    @pytest.mark.parametrize(PARAM_FIELD_NAME, [
        pytest.param(ATTRIB_FILE,          id=ATTRIB_FILE),
        pytest.param(ATTRIB_SHA,           id=ATTRIB_SHA),
        pytest.param(FIELD_SOURCE_REMOTE,  id=FIELD_SOURCE_REMOTE),
        pytest.param(FIELD_SOURCE_BRANCH,  id=FIELD_SOURCE_BRANCH),
        pytest.param(FIELD_MERGE_STRATEGY, id=FIELD_MERGE_STRATEGY),
    ])
    def test_init_optional_attrib_defaults_to_none_when_missing(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        ops = _PatchSetOperations(make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK))
        assert getattr(ops, field_name) is None

    def test_tuple_returns_correct_patch_operation_namedtuple(self, full_ops):
        """The tuple property must return a PatchOperation namedtuple with the correct field values."""
        assert full_ops.tuple == PatchOperation(
            type=ELEMENT_TAG_CHERRY_PICK,
            file=OPS_FILE,
            sha=OPS_SHA,
            source_remote=OPS_SOURCE_REMOTE,
            source_branch=OPS_SOURCE_BRANCH,
            merge_strategy=OPS_MERGE_STRATEGY,
        )
