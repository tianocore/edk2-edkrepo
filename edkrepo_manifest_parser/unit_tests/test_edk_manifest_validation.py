#!/usr/bin/env python3
#
## @file
# test_edk_manifest_validation.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest_validation as emv
import edkrepo.common.humble as humble

MANIFEST_PATH_2 = '/fake/path/manifest2.xml'
MANIFEST_DIR = '/fake/manifest/dir'
CI_INDEX_PATH = '/fake/manifest/dir/CiIndex.xml'
PROJECT_XML_RELATIVE = 'ProjectA/ProjectA.xml'
PROJECT_LIST = [helpers.PROJECT1_NAME, helpers.PROJECT2_NAME]
CANNOT_PROCESS_MSG = 'Cannot process codename validation'
PARSE_PASS = (helpers.RESULT_PARSING, True, None)
PARSE_FAIL = (helpers.RESULT_PARSING, False, helpers.BAD_XML_MSG)
CODENAME_PASS = (helpers.RESULT_CODENAME, True, None)
DUPLICATE_PASS = (helpers.RESULT_DUPLICATE, True, None)
CODENAME_HARDCODED_FAIL = (helpers.RESULT_CODENAME, False, CANNOT_PROCESS_MSG)
FILE_RESULTS = [PARSE_PASS, CODENAME_PASS]
FAILURE_RESULTS = [PARSE_FAIL, CODENAME_PASS]
PROJECT_RESULTS = [PARSE_PASS, CODENAME_PASS, DUPLICATE_PASS]
FILE_NAME_FMT = 'File name: {} '
ERROR_TYPE_FMT = 'Error type: {} '
ERROR_MSG_FMT = 'Error message: {} \n'

VALIDATION_STATUS_FIELDS = 'data, expected'
ID_ALL_PASS = 'all_pass'
ID_ONE_FAIL = 'one_fail'
ID_EMPTY_DICT = 'empty_dict'


