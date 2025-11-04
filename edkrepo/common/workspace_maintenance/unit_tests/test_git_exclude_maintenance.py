#!/usr/bin/env python3
#
## @file
# test_git_exclude_maintenance.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.common.workspace_maintenance.git_exclude_maintenance import write_git_exclude, generate_exclude_pattern

class TestWriteGitExclude:
    REPO_PATH = "/mock/repo"
    EXCLUDE_PATTERN = "*.log"
    EXCLUDE_FILE_PATH = "/mock/repo/.git/info/exclude"

    def test_open_called_with_correct_arguments(self):
        mock_exclude_file = mock_open()
        with patch("builtins.open", mock_exclude_file) as mocked_open, patch("os.path.join", return_value=self.EXCLUDE_FILE_PATH):
            write_git_exclude(self.REPO_PATH, self.EXCLUDE_PATTERN)
            mocked_open.assert_called_once_with(self.EXCLUDE_FILE_PATH, "a")

    def test_write_called_with_correct_pattern(self):
        mock_exclude_file = mock_open()
        with patch("builtins.open", mock_exclude_file) as mocked_open, patch("os.path.join", return_value=self.EXCLUDE_FILE_PATH):
            write_git_exclude(self.REPO_PATH, self.EXCLUDE_PATTERN)
            mocked_open().write.assert_called_once_with(self.EXCLUDE_PATTERN + "\n")

class TestGenerateExcludePattern:
    def test_generate_exclude_pattern(self):
        parent_repo_path = "/home/user/project"
        nested_repo_path = "/home/user/project/subdir/nested_repo"
        expected_pattern = os.path.normpath("subdir/nested_repo/") + os.sep
        result = generate_exclude_pattern(parent_repo_path, nested_repo_path)
        print(result)
        print(expected_pattern)
        assert result == expected_pattern

    def test_generate_exclude_pattern_different_drives(self):
        parent_repo_path = "C:/Users/Project"
        nested_repo_path = "D:/OtherProject/NestedRepo"
        try:
            generate_exclude_pattern(parent_repo_path, nested_repo_path)
            assert False, "Expected ValueError for different drives"
        except ValueError:
            pass  # Test passes if ValueError is raised

    def test_generate_exclude_pattern_no_common_prefix(self):
        parent_repo_path = "/home/user/project"
        nested_repo_path = "/var/log/nested_repo"
        try:
            generate_exclude_pattern(parent_repo_path, nested_repo_path)
            assert False, "Expected ValueError for no common prefix"
        except ValueError as e:
            pass  # Test passes if ValueError is raised