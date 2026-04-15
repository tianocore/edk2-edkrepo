#!/usr/bin/env python3
#
## @file
# test_folder_to_folder_mapping_folder_exclude.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import FolderToFolderMappingFolderExclude
from edkrepo_manifest_parser.edk_manifest import _FolderToFolderMappingFolderExclude
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_empty_element,
)
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_iter,
)

ATTRIB_PATH  = 'path'
EXCLUDE_PATH = 'exclude/some/path'


class TestFolderToFolderMappingFolderExclude:

    @pytest.fixture
    def full_folder_exclude(self):
        """Return a _FolderToFolderMappingFolderExclude built from an element with EXCLUDE_PATH set."""
        element = make_mock_element_with_iter({ATTRIB_PATH: EXCLUDE_PATH})
        return _FolderToFolderMappingFolderExclude(element)

    def test_path_defaults_to_none_when_absent(self):
        """When the path attribute is absent, __init__ must set self.path to None."""
        exc = _FolderToFolderMappingFolderExclude(make_empty_element())

        assert exc.path is None

    def test_path_when_present(self, full_folder_exclude):
        """When the path attribute is present, __init__ must set self.path to its value."""
        assert full_folder_exclude.path == EXCLUDE_PATH

    def test_tuple_returns_correct_folder_to_folder_mapping_folder_exclude_namedtuple(self, full_folder_exclude):
        """The tuple property must return a FolderToFolderMappingFolderExclude namedtuple with the correct path."""
        assert full_folder_exclude.tuple == FolderToFolderMappingFolderExclude(path=EXCLUDE_PATH)

