#!/usr/bin/env python3
#
## @file
# test_folder_to_folder_mapping_folder.py
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

FIELD_PROJECT1_FOLDER = 'project1_folder'
FIELD_PROJECT2_FOLDER = 'project2_folder'
ID_PROJECT1_FOLDER_PRESENT = 'project1_folder_present'
ID_PROJECT2_FOLDER_PRESENT = 'project2_folder_present'


class TestFolderToFolderMappingFolder:

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        folder = edk_manifest._FolderToFolderMappingFolder(helpers.make_empty_element())

        assert folder.project1_folder is None
        assert folder.project2_folder is None
        assert folder.excludes == []

    @pytest.mark.parametrize(helpers.PARAM_ATTRIB_VALUE_FIELD, [
        pytest.param(helpers.ATTRIB_PROJECT1, helpers.PROJECT1_FOLDER, FIELD_PROJECT1_FOLDER, id=ID_PROJECT1_FOLDER_PRESENT),
        pytest.param(helpers.ATTRIB_PROJECT2, helpers.PROJECT2_FOLDER, FIELD_PROJECT2_FOLDER, id=ID_PROJECT2_FOLDER_PRESENT),
    ])
    def test_init_sets_project_folder_when_present(self, attrib_key, attrib_value, field_name):
        """When a project folder attribute is present, __init__ must set the corresponding field to its value."""
        element = helpers.make_mock_element_with_iter(
            {attrib_key: attrib_value},
            {helpers.TAG_EXCLUDE: []},
        )
        folder = edk_manifest._FolderToFolderMappingFolder(element)
        assert getattr(folder, field_name) == attrib_value

    def test_init_populates_excludes_from_exclude_children(self):
        """When Exclude children are present, __init__ must create a _FolderToFolderMappingFolderExclude for each."""
        exclude_elem = helpers.make_mock_element_with_iter({helpers.ATTRIB_PATH: helpers.EXCLUDE_PATH})
        element = helpers.make_mock_element_with_iter({}, {helpers.TAG_EXCLUDE: [exclude_elem]})
        folder = edk_manifest._FolderToFolderMappingFolder(element)

        assert len(folder.excludes) == 1
        assert folder.excludes[0].path == helpers.EXCLUDE_PATH

    def test_tuple_returns_correct_folder_to_folder_mapping_folder_namedtuple(self):
        """The tuple property must return a FolderToFolderMappingFolder namedtuple with all field values correct."""
        exclude_elem = helpers.make_mock_element_with_iter({helpers.ATTRIB_PATH: helpers.EXCLUDE_PATH})
        element = helpers.make_mock_element_with_iter(
            {helpers.ATTRIB_PROJECT1: helpers.PROJECT1_FOLDER, helpers.ATTRIB_PROJECT2: helpers.PROJECT2_FOLDER},
            {helpers.TAG_EXCLUDE: [exclude_elem]},
        )
        result = edk_manifest._FolderToFolderMappingFolder(element).tuple

        assert result.project1_folder == helpers.PROJECT1_FOLDER
        assert result.project2_folder == helpers.PROJECT2_FOLDER
        assert len(result.excludes) == 1
        assert result.excludes[0].path == helpers.EXCLUDE_PATH
