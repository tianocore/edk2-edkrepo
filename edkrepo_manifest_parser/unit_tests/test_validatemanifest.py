#!/usr/bin/env python3
#
## @file
# test_validatemanifest.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from unittest.mock import MagicMock
from edkrepo_manifest_parser.unit_test_bases import base_tests as bt
import importlib


class TestValidateManifest(bt.BaseTestValidateManifest):

    validation_module = 'edkrepo_manifest_parser.edk_manifest_validation'

    def test_collect_file_validation_results_parsing_succeeds_codename_included(self, mock_validate_manifest):
        """When parsing succeeds and _manifest_xmldata is populated, validate_codename is called and its result is appended."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        xmldata = MagicMock()
        xmldata.project_info.codename = bt.PROJECT1_NAME
        mock_vm = self._setup_file_validator_mock(mock_validate_manifest, bt.PARSE_PASS, xmldata)
        mock_vm.validate_codename.return_value = bt.CODENAME_PASS

        result = validation_mod._collect_file_validation_results(bt.MANIFEST_FILE_PATH)

        assert result == [bt.PARSE_PASS, bt.CODENAME_PASS]
        mock_vm.validate_codename.assert_called_once_with(bt.PROJECT1_NAME)

    def test_collect_file_validation_results_parsing_fails_hardcoded_codename_error(self, mock_validate_manifest):
        """When parsing fails and _manifest_xmldata is None, a hardcoded CODENAME failure tuple is appended without calling validate_codename."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        mock_vm = self._setup_file_validator_mock(mock_validate_manifest, bt.PARSE_FAIL, None)

        result = validation_mod._collect_file_validation_results(bt.MANIFEST_FILE_PATH)

        assert result == [bt.PARSE_FAIL, bt.CODENAME_HARDCODED_FAIL]
        mock_vm.validate_codename.assert_not_called()

    def test_validate_manifestfiles_empty_list_returns_empty_dict(self):
        """When called with an empty list, validate_manifestfiles returns an empty dictionary without invoking any helper."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        result = validation_mod.validate_manifestfiles([])
        assert result == {}

    def test_validate_manifestfiles_single_manifest_calls_helper_once(self, mock_collect_file_results):
        """When the list contains one path, _collect_file_validation_results is called once and the result is keyed by that path."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        mock_collect_file_results.return_value = bt.FILE_RESULTS

        result = validation_mod.validate_manifestfiles([bt.MANIFEST_FILE_PATH])

        mock_collect_file_results.assert_called_once_with(bt.MANIFEST_FILE_PATH)
        assert result == {bt.MANIFEST_FILE_PATH: bt.FILE_RESULTS}

    def test_validate_manifestfiles_multiple_manifests_calls_helper_for_each(self, mock_collect_file_results):
        """When the list contains two paths, _collect_file_validation_results is called once per path and both results are mapped correctly."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        results_a = bt.FILE_RESULTS
        results_b = [bt.PARSE_FAIL, bt.CODENAME_HARDCODED_FAIL]
        mock_collect_file_results.side_effect = [results_a, results_b]

        result = validation_mod.validate_manifestfiles([bt.MANIFEST_FILE_PATH, bt.MANIFEST_PATH_2])

        assert mock_collect_file_results.call_count == bt.TWO_ITEMS
        mock_collect_file_results.assert_any_call(bt.MANIFEST_FILE_PATH)
        mock_collect_file_results.assert_any_call(bt.MANIFEST_PATH_2)
        assert result == {bt.MANIFEST_FILE_PATH: results_a, bt.MANIFEST_PATH_2: results_b}
