#!/usr/bin/env python3
#
## @file
# test_sparse_settings.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
    make_empty_element,
    ATTRIB_BOOL_TRUE,
    ATTRIB_BOOL_FALSE,
    ATTRIB_SPARSE_BY_DEFAULT,
    BOOL_FLAG_FIELDS,
)
from edkrepo_manifest_parser.edk_manifest import (
    _SparseSettings,
    SparseSettings,
)

SPARSE_BOOL_IDS = [ATTRIB_BOOL_TRUE, ATTRIB_BOOL_FALSE]


class TestSparseSettings:

    def test_sparse_by_default_defaults_to_false_when_absent(self):
        """When sparseByDefault is absent, __init__ must default self.sparse_by_default to False."""
        ss = _SparseSettings(make_empty_element())

        assert ss.sparse_by_default is False

    @pytest.mark.parametrize(BOOL_FLAG_FIELDS, [
        (ATTRIB_BOOL_TRUE,  True),
        (ATTRIB_BOOL_FALSE, False),
    ], ids=SPARSE_BOOL_IDS)
    def test_sparse_by_default_bool_flag(self, attrib_val, expected):
        """When sparseByDefault is 'true' or 'false', __init__ must set self.sparse_by_default correctly."""
        element = make_mock_element_with_iter({ATTRIB_SPARSE_BY_DEFAULT: attrib_val})
        ss = _SparseSettings(element)
        assert ss.sparse_by_default is expected

    def test_tuple_returns_correct_namedtuple(self):
        """The tuple property must return a SparseSettings namedtuple with the correct sparse_by_default value."""
        element = make_mock_element_with_iter({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_TRUE})
        ss = _SparseSettings(element)

        assert ss.tuple == SparseSettings(sparse_by_default=True)
