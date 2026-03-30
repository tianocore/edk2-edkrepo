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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
    make_text_element,
    make_empty_element,
    ATTRIB_REMOTE,
    ATTRIB_COMBINATION,
    REMOTE_NAME,
    TAG_ALWAYS_INCLUDE,
    TAG_ALWAYS_EXCLUDE,
    COMBINATION,
    INCLUDE_VALUE,
    EXCLUDE_VALUE,
    INCLUDE_MULTI,
    PIPE_SEPARATOR,
    FIELD_REMOTE_NAME,
    FIELD_ALWAYS_INCLUDE,
    FIELD_ALWAYS_EXCLUDE,
)
from edkrepo_manifest_parser.edk_manifest import (
    _SparseData,
    SparseData,
)


class TestSparseData:
    @staticmethod
    def _assert_attrib_field(attrib_key, attrib_value, field_name):
        """Build a _SparseData element with a single attribute and assert the named field equals attrib_value."""
        element = make_mock_element_with_iter({attrib_key: attrib_value})
        sd = _SparseData(element)
        assert getattr(sd, field_name) == attrib_value

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

    def test_combination_when_present(self):
        """When the combination attribute is present, __init__ must set COMBINATION to its value."""
        self._assert_attrib_field(ATTRIB_COMBINATION, COMBINATION, ATTRIB_COMBINATION)

    def test_remote_name_when_present(self):
        """When the remote attribute is present, __init__ must set self.remote_name to its value."""
        self._assert_attrib_field(ATTRIB_REMOTE, REMOTE_NAME, FIELD_REMOTE_NAME)

    def test_always_exclude_populated_from_single_child(self):
        """When one AlwaysExclude child is present, __init__ must append its text to self.always_exclude."""
        self._assert_child_list_field(TAG_ALWAYS_EXCLUDE, EXCLUDE_VALUE, FIELD_ALWAYS_EXCLUDE, [EXCLUDE_VALUE])

    def test_always_include_splits_pipe_separated_values(self):
        """When an AlwaysInclude child contains pipe-separated paths, they must each be added separately."""
        self._assert_child_list_field(TAG_ALWAYS_INCLUDE, INCLUDE_MULTI, FIELD_ALWAYS_INCLUDE, INCLUDE_MULTI.split(PIPE_SEPARATOR))

    def test_always_include_populated_from_single_child(self):
        """When one AlwaysInclude child is present, __init__ must append its text to self.always_include."""
        self._assert_child_list_field(TAG_ALWAYS_INCLUDE, INCLUDE_VALUE, FIELD_ALWAYS_INCLUDE, [INCLUDE_VALUE])

    def test_tuple_returns_correct_namedtuple(self):
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
