#!/usr/bin/env python3
#
## @file
# test_ci_index_xml.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.edk_manifest as edk_manifest
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers

PROJECT_XML_A = f'{helpers.PROJECT1_NAME}/{helpers.PROJECT1_NAME}.xml'
ELEMENT_TAG_CI_PROJECT_LIST = 'ProjectList'
CI_DEFAULT_XML_PATH = 'fake_path.xml'
CI_PARAMETRIZE_FIELDS = 'archived_a,archived_b,expected'
ID_MIXED = 'mixed'
ID_ALL_ARCHIVED = 'all_archived'
ID_NONE_ARCHIVED = 'none_archived'


class TestCiIndexXml:

    @pytest.fixture(autouse=True)
    def mock_et(self):
        """Patch ET.ElementTree for every test to prevent real file I/O; yields the mock class."""
        with patch('edkrepo_manifest_parser.edk_manifest.ET.ElementTree') as mock_et_cls:
            mock_tree = MagicMock()
            mock_et_cls.return_value = mock_tree
            mock_tree.getroot.return_value.tag = ELEMENT_TAG_CI_PROJECT_LIST
            mock_tree.iter.return_value = []
            yield mock_et_cls

    @staticmethod
    def _make_mock_project(name, archived, xml_path=None):
        """Build and return a mock _Project with the given name, archived flag, and xmlPath."""
        if xml_path is None:
            xml_path = CI_DEFAULT_XML_PATH
        proj = MagicMock()
        proj.name = name
        proj.archived = archived
        proj.xmlPath = xml_path
        return proj

    @staticmethod
    def _make_two_project_map(archived_a, archived_b):
        """Build a _projects dict with PROJECT1_NAME and PROJECT2_NAME using the given archived flags."""
        return {
            helpers.PROJECT1_NAME: TestCiIndexXml._make_mock_project(helpers.PROJECT1_NAME, archived_a),
            helpers.PROJECT2_NAME: TestCiIndexXml._make_mock_project(helpers.PROJECT2_NAME, archived_b),
        }

    @pytest.fixture
    def ci_instance(self):
        """Return a bare edk_manifest.CiIndexXml instance with an empty _projects map ready for per-test configuration."""
        return edk_manifest.CiIndexXml(helpers.CI_INDEX_PATH)

    @pytest.fixture
    def mock_project_cls(self):
        """Patch _Project for the duration of a test; yields the mock class with no default configuration."""
        with patch('edkrepo_manifest_parser.edk_manifest._Project') as mock:
            yield mock

    def test_init_empty_tree_results_in_empty_project_map(self, mock_project_cls):
        """When the XML tree has no Project elements, _projects must be empty and _Project never called."""
        ci = edk_manifest.CiIndexXml(helpers.CI_INDEX_PATH)

        assert ci._projects == {}
        mock_project_cls.assert_not_called()

    def test_init_single_project_populates_map_with_correct_key(self, mock_project_cls, mock_et):
        """When the tree has one Project element, _projects must contain exactly that entry keyed by name."""
        mock_elem = MagicMock()
        mock_et.return_value.iter.return_value = [mock_elem]
        proj_a = self._make_mock_project(helpers.PROJECT1_NAME, False, PROJECT_XML_A)
        mock_project_cls.return_value = proj_a

        ci = edk_manifest.CiIndexXml(helpers.CI_INDEX_PATH)

        assert ci._projects == {helpers.PROJECT1_NAME: proj_a}
        mock_project_cls.assert_called_once_with(mock_elem)

    def test_init_multiple_projects_all_keyed_by_name(self, mock_project_cls, mock_et):
        """When the tree has multiple Project elements, _projects must contain one entry per project."""
        mock_elem_a, mock_elem_b = MagicMock(), MagicMock()
        mock_et.return_value.iter.return_value = [mock_elem_a, mock_elem_b]
        proj_a = self._make_mock_project(helpers.PROJECT1_NAME, False)
        proj_b = self._make_mock_project(helpers.PROJECT2_NAME, True)
        mock_project_cls.side_effect = [proj_a, proj_b]

        ci = edk_manifest.CiIndexXml(helpers.CI_INDEX_PATH)

        assert ci._projects == {helpers.PROJECT1_NAME: proj_a, helpers.PROJECT2_NAME: proj_b}

    @pytest.mark.parametrize(CI_PARAMETRIZE_FIELDS, [
        pytest.param(False, True, [helpers.PROJECT1_NAME], id=ID_MIXED),
        pytest.param(True, True, [], id=ID_ALL_ARCHIVED),
        pytest.param(False, False, [helpers.PROJECT1_NAME, helpers.PROJECT2_NAME], id=ID_NONE_ARCHIVED),
    ])
    def test_project_list(self, ci_instance, archived_a, archived_b, expected):
        """project_list must return only non-archived project names for each combination of archived flags."""
        ci_instance._projects = self._make_two_project_map(archived_a, archived_b)

        assert set(ci_instance.project_list) == set(expected)

    @pytest.mark.parametrize(CI_PARAMETRIZE_FIELDS, [
        pytest.param(False, True, [helpers.PROJECT2_NAME], id=ID_MIXED),
        pytest.param(False, False, [], id=ID_NONE_ARCHIVED),
        pytest.param(True, True, [helpers.PROJECT1_NAME, helpers.PROJECT2_NAME], id=ID_ALL_ARCHIVED),
    ])
    def test_archived_project_list(self, ci_instance, archived_a, archived_b, expected):
        """archived_project_list must return only archived project names for each combination of archived flags."""
        ci_instance._projects = self._make_two_project_map(archived_a, archived_b)

        assert set(ci_instance.archived_project_list) == set(expected)

    def test_get_project_xml_returns_path_when_project_found(self, ci_instance):
        """When the requested project exists in _projects, get_project_xml must return its xmlPath."""
        ci_instance._projects = {
            helpers.PROJECT1_NAME: self._make_mock_project(helpers.PROJECT1_NAME, False, PROJECT_XML_A),
        }

        assert ci_instance.get_project_xml(helpers.PROJECT1_NAME) == PROJECT_XML_A

    def test_get_project_xml_raises_value_error_when_not_found(self, ci_instance):
        """When the requested project is absent from _projects, get_project_xml must raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ci_instance.get_project_xml(helpers.UNKNOWN)
        assert str(exc_info.value) == edk_manifest.INVALID_PROJECTNAME_ERROR.format(helpers.UNKNOWN)
