#!/usr/bin/env python3
#
## @file
# test_folder_to_folder_mapping_folder_exclude.py
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


class TestFolderToFolderMappingFolderExclude:

    @pytest.fixture
    def full_folder_exclude(self):
        """Return a _FolderToFolderMappingFolderExclude built from an element with EXCLUDE_PATH set."""
        element = helpers.make_mock_element_with_iter({helpers.ATTRIB_PATH: helpers.EXCLUDE_PATH})
        return edk_manifest._FolderToFolderMappingFolderExclude(element)

    def test_path_defaults_to_none_when_absent(self):
        """When the path attribute is absent, __init__ must set self.path to None."""
        exc = edk_manifest._FolderToFolderMappingFolderExclude(helpers.make_empty_element())

        assert exc.path is None

    def test_path_when_present(self, full_folder_exclude):
        """When the path attribute is present, __init__ must set self.path to its value."""
        assert full_folder_exclude.path == helpers.EXCLUDE_PATH

    def test_tuple_returns_correct_folder_to_folder_mapping_folder_exclude_namedtuple(self, full_folder_exclude):
        """The tuple property must return a FolderToFolderMappingFolderExclude namedtuple with the correct path."""
        assert full_folder_exclude.tuple == edk_manifest.FolderToFolderMappingFolderExclude(path=helpers.EXCLUDE_PATH)
