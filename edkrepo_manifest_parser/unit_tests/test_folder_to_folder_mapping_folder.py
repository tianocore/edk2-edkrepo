#!/usr/bin/env python3
#
## @file
# test_folder_to_folder_mapping_folder.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import _FolderToFolderMappingFolder
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_empty_element,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
)

ATTRIB_PATH                 = 'path'
ATTRIB_PROJECT1             = 'project1'
ATTRIB_PROJECT2             = 'project2'
TAG_EXCLUDE                 = 'Exclude'
FIELD_PROJECT1_FOLDER       = 'project1_folder'
FIELD_PROJECT2_FOLDER       = 'project2_folder'
PROJECT1_FOLDER             = 'project1/path'
PROJECT2_FOLDER             = 'project2/path'
EXCLUDE_PATH                = 'exclude/some/path'
PARAM_PROJECT_FOLDER        = 'attrib_key, attrib_value, field_name'
ID_PROJECT1_FOLDER_PRESENT  = 'project1_folder_present'
ID_PROJECT2_FOLDER_PRESENT  = 'project2_folder_present'


class TestFolderToFolderMappingFolder:

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        folder = _FolderToFolderMappingFolder(make_empty_element())

        assert folder.project1_folder is None
        assert folder.project2_folder is None
        assert folder.excludes == []

    @pytest.mark.parametrize(PARAM_PROJECT_FOLDER, [
        pytest.param(ATTRIB_PROJECT1, PROJECT1_FOLDER, FIELD_PROJECT1_FOLDER, id=ID_PROJECT1_FOLDER_PRESENT),
        pytest.param(ATTRIB_PROJECT2, PROJECT2_FOLDER, FIELD_PROJECT2_FOLDER, id=ID_PROJECT2_FOLDER_PRESENT),
    ])
    def test_init_sets_project_folder_when_present(self, attrib_key, attrib_value, field_name):
        """When a project folder attribute is present, __init__ must set the corresponding field to its value."""
        element = make_mock_element_with_iter(
            {attrib_key: attrib_value},
            {TAG_EXCLUDE: []},
        )
        folder = _FolderToFolderMappingFolder(element)
        assert getattr(folder, field_name) == attrib_value

    def test_init_populates_excludes_from_exclude_children(self):
        """When Exclude children are present, __init__ must create a _FolderToFolderMappingFolderExclude for each."""
        exclude_elem = make_mock_element_with_iter({ATTRIB_PATH: EXCLUDE_PATH})
        element = make_mock_element_with_iter({}, {TAG_EXCLUDE: [exclude_elem]})
        folder = _FolderToFolderMappingFolder(element)

        assert len(folder.excludes) == 1
        assert folder.excludes[0].path == EXCLUDE_PATH

    def test_tuple_returns_correct_folder_to_folder_mapping_folder_namedtuple(self):
        """The tuple property must return a FolderToFolderMappingFolder namedtuple with all field values correct."""
        exclude_elem = make_mock_element_with_iter({ATTRIB_PATH: EXCLUDE_PATH})
        element = make_mock_element_with_iter(
            {ATTRIB_PROJECT1: PROJECT1_FOLDER, ATTRIB_PROJECT2: PROJECT2_FOLDER},
            {TAG_EXCLUDE: [exclude_elem]},
        )
        result = _FolderToFolderMappingFolder(element).tuple

        assert result.project1_folder == PROJECT1_FOLDER
        assert result.project2_folder == PROJECT2_FOLDER
        assert len(result.excludes) == 1
        assert result.excludes[0].path == EXCLUDE_PATH

