#!/usr/bin/env python3
#
## @file
# test_sparse_data.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import SparseData
from edkrepo_manifest_parser.edk_manifest import _SparseData
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    REMOTE_NAME,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_empty_element,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_text_element,
)

ATTRIB_COMBINATION          = 'combination'
ATTRIB_REMOTE               = 'remote'
TAG_ALWAYS_INCLUDE          = 'AlwaysInclude'
TAG_ALWAYS_EXCLUDE          = 'AlwaysExclude'
COMBINATION                 = 'mycombo'
INCLUDE_VALUE               = 'path/to/include'
EXCLUDE_VALUE               = 'path/to/exclude'
INCLUDE_MULTI               = 'path/a|path/b'
EXCLUDE_MULTI               = 'path/c|path/d'
PIPE_SEPARATOR              = '|'
FIELD_COMBINATION           = 'combination'
FIELD_REMOTE_NAME           = 'remote_name'
FIELD_ALWAYS_INCLUDE        = 'always_include'
FIELD_ALWAYS_EXCLUDE        = 'always_exclude'
PARAM_OPTIONAL_ATTRIB       = 'attrib_key, attrib_val, field_name, expected'
PARAM_LIST_FIELD            = 'tag, text_value, field_name, expected'
ID_COMBINATION_PRESENT      = 'combination_present'
ID_REMOTE_NAME_PRESENT      = 'remote_name_present'
ID_ALWAYS_INCLUDE           = 'always_include'
ID_ALWAYS_EXCLUDE           = 'always_exclude'
ID_ALWAYS_INCLUDE_SPLIT     = 'always_include_split'
ID_ALWAYS_EXCLUDE_SPLIT     = 'always_exclude_split'


class TestSparseData:

    @staticmethod
    def _assert_child_list_field(tag, text_value, field_name, expected):
        """Build a _SparseData element with one child under tag and assert the named list field equals expected."""
        child = make_text_element(text_value)
        element = make_mock_element_with_iter({}, {tag: [child]})
        sd = _SparseData(element)
        assert getattr(sd, field_name) == expected

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        sd = _SparseData(make_empty_element())

        assert sd.combination is None
        assert sd.remote_name is None
        assert sd.always_include == []
        assert sd.always_exclude == []

    @pytest.mark.parametrize(PARAM_OPTIONAL_ATTRIB, [
        pytest.param(ATTRIB_COMBINATION, COMBINATION, FIELD_COMBINATION, COMBINATION, id=ID_COMBINATION_PRESENT),
        pytest.param(ATTRIB_REMOTE,      REMOTE_NAME, FIELD_REMOTE_NAME, REMOTE_NAME, id=ID_REMOTE_NAME_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, attrib_key, attrib_val, field_name, expected):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        element = make_mock_element_with_iter({attrib_key: attrib_val})
        sd = _SparseData(element)
        assert getattr(sd, field_name) == expected

    @pytest.mark.parametrize(PARAM_LIST_FIELD, [
        pytest.param(TAG_ALWAYS_INCLUDE, INCLUDE_VALUE, FIELD_ALWAYS_INCLUDE, [INCLUDE_VALUE], id=ID_ALWAYS_INCLUDE),
        pytest.param(TAG_ALWAYS_EXCLUDE, EXCLUDE_VALUE, FIELD_ALWAYS_EXCLUDE, [EXCLUDE_VALUE], id=ID_ALWAYS_EXCLUDE),
    ])
    def test_init_populates_list_field_from_single_child(self, tag, text_value, field_name, expected):
        """When one child element is present, __init__ must append its text to the corresponding list field."""
        self._assert_child_list_field(tag, text_value, field_name, expected)

    @pytest.mark.parametrize(PARAM_LIST_FIELD, [
        pytest.param(TAG_ALWAYS_INCLUDE, INCLUDE_MULTI, FIELD_ALWAYS_INCLUDE, INCLUDE_MULTI.split(PIPE_SEPARATOR), id=ID_ALWAYS_INCLUDE_SPLIT),
        pytest.param(TAG_ALWAYS_EXCLUDE, EXCLUDE_MULTI, FIELD_ALWAYS_EXCLUDE, EXCLUDE_MULTI.split(PIPE_SEPARATOR), id=ID_ALWAYS_EXCLUDE_SPLIT),
    ])
    def test_init_splits_pipe_separated_values(self, tag, text_value, field_name, expected):
        """When a child element contains pipe-separated paths, __init__ must add each path as a separate entry."""
        self._assert_child_list_field(tag, text_value, field_name, expected)

    def test_tuple_returns_correct_sparse_data_namedtuple(self):
        """The tuple property must return a SparseData namedtuple with all field values correct."""
        include_elem = make_text_element(INCLUDE_VALUE)
        exclude_elem = make_text_element(EXCLUDE_VALUE)
        element = make_mock_element_with_iter(
            {ATTRIB_COMBINATION: COMBINATION, ATTRIB_REMOTE: REMOTE_NAME},
            {TAG_ALWAYS_INCLUDE: [include_elem], TAG_ALWAYS_EXCLUDE: [exclude_elem]},
        )
        result = _SparseData(element).tuple

        assert result == SparseData(
            combination=COMBINATION,
            remote_name=REMOTE_NAME,
            always_include=[INCLUDE_VALUE],
            always_exclude=[EXCLUDE_VALUE],
        )

