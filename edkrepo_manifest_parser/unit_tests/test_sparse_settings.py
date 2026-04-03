#!/usr/bin/env python3
#
## @file
# test_sparse_settings.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import SparseSettings
from edkrepo_manifest_parser.edk_manifest import _SparseSettings
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
)

ATTRIB_SPARSE_BY_DEFAULT        = 'sparseByDefault'
ATTRIB_BOOL_TRUE                = 'true'
ATTRIB_BOOL_FALSE               = 'false'
PARAM_SPARSE_BY_DEFAULT         = 'attrib, expected'
ID_SPARSE_BY_DEFAULT_ABSENT     = 'sparse_by_default_absent'
ID_SPARSE_BY_DEFAULT_TRUE       = 'sparse_by_default_true'
ID_SPARSE_BY_DEFAULT_FALSE      = 'sparse_by_default_false'


class TestSparseSettings:

    @pytest.mark.parametrize(PARAM_SPARSE_BY_DEFAULT, [
        pytest.param({},                                              False, id=ID_SPARSE_BY_DEFAULT_ABSENT),
        pytest.param({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_TRUE},  True,  id=ID_SPARSE_BY_DEFAULT_TRUE),
        pytest.param({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_FALSE}, False, id=ID_SPARSE_BY_DEFAULT_FALSE),
    ])
    def test_init_sets_sparse_by_default(self, attrib, expected):
        """When sparseByDefault is absent, 'true', or 'false', __init__ must set self.sparse_by_default correctly."""
        element = make_mock_element_with_iter(attrib)
        assert _SparseSettings(element).sparse_by_default is expected

    def test_tuple_returns_correct_sparse_settings_namedtuple(self):
        """The tuple property must return a SparseSettings namedtuple with the correct sparse_by_default value."""
        element = make_mock_element_with_iter({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_TRUE})
        ss = _SparseSettings(element)

        assert ss.tuple == SparseSettings(sparse_by_default=True)
