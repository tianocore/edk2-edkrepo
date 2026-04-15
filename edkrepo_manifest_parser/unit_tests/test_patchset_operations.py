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
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

ELEMENT_TAG_CHERRY_PICK = 'CherryPick'
ATTRIB_SHA = 'sha'
ATTRIB_SOURCE_REMOTE = 'sourceRemote'
ATTRIB_SOURCE_BRANCH = 'sourceBranch'
ATTRIB_MERGE_STRATEGY = 'mergeStrategy'
OPS_FILE = 'some_file.patch'
OPS_SHA = 'aabbcc'
OPS_MERGE_STRATEGY = 'ours'
FIELD_SOURCE_REMOTE = 'source_remote'
FIELD_SOURCE_BRANCH = 'source_branch'
FIELD_MERGE_STRATEGY = 'merge_strategy'


class TestPatchSetOperations:

    @pytest.fixture
    def full_ops(self):
        """Return a _PatchSetOperations instance with all optional attributes present."""
        return edk_manifest._PatchSetOperations(helpers.make_mock_element({
            helpers.ATTRIB_FILE: OPS_FILE,
            ATTRIB_SHA: OPS_SHA,
            ATTRIB_SOURCE_REMOTE: helpers.UPSTREAM,
            ATTRIB_SOURCE_BRANCH: helpers.DEV,
            ATTRIB_MERGE_STRATEGY: OPS_MERGE_STRATEGY,
        }, tag=ELEMENT_TAG_CHERRY_PICK))

    def test_init_sets_type_from_element_tag(self):
        """__init__ must set self.type to element.tag."""
        element = helpers.make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK)

        ops = edk_manifest._PatchSetOperations(element)

        assert ops.type == ELEMENT_TAG_CHERRY_PICK

    def test_init_sets_all_optional_attribs_when_present(self, full_ops):
        """When all optional attributes are present, __init__ must set each field to its value."""
        assert full_ops.file == OPS_FILE
        assert full_ops.sha == OPS_SHA
        assert full_ops.source_remote == helpers.UPSTREAM
        assert full_ops.source_branch == helpers.DEV
        assert full_ops.merge_strategy == OPS_MERGE_STRATEGY

    @pytest.mark.parametrize(helpers.PARAM_FIELD_NAME, [
        pytest.param(helpers.ATTRIB_FILE, id=helpers.ATTRIB_FILE),
        pytest.param(ATTRIB_SHA, id=ATTRIB_SHA),
        pytest.param(FIELD_SOURCE_REMOTE, id=FIELD_SOURCE_REMOTE),
        pytest.param(FIELD_SOURCE_BRANCH, id=FIELD_SOURCE_BRANCH),
        pytest.param(FIELD_MERGE_STRATEGY, id=FIELD_MERGE_STRATEGY),
    ])
    def test_init_optional_attrib_defaults_to_none_when_missing(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        ops = edk_manifest._PatchSetOperations(helpers.make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK))
        assert getattr(ops, field_name) is None

    def test_tuple_returns_correct_patch_operation_namedtuple(self, full_ops):
        """The tuple property must return a PatchOperation namedtuple with the correct field values."""
        assert full_ops.tuple == edk_manifest.PatchOperation(
            type=ELEMENT_TAG_CHERRY_PICK,
            file=OPS_FILE,
            sha=OPS_SHA,
            source_remote=helpers.UPSTREAM,
            source_branch=helpers.DEV,
            merge_strategy=OPS_MERGE_STRATEGY,
        )
