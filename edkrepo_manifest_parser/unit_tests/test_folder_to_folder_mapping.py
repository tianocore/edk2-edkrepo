#!/usr/bin/env python3
#
## @file
# test_folder_to_folder_mapping.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
    make_empty_element,
    REMOTE_NAME,
    PROJECT1_NAME,
    PROJECT2_NAME,
)
from edkrepo_manifest_parser.edk_manifest import (
    _FolderToFolderMapping,
)

ATTRIB_PROJECT1             = 'project1'
ATTRIB_PROJECT2             = 'project2'
ATTRIB_REMOTE               = 'remote'
TAG_EXCLUDE                 = 'Exclude'
TAG_FOLDER                  = 'Folder'
TAG_FILE                    = 'File'
FIELD_REMOTE_NAME           = 'remote_name'
PROJECT1_FOLDER             = 'project1/path'
PROJECT2_FOLDER             = 'project2/path'
PARAM_OPTIONAL_ATTRIB       = 'attrib_key, attrib_value, field_name'
ID_PROJECT1_PRESENT         = 'project1_present'
ID_PROJECT2_PRESENT         = 'project2_present'
ID_REMOTE_NAME_PRESENT      = 'remote_name_present'
PARAM_CHILD_SLOT            = 'folder_children_count, file_children_count'
ID_FOLDER_CHILD             = 'folder_child'
ID_FILE_CHILD               = 'file_child'


class TestFolderToFolderMapping:

    @staticmethod
    def _make_folder_child_element(project1=None, project2=None):
        """Build a mock element suitable for use as a Folder/File child with optional project attribs and no Exclude children."""
        attrib = {}
        if project1 is not None:
            attrib[ATTRIB_PROJECT1] = project1
        if project2 is not None:
            attrib[ATTRIB_PROJECT2] = project2
        return make_mock_element_with_iter(attrib, {TAG_EXCLUDE: []})

    @staticmethod
    def _build_mapping_from_children(folder_children, file_children):
        """Build a _FolderToFolderMapping from explicit Folder and File child lists."""
        element = make_mock_element_with_iter(
            {},
            {TAG_FOLDER: folder_children, TAG_FILE: file_children},
        )
        return _FolderToFolderMapping(element)

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        mapping = _FolderToFolderMapping(make_empty_element())

        assert mapping.project1 is None
        assert mapping.project2 is None
        assert mapping.remote_name is None
        assert mapping.folders == []

    @pytest.mark.parametrize(PARAM_OPTIONAL_ATTRIB, [
        pytest.param(ATTRIB_PROJECT1, PROJECT1_NAME, ATTRIB_PROJECT1, id=ID_PROJECT1_PRESENT),
        pytest.param(ATTRIB_PROJECT2, PROJECT2_NAME, ATTRIB_PROJECT2, id=ID_PROJECT2_PRESENT),
        pytest.param(ATTRIB_REMOTE,   REMOTE_NAME,   FIELD_REMOTE_NAME, id=ID_REMOTE_NAME_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, attrib_key, attrib_value, field_name):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        element = make_mock_element_with_iter({attrib_key: attrib_value})
        mapping = _FolderToFolderMapping(element)
        assert getattr(mapping, field_name) == attrib_value

    @pytest.mark.parametrize(PARAM_CHILD_SLOT, [
        pytest.param(1, 0, id=ID_FOLDER_CHILD),
        pytest.param(0, 1, id=ID_FILE_CHILD),
    ])
    def test_init_populates_folders_from_single_child_tag(self, folder_children_count, file_children_count):
        """When one child element is present under either the Folder or File tag, __init__ must add one _FolderToFolderMappingFolder with the correct project folder values."""
        child = self._make_folder_child_element(PROJECT1_FOLDER, PROJECT2_FOLDER)
        mapping = self._build_mapping_from_children(
            [child] * folder_children_count,
            [child] * file_children_count,
        )

        assert len(mapping.folders) == 1
        assert mapping.folders[0].project1_folder == PROJECT1_FOLDER
        assert mapping.folders[0].project2_folder == PROJECT2_FOLDER

    def test_init_combines_folder_and_file_children(self):
        """When both Folder and File children are present, __init__ must create entries for all of them."""
        folder_child = self._make_folder_child_element(PROJECT1_FOLDER)
        file_child = self._make_folder_child_element(PROJECT2_FOLDER)
        mapping = self._build_mapping_from_children([folder_child], [file_child])

        assert len(mapping.folders) == 2

    def test_tuple_returns_correct_folder_to_folder_mapping_namedtuple(self):
        """The tuple property must return a FolderToFolderMapping namedtuple with all field values correct."""
        folder_child = self._make_folder_child_element(PROJECT1_FOLDER, PROJECT2_FOLDER)
        element = make_mock_element_with_iter(
            {ATTRIB_PROJECT1: PROJECT1_NAME, ATTRIB_PROJECT2: PROJECT2_NAME, ATTRIB_REMOTE: REMOTE_NAME},
            {TAG_FOLDER: [folder_child], TAG_FILE: []},
        )
        result = _FolderToFolderMapping(element).tuple

        assert result.project1 == PROJECT1_NAME
        assert result.project2 == PROJECT2_NAME
        assert result.remote_name == REMOTE_NAME
        assert len(result.folders) == 1

