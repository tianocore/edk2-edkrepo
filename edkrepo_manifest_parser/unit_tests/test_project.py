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
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

ATTRIB_XML_PATH = 'xmlPath'
ELEMENT_TAG_PROJECT = 'Project'
TEST_PROJECT_NAME = 'MyProject'
PROJECT_XML_PATH = 'MyProject/MyProject.xml'
PROJECT_ARCHIVED_FLAG_FIELDS = 'archived_value,expected'
ID_TRUE_LOWER = 'true_lower'
ID_FALSE_LOWER = 'false_lower'
ID_TRUE_UPPER = 'true_upper'


class TestProject:
    @staticmethod
    def _make_full_element(archived=None):
        """Build a mock element with name, xmlPath and an optional archived value."""
        attrib = {
            helpers.ATTRIB_NAME: TEST_PROJECT_NAME,
            ATTRIB_XML_PATH: PROJECT_XML_PATH,
        }
        if archived is not None:
            attrib[helpers.ATTRIB_ARCHIVED] = archived
        return helpers.make_mock_element(attrib, tag=ELEMENT_TAG_PROJECT)

    @staticmethod
    def _assert_required_attrib_key_error(attrib):
        """Call edk_manifest._parse_project_required_attribs with attrib and assert KeyError with the required-attrib message prefix."""
        element = helpers.make_mock_element(attrib, tag=ELEMENT_TAG_PROJECT)
        with pytest.raises(KeyError) as exc_info:
            edk_manifest._parse_project_required_attribs(element)
        assert edk_manifest.REQUIRED_ATTRIB_ERROR_MSG.split(helpers.REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_parse_required_attribs_returns_name_and_xml_path_when_both_present(self):
        """When name and xmlPath are present, must return (name, xmlPath) without raising."""
        element = self._make_full_element()

        name, xml_path = edk_manifest._parse_project_required_attribs(element)

        assert name == TEST_PROJECT_NAME
        assert xml_path == PROJECT_XML_PATH

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent from the element, must raise KeyError with the required-attrib message."""
        self._assert_required_attrib_key_error({ATTRIB_XML_PATH: PROJECT_XML_PATH})

    def test_parse_required_attribs_raises_key_error_when_xml_path_missing(self):
        """When xmlPath is absent from the element, must raise KeyError with the required-attrib message."""
        self._assert_required_attrib_key_error({helpers.ATTRIB_NAME: TEST_PROJECT_NAME})

    def test_init_sets_name_and_xml_path_from_required_attribs(self):
        """When all required attributes are present, __init__ must set name and xmlPath correctly."""
        element = self._make_full_element()

        proj = edk_manifest._Project(element)

        assert proj.name == TEST_PROJECT_NAME
        assert proj.xmlPath == PROJECT_XML_PATH

    @pytest.mark.parametrize(PROJECT_ARCHIVED_FLAG_FIELDS, [
        pytest.param(helpers.ATTRIB_BOOL_TRUE, True, id=ID_TRUE_LOWER),
        pytest.param(helpers.ATTRIB_BOOL_FALSE, False, id=ID_FALSE_LOWER),
        pytest.param(None, False, id=helpers.ID_MISSING),
        pytest.param(helpers.ARCHIVED_TRUE_UPPER, True, id=ID_TRUE_UPPER),
    ])
    def test_init_archived_flag(self, archived_value, expected):
        """Each archived_value must produce the expected boolean on self.archived."""
        element = self._make_full_element(archived=archived_value)
        proj = edk_manifest._Project(element)
        assert proj.archived is expected
