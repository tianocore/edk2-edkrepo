#!/usr/bin/env python3
#
## @file
# test_validatemanifest.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest_validation as emv

PROJECT1_NAME_LOWER = helpers.PROJECT1_NAME.lower()
MISSING_PROJECT = 'Missing'
ACTUAL_CODENAME = 'ActualCodename'
HELLO_UPPER = 'Hello'
STR_FOO = 'foo'
STR_BAR = 'bar'
CASE_EQUAL_FIELDS = 'str1,str2,expected'
ID_SAME_CASE = 'same_case'
ID_DIFF_CASE = 'different_case'
ID_UNEQUAL = 'unequal'
SINGLE_MATCH_FAIL_FIELDS = 'project,project_list,expected_msg'
ID_MULTIPLE_MATCHES = 'multiple_matches'


class TestValidateManifest:

    @pytest.fixture
    def mock_manifest_xml(self):
        """Patch ManifestXml; yields a configured mock class whose return_value is a fresh MagicMock instance exposed as mock_cls.instance."""
        with patch('edkrepo_manifest_parser.edk_manifest_validation.ManifestXml') as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            mock_cls.instance = instance
            yield mock_cls

    @pytest.fixture
    def vm(self):
        """Return a emv.ValidateManifest instance initialized with MANIFEST_PATH."""
        return emv.ValidateManifest(helpers.MANIFEST_PATH)

    @staticmethod
    def _make_obj_with_codename(codename):
        """Build a emv.ValidateManifest instance whose _manifest_xmldata reports the given codename."""
        obj = emv.ValidateManifest(helpers.MANIFEST_PATH)
        mock_data = MagicMock()
        mock_data.project_info.codename = codename
        obj._manifest_xmldata = mock_data
        return obj

    @staticmethod
    def _call_validate_codename(codename, project):
        """Build a emv.ValidateManifest with the given codename and return the result of validate_codename."""
        return TestValidateManifest._make_obj_with_codename(codename).validate_codename(project)

    @staticmethod
    def _call_single_match(vm, project, project_list):
        """Call validate_case_insensitive_single_match with CI_INDEX_PATH as the index filename."""
        return vm.validate_case_insensitive_single_match(project, project_list, helpers.CI_INDEX_PATH)

    @staticmethod
    def _assert_parsing_result(vm, expected_result, expected_xmldata):
        """Call validate_parsing on vm and assert both the result tuple and _manifest_xmldata."""
        result = vm.validate_parsing()
        assert result == expected_result
        assert vm._manifest_xmldata is expected_xmldata

    @staticmethod
    def _assert_try_parse_result(expected_xmldata, expected_error):
        """Call emv._try_parse_manifest_xml and assert both returned values."""
        xmldata, error = emv._try_parse_manifest_xml(helpers.MANIFEST_PATH)
        assert xmldata is expected_xmldata
        assert error is expected_error

    def test_try_parse_manifest_xml_returns_xmldata_on_success(self, mock_manifest_xml):
        """When ManifestXml succeeds, must return (xmldata, None) with the constructed instance."""
        self._assert_try_parse_result(mock_manifest_xml.instance, None)

    def test_try_parse_manifest_xml_returns_none_and_exception_on_failure(self, mock_manifest_xml):
        """When ManifestXml raises, must return (None, exception) with the original exception."""
        exc = TypeError(helpers.BAD_XML_MSG)
        mock_manifest_xml.side_effect = exc
        self._assert_try_parse_result(None, exc)

    def test_validate_parsing_success(self, vm, mock_manifest_xml):
        """When ManifestXml succeeds, must return ("PARSING", True, None) and set _manifest_xmldata."""
        self._assert_parsing_result(vm, (helpers.RESULT_PARSING, True, None), mock_manifest_xml.instance)

    def test_validate_parsing_failure(self, vm, mock_manifest_xml):
        """When ManifestXml raises, must return ("PARSING", False, error) and set _manifest_xmldata to None."""
        exc = TypeError(helpers.BAD_XML_MSG)
        mock_manifest_xml.side_effect = exc
        self._assert_parsing_result(vm, (helpers.RESULT_PARSING, False, exc), None)

    def test_validate_codename_fails_when_no_manifest_data(self, vm):
        """When _manifest_xmldata is None, must return ('CODENAME', False, message containing the project name)."""
        vm._manifest_xmldata = None

        result = vm.validate_codename(helpers.PROJECT1_NAME)

        assert result[0] == helpers.RESULT_CODENAME
        assert result[1] is False
        assert helpers.PROJECT1_NAME in str(result[2])

    def test_validate_codename_succeeds_when_codename_matches(self):
        """When _manifest_xmldata.project_info.codename equals the project, must return ('CODENAME', True, None)."""
        result = self._call_validate_codename(helpers.PROJECT1_NAME, helpers.PROJECT1_NAME)

        assert result == (helpers.RESULT_CODENAME, True, None)

    def test_validate_codename_fails_when_codename_mismatches(self):
        """When _manifest_xmldata.project_info.codename differs from the project, must return ('CODENAME', False, message)."""
        result = self._call_validate_codename(ACTUAL_CODENAME, helpers.PROJECT1_NAME)

        assert result[0] == helpers.RESULT_CODENAME
        assert result[1] is False
        assert result[2] is not None

    def test_validate_case_insensitive_single_match_exactly_one_match(self, vm):
        """When exactly one case-insensitive match is found, must return ('DUPLICATE', True, None)."""
        result = self._call_single_match(vm, helpers.PROJECT1_NAME, [helpers.PROJECT1_NAME, helpers.PROJECT2_NAME])

        assert result == (helpers.RESULT_DUPLICATE, True, None)

    @pytest.mark.parametrize(SINGLE_MATCH_FAIL_FIELDS, [
        pytest.param(MISSING_PROJECT, [helpers.PROJECT1_NAME, helpers.PROJECT2_NAME], MISSING_PROJECT, id=helpers.ID_NO_MATCH),
        pytest.param(helpers.PROJECT1_NAME, [helpers.PROJECT1_NAME, PROJECT1_NAME_LOWER], helpers.PROJECT1_NAME, id=ID_MULTIPLE_MATCHES),
    ])
    def test_validate_case_insensitive_single_match_fails(self, vm, project, project_list, expected_msg):
        """Must return ('DUPLICATE', False, message) when no match or multiple matches are found."""
        result = self._call_single_match(vm, project, project_list)

        assert result[0] == helpers.RESULT_DUPLICATE
        assert result[1] is False
        assert expected_msg in str(result[2])

    def test_list_entries_returns_matching_entries(self, vm):
        """When the project list contains case-insensitive matches, must return all of them."""
        project_list = [helpers.PROJECT1_NAME, PROJECT1_NAME_LOWER, helpers.PROJECT2_NAME]

        result = vm.list_entries(PROJECT1_NAME_LOWER, project_list)

        assert helpers.PROJECT1_NAME in result
        assert PROJECT1_NAME_LOWER in result
        assert helpers.PROJECT2_NAME not in result

    def test_list_entries_returns_empty_when_no_matches(self, vm):
        """When no entries match the project name, must return an empty list."""
        result = vm.list_entries(MISSING_PROJECT, [helpers.PROJECT1_NAME, helpers.PROJECT2_NAME])

        assert result == []

    @pytest.mark.parametrize(CASE_EQUAL_FIELDS, [
        pytest.param(helpers.HELLO, helpers.HELLO, True, id=ID_SAME_CASE),
        pytest.param(HELLO_UPPER, helpers.HELLO, True, id=ID_DIFF_CASE),
        pytest.param(STR_FOO, STR_BAR, False, id=ID_UNEQUAL),
    ])
    def test_case_insensitive_equal(self, vm, str1, str2, expected):
        """Must return True when str1 and str2 are case-insensitively equal, False otherwise."""
        assert vm.case_insensitive_equal(str1, str2) is expected
