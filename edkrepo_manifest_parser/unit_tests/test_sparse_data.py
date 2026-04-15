#!/usr/bin/env python3
#
## @file
# test_sparse_data.py
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

TAG_ALWAYS_INCLUDE = 'AlwaysInclude'
TAG_ALWAYS_EXCLUDE = 'AlwaysExclude'
COMBINATION = 'mycombo'
INCLUDE_VALUE = 'path/to/include'
EXCLUDE_VALUE = 'path/to/exclude'
INCLUDE_MULTI = 'path/a|path/b'
EXCLUDE_MULTI = 'path/c|path/d'
PIPE_SEPARATOR = '|'
FIELD_ALWAYS_INCLUDE = 'always_include'
FIELD_ALWAYS_EXCLUDE = 'always_exclude'
PARAM_LIST_FIELD = 'tag, text_value, field_name, expected'
ID_COMBINATION_PRESENT = 'combination_present'
ID_ALWAYS_INCLUDE_SPLIT = 'always_include_split'
ID_ALWAYS_EXCLUDE_SPLIT = 'always_exclude_split'


class TestSparseData:

    @staticmethod
    def _assert_child_list_field(tag, text_value, field_name, expected):
        """Build a _SparseData element with one child under tag and assert the named list field equals expected."""
        child = helpers.make_text_element(text_value)
        element = helpers.make_mock_element_with_iter({}, {tag: [child]})
        sd = edk_manifest._SparseData(element)
        assert getattr(sd, field_name) == expected

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        sd = edk_manifest._SparseData(helpers.make_empty_element())

        assert sd.combination is None
        assert sd.remote_name is None
        assert sd.always_include == []
        assert sd.always_exclude == []

    @pytest.mark.parametrize(helpers.PARAM_ATTRIB_VAL_FIELD_EXPECTED, [
        pytest.param(helpers.ATTRIB_COMBINATION, COMBINATION, helpers.ATTRIB_COMBINATION, COMBINATION, id=ID_COMBINATION_PRESENT),
        pytest.param(helpers.ATTRIB_REMOTE, helpers.REMOTE_NAME, helpers.FIELD_REMOTE_NAME, helpers.REMOTE_NAME, id=helpers.ID_REMOTE_NAME_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, attrib_key, attrib_val, field_name, expected):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        element = helpers.make_mock_element_with_iter({attrib_key: attrib_val})
        sd = edk_manifest._SparseData(element)
        assert getattr(sd, field_name) == expected

    @pytest.mark.parametrize(PARAM_LIST_FIELD, [
        pytest.param(TAG_ALWAYS_INCLUDE, INCLUDE_VALUE, FIELD_ALWAYS_INCLUDE, [INCLUDE_VALUE], id=FIELD_ALWAYS_INCLUDE),
        pytest.param(TAG_ALWAYS_EXCLUDE, EXCLUDE_VALUE, FIELD_ALWAYS_EXCLUDE, [EXCLUDE_VALUE], id=FIELD_ALWAYS_EXCLUDE),
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
        include_elem = helpers.make_text_element(INCLUDE_VALUE)
        exclude_elem = helpers.make_text_element(EXCLUDE_VALUE)
        element = helpers.make_mock_element_with_iter(
            {helpers.ATTRIB_COMBINATION: COMBINATION, helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME},
            {TAG_ALWAYS_INCLUDE: [include_elem], TAG_ALWAYS_EXCLUDE: [exclude_elem]},
        )
        result = edk_manifest._SparseData(element).tuple

        assert result == edk_manifest.SparseData(
            combination=COMBINATION,
            remote_name=helpers.REMOTE_NAME,
            always_include=[INCLUDE_VALUE],
            always_exclude=[EXCLUDE_VALUE],
        )
