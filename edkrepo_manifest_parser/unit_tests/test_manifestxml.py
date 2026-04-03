#!/usr/bin/env python3
#
## @file
# test_manifestxml.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import re
from unittest.mock import MagicMock

# Add the parent directory to the system path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from edk_manifest import RepoSource, ManifestXml, CiIndexXml, DUPLICATE_TAG_ERROR, INVALID_REPO_PATH_ERROR, NO_PARENT_REPO_ERROR


class TestCiIndexXmlDuplicateProject:

    VALID_INDEX_XML = """<?xml version="1.0" encoding="utf-8"?>
<ProjectList>
  <Project name="ProjectA" xmlPath="ProjectA/ProjectA.xml" archived="false"/>
  <Project name="ProjectB" xmlPath="ProjectB/ProjectB.xml" archived="false"/>
</ProjectList>"""

    DUPLICATE_INDEX_XML = """<?xml version="1.0" encoding="utf-8"?>
<ProjectList>
  <Project name="ProjectA" xmlPath="ProjectA/ProjectA.xml" archived="false"/>
  <Project name="ProjectA" xmlPath="ProjectA/duplicate.xml" archived="false"/>
</ProjectList>"""

    def test_valid_index_xml_parses_successfully(self, tmp_path):
        xml_file = tmp_path / "index.xml"
        xml_file.write_text(self.VALID_INDEX_XML)

        ci = CiIndexXml(str(xml_file))
        assert set(ci.project_list) == {"ProjectA", "ProjectB"}

    def test_duplicate_project_name_raises_key_error(self, tmp_path):
        xml_file = tmp_path / "index.xml"
        xml_file.write_text(self.DUPLICATE_INDEX_XML)

        expected = re.escape(DUPLICATE_TAG_ERROR.format('Project', 'ProjectA'))
        with pytest.raises(KeyError, match=expected):
            CiIndexXml(str(xml_file))


class TestNestedRepo:

    #Mock data for testing get_parent_of_nested_repo() method
    MOCK_REPO_SOURCES = [
        RepoSource(root="parent_repo", remote_name="origin", remote_url="https://example.com/repo.git", branch="main", commit="abc123", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=False)
        ]
    
    MOCK_MANIFEST = MagicMock(spec=ManifestXml)
    MOCK_MANIFEST.get_parent_of_nested_repo = MagicMock(wraps=ManifestXml.get_parent_of_nested_repo)

    def test_get_parent_of_nested_repo_not_nested(self):
        try:
            self.MOCK_MANIFEST.get_parent_of_nested_repo(self, self.MOCK_REPO_SOURCES, "parent_repo")
        except ValueError as e:
            assert str(e) == INVALID_REPO_PATH_ERROR.format("parent_repo")

    def test_get_parent_of_nested_repo_one_level(self):
        result = self.MOCK_MANIFEST.get_parent_of_nested_repo(self, self.MOCK_REPO_SOURCES, "parent_repo/nested_repo")
        assert result.root == "parent_repo"

    def test_get_parent_of_nested_repo_multiple_levels(self):
        result = self.MOCK_MANIFEST.get_parent_of_nested_repo(self, self.MOCK_REPO_SOURCES, "parent_repo/nested_repo/level2")
        assert str(result.root) == "parent_repo"

    def test_get_parent_of_nested_repo_invalid_path(self):
        try:
            self.MOCK_MANIFEST.get_parent_of_nested_repo(self, self.MOCK_REPO_SOURCES, "invalid_path")
        except ValueError as e:
            assert str(e) == INVALID_REPO_PATH_ERROR.format("invalid_path")

    def test_get_parent_of_nested_repo_no_parent_found(self):
        try:
            self.MOCK_MANIFEST.get_parent_of_nested_repo(self, self.MOCK_REPO_SOURCES, "nonexistent_repo/level2")
        except ValueError as e:
            print(e)
            assert str(e) == NO_PARENT_REPO_ERROR.format("nonexistent_repo/level2")

