#!/usr/bin/env python3
#
## @file
# test_project.py
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
    ATTRIB_NAME,
    ATTRIB_BOOL_TRUE,
    ATTRIB_BOOL_FALSE,
    REQUIRED_ATTRIB_SPLIT_CHAR,
    ELEMENT_TAG_PROJECT,
    TEST_PROJECT_NAME,
    PROJECT_XML_PATH,
    ARCHIVED_TRUE_UPPER,
    ATTRIB_XML_PATH,
    ATTRIB_ARCHIVED,
    PROJECT_ARCHIVED_FLAG_FIELDS,
    ID_TRUE_LOWER,
    ID_FALSE_LOWER,
    ID_MISSING,
    ID_TRUE_UPPER,
)
from edkrepo_manifest_parser.edk_manifest import _Project, _parse_project_required_attribs, REQUIRED_ATTRIB_ERROR_MSG

ARCHIVED_FLAG_IDS = [ID_TRUE_LOWER, ID_FALSE_LOWER, ID_MISSING, ID_TRUE_UPPER]


class TestProject:
    @staticmethod
    def _make_full_element(archived=None):
        """Build a mock element with name, xmlPath and an optional archived value."""
        attrib = {
            ATTRIB_NAME: TEST_PROJECT_NAME,
            ATTRIB_XML_PATH: PROJECT_XML_PATH,
        }
        if archived is not None:
            attrib[ATTRIB_ARCHIVED] = archived
        return make_mock_element(attrib, tag=ELEMENT_TAG_PROJECT)

    @staticmethod
    def _assert_required_attrib_key_error(attrib):
        """Call _parse_project_required_attribs with attrib and assert KeyError with the required-attrib message prefix."""
        element = make_mock_element(attrib, tag=ELEMENT_TAG_PROJECT)
        with pytest.raises(KeyError) as exc_info:
            _parse_project_required_attribs(element)
        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_parse_required_attribs_returns_name_and_xml_path_when_both_present(self):
        """When name and xmlPath are present, must return (name, xmlPath) without raising."""
        element = self._make_full_element()

        name, xml_path = _parse_project_required_attribs(element)

        assert name == TEST_PROJECT_NAME
        assert xml_path == PROJECT_XML_PATH

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent from the element, must raise KeyError with the required-attrib message."""
        self._assert_required_attrib_key_error({ATTRIB_XML_PATH: PROJECT_XML_PATH})

    def test_parse_required_attribs_raises_key_error_when_xml_path_missing(self):
        """When xmlPath is absent from the element, must raise KeyError with the required-attrib message."""
        self._assert_required_attrib_key_error({ATTRIB_NAME: TEST_PROJECT_NAME})

    def test_init_sets_name_and_xml_path_from_required_attribs(self):
        """When all required attributes are present, __init__ must set name and xmlPath correctly."""
        element = self._make_full_element()

        proj = _Project(element)

        assert proj.name == TEST_PROJECT_NAME
        assert proj.xmlPath == PROJECT_XML_PATH

    @pytest.mark.parametrize(PROJECT_ARCHIVED_FLAG_FIELDS, [
        (ATTRIB_BOOL_TRUE,  True),
        (ATTRIB_BOOL_FALSE, False),
        (None,                 False),
        (ARCHIVED_TRUE_UPPER,  True),
    ], ids=ARCHIVED_FLAG_IDS)
    def test_init_archived_flag(self, archived_value, expected):
        """Each archived_value must produce the expected boolean on self.archived."""
        element = self._make_full_element(archived=archived_value)
        proj = _Project(element)
        assert proj.archived is expected