class TestEdkManifestValidation:

    @pytest.fixture
    def mock_validate_manifest(self):
        """Patch ValidateManifest for the duration of a test; yields the mock class for per-test configuration."""
        with patch('edkrepo_manifest_parser.edk_manifest_validation.ValidateManifest') as mock:
            yield mock

    @pytest.fixture
    def mock_collect_file_results(self):
        """Patch emv._collect_file_validation_results for the duration of a test; yields the mock for per-test configuration."""
        with patch('edkrepo_manifest_parser.edk_manifest_validation._collect_file_validation_results') as mock:
            yield mock

    @pytest.fixture
    def mock_ci_index_cls(self):
        """Patch CiIndexXml for the duration of a test; yields the mock class for per-test configuration."""
        with patch('edkrepo_manifest_parser.edk_manifest_validation.CiIndexXml') as mock:
            yield mock

    @pytest.fixture
    def mock_resolve_path(self):
        """Patch emv._resolve_project_manifest_path for the duration of a test; yields the mock for per-test configuration."""
        with patch('edkrepo_manifest_parser.edk_manifest_validation._resolve_project_manifest_path') as mock:
            yield mock

    @pytest.fixture
    def mock_collect_project_results(self):
        """Patch emv._collect_project_validation_results for the duration of a test; yields the mock for per-test configuration."""
        with patch('edkrepo_manifest_parser.edk_manifest_validation._collect_project_validation_results') as mock:
            yield mock

    @pytest.fixture
    def mock_print(self):
        """Patch builtins.print for the duration of a test; yields the mock for assertion."""
        with patch('builtins.print') as mock:
            yield mock

    @staticmethod
    def _make_mock_ci_index(mock_ci_index_cls, project_list, archived_project_list):
        """Configure a mock CiIndexXml class so its instance returns the given project and archived lists."""
        mock_ci = mock_ci_index_cls.return_value
        mock_ci.project_list = project_list
        mock_ci.archived_project_list = archived_project_list
        return mock_ci

    @staticmethod
    def _make_mock_project_validator(mock_cls, parse_result):
        """Configure a mock ValidateManifest class so its instance returns the given parse result and passing validations."""
        mock_vm = mock_cls.return_value
        mock_vm.validate_parsing.return_value = parse_result
        mock_vm.validate_codename.return_value = CODENAME_PASS
        mock_vm.validate_case_insensitive_single_match.return_value = DUPLICATE_PASS
        return mock_vm

    @staticmethod
    def _setup_file_validator_mock(mock_validate_manifest, parse_result, xmldata):
        """Configure the ValidateManifest instance mock with the given parse result and _manifest_xmldata; return mock_vm."""
        mock_vm = mock_validate_manifest.return_value
        mock_vm.validate_parsing.return_value = parse_result
        mock_vm._manifest_xmldata = xmldata
        return mock_vm

    @staticmethod
    def _call_collect_project_results(mock_validate_manifest, parse_result):
        """Set up the ValidateManifest mock, invoke emv._collect_project_validation_results, assert three results, and return (mock_vm, result)."""
        mock_vm = TestEdkManifestValidation._make_mock_project_validator(mock_validate_manifest, parse_result)
        result = emv._collect_project_validation_results(helpers.MANIFEST_FILE_PATH, helpers.PROJECT1_NAME, PROJECT_LIST, CI_INDEX_PATH)
        assert len(result) == 3
        return mock_vm, result

    @staticmethod
    def _setup_manifestrepo_mocks(mock_ci_index_cls, mock_collect_project_results):
        """Configure CiIndexXml with one active and one archived project and set collect-project mock to return PROJECT_RESULTS."""
        TestEdkManifestValidation._make_mock_ci_index(mock_ci_index_cls, [helpers.PROJECT1_NAME], [helpers.PROJECT2_NAME])
        mock_collect_project_results.return_value = PROJECT_RESULTS

    @staticmethod
    def _call_print_errors(results):
        """Build a single-entry validation dict keyed by MANIFEST_PATH and invoke emv.print_manifest_errors."""
        emv.print_manifest_errors({helpers.MANIFEST_FILE_PATH: results})

    def test_collect_file_validation_results_parsing_succeeds_codename_included(self, mock_validate_manifest):
        """When parsing succeeds and _manifest_xmldata is populated, validate_codename is called and its result is appended."""
        xmldata = MagicMock()
        xmldata.project_info.codename = helpers.PROJECT1_NAME
        mock_vm = self._setup_file_validator_mock(mock_validate_manifest, PARSE_PASS, xmldata)
        mock_vm.validate_codename.return_value = CODENAME_PASS

        result = emv._collect_file_validation_results(helpers.MANIFEST_FILE_PATH)

        assert result == [PARSE_PASS, CODENAME_PASS]
        mock_vm.validate_codename.assert_called_once_with(helpers.PROJECT1_NAME)

    def test_collect_file_validation_results_parsing_fails_hardcoded_codename_error(self, mock_validate_manifest):
        """When parsing fails and _manifest_xmldata is None, a hardcoded CODENAME failure tuple is appended without calling validate_codename."""
        mock_vm = self._setup_file_validator_mock(mock_validate_manifest, PARSE_FAIL, None)

        result = emv._collect_file_validation_results(helpers.MANIFEST_FILE_PATH)

        assert result == [PARSE_FAIL, CODENAME_HARDCODED_FAIL]
        mock_vm.validate_codename.assert_not_called()

    def test_resolve_project_manifest_path_returns_normalized_joined_path(self):
        """The returned path equals os.path.join(global_manifest_directory, os.path.normpath(get_project_xml(project)))."""
        mock_ci_index = MagicMock()
        mock_ci_index.get_project_xml.return_value = PROJECT_XML_RELATIVE

        result = emv._resolve_project_manifest_path(mock_ci_index, MANIFEST_DIR, helpers.PROJECT1_NAME)

        expected = os.path.join(MANIFEST_DIR, os.path.normpath(PROJECT_XML_RELATIVE))
        assert result == expected
        mock_ci_index.get_project_xml.assert_called_once_with(helpers.PROJECT1_NAME)

    def test_collect_project_validation_results_all_validations_pass(self, mock_validate_manifest):
        """When all three ValidateManifest methods return passing tuples, the result contains exactly three passing entries."""
        _, result = self._call_collect_project_results(mock_validate_manifest, PARSE_PASS)

        assert result[2][0] == helpers.RESULT_DUPLICATE
        assert all(entry[1] is True for entry in result)

    def test_collect_project_validation_results_parsing_fails_three_results_returned(self, mock_validate_manifest):
        """When parsing fails, all three validators still run and three results are returned with the first having False status."""
        mock_vm, result = self._call_collect_project_results(mock_validate_manifest, PARSE_FAIL)

        assert result[0][1] is False
        mock_vm.validate_codename.assert_called_once_with(helpers.PROJECT1_NAME)
        mock_vm.validate_case_insensitive_single_match.assert_called_once_with(
            helpers.PROJECT1_NAME, PROJECT_LIST, CI_INDEX_PATH
        )

    def test_validate_manifestfiles_empty_list_returns_empty_dict(self):
        """When called with an empty list, returns an empty dictionary without invoking any helper."""
        result = emv.validate_manifestfiles([])
        assert result == {}

    def test_validate_manifestfiles_single_manifest_calls_helper_once(self, mock_collect_file_results):
        """When the list contains one path, emv._collect_file_validation_results is called once and the result is keyed by that path."""
        mock_collect_file_results.return_value = FILE_RESULTS

        result = emv.validate_manifestfiles([helpers.MANIFEST_FILE_PATH])

        mock_collect_file_results.assert_called_once_with(helpers.MANIFEST_FILE_PATH)
        assert result == {helpers.MANIFEST_FILE_PATH: FILE_RESULTS}

    def test_validate_manifestfiles_multiple_manifests_calls_helper_for_each(self, mock_collect_file_results):
        """When the list contains two paths, emv._collect_file_validation_results is called once per path and both results are mapped correctly."""
        results_a = FILE_RESULTS
        results_b = [PARSE_FAIL, CODENAME_HARDCODED_FAIL]
        mock_collect_file_results.side_effect = [results_a, results_b]

        result = emv.validate_manifestfiles([helpers.MANIFEST_FILE_PATH, MANIFEST_PATH_2])

        assert mock_collect_file_results.call_count == 2
        mock_collect_file_results.assert_any_call(helpers.MANIFEST_FILE_PATH)
        mock_collect_file_results.assert_any_call(MANIFEST_PATH_2)
        assert result == {helpers.MANIFEST_FILE_PATH: results_a, MANIFEST_PATH_2: results_b}

    def test_validate_manifestrepo_without_archived_only_active_projects_processed(
            self, mock_ci_index_cls, mock_resolve_path, mock_collect_project_results):
        """When verify_archived=False, only active projects are iterated and the dict contains exactly one entry."""
        self._setup_manifestrepo_mocks(mock_ci_index_cls, mock_collect_project_results)
        mock_resolve_path.return_value = helpers.MANIFEST_FILE_PATH

        result = emv.validate_manifestrepo(MANIFEST_DIR, verify_archived=False)

        mock_collect_project_results.assert_called_once()
        assert list(result.keys()) == [helpers.MANIFEST_FILE_PATH]

    def test_validate_manifestrepo_with_archived_active_and_archived_processed(
            self, mock_ci_index_cls, mock_resolve_path, mock_collect_project_results):
        """When verify_archived=True, both active and archived projects are iterated and the dict contains two entries."""
        self._setup_manifestrepo_mocks(mock_ci_index_cls, mock_collect_project_results)
        mock_resolve_path.side_effect = [helpers.MANIFEST_FILE_PATH, MANIFEST_PATH_2]

        result = emv.validate_manifestrepo(MANIFEST_DIR, verify_archived=True)

        assert mock_collect_project_results.call_count == 2
        assert set(result.keys()) == {helpers.MANIFEST_FILE_PATH, MANIFEST_PATH_2}

    @pytest.mark.parametrize(VALIDATION_STATUS_FIELDS, [
        pytest.param({helpers.MANIFEST_FILE_PATH: FILE_RESULTS}, False, id=ID_ALL_PASS),
        pytest.param({helpers.MANIFEST_FILE_PATH: FAILURE_RESULTS}, True, id=ID_ONE_FAIL),
        pytest.param({}, False, id=ID_EMPTY_DICT),
    ])
    def test_get_manifest_validation_status(self, data, expected):
        """Verify all manifests in the dict; parametrized over all-pass, one-fail, and empty-dict scenarios."""
        assert emv.get_manifest_validation_status(data) is expected

    def test_print_manifest_errors_prints_header_and_details_for_failures(self, mock_print):
        """When the dict contains a failing result, VERIFY_ERROR_HEADER and the file/type/message lines are all printed."""
        self._call_print_errors(FAILURE_RESULTS)

        mock_print.assert_any_call(humble.VERIFY_ERROR_HEADER)
        mock_print.assert_any_call(FILE_NAME_FMT.format(helpers.MANIFEST_FILE_PATH))
        mock_print.assert_any_call(ERROR_TYPE_FMT.format(helpers.RESULT_PARSING))
        mock_print.assert_any_call(ERROR_MSG_FMT.format(helpers.BAD_XML_MSG))
        assert mock_print.call_count == 4

    def test_print_manifest_errors_all_passing_only_header_printed(self, mock_print):
        """When all results are passing, only VERIFY_ERROR_HEADER is printed and no error detail lines follow."""
        self._call_print_errors(FILE_RESULTS)

        mock_print.assert_called_once_with(humble.VERIFY_ERROR_HEADER)
