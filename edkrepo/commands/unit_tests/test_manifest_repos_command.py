#!/usr/bin/env python3
#
## @file
# test_manifest_repos_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import json
from unittest.mock import MagicMock, patch, call
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.manifest_repos_command import ManifestRepos
from edkrepo.commands.humble import manifest_repos_humble as humble


class TestListManifestRepos:
    """Unit tests for the ManifestRepos._list_manifest_repos method"""

    @pytest.fixture
    def manifest_repos_cmd(self):
        """Provide a ManifestRepos instance for testing"""
        return ManifestRepos()

    @pytest.fixture
    def mock_config(self):
        """Provide a mock config for testing"""
        return {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}

    @pytest.mark.parametrize("cfg_repos,user_cfg_repos,verbose,mock_paths", [
        # Non-verbose tests
        (['repo1', 'repo2'], [], False, []),
        ([], ['user_repo1', 'user_repo2'], False, []),
        ([], [], False, []),
        # Verbose tests
        (['repo1', 'repo2'], [], True, ['/path/to/repo1', '/path/to/repo2']),
        ([], ['user_repo1', 'user_repo2'], True, ['/path/to/user_repo1', '/path/to/user_repo2']),
        (['repo1', 'repo2'], ['user_repo1'], True, ['/path/to/repo1', '/path/to/repo2', '/path/to/user_repo1']),
    ], ids=[
        "non_verbose_cfg_only",
        "non_verbose_user_cfg_only",
        "empty_lists",
        "verbose_cfg_only",
        "verbose_user_cfg_only",
        "verbose_both",
    ])
    @patch('edkrepo.commands.manifest_repos_command.ui_functions.print_info_msg')
    @patch('edkrepo.commands.manifest_repos_command.manifest_repos_maintenance.get_manifest_repo_path')
    def test_list_manifest_repos(self, mock_get_path, mock_print_info, manifest_repos_cmd, 
                                 mock_config, cfg_repos, user_cfg_repos, verbose, mock_paths):
        """Test _list_manifest_repos with various configurations"""
        # Setup mock paths
        if mock_paths:
            mock_get_path.side_effect = mock_paths
        
        # Execute method
        manifest_repos_cmd._list_manifest_repos(cfg_repos, user_cfg_repos, mock_config, verbose)
        
        # Verify print_info_msg calls
        if not cfg_repos and not user_cfg_repos:
            mock_print_info.assert_not_called()
        else:
            for repo in cfg_repos:
                if verbose:
                    path = mock_paths[cfg_repos.index(repo)] if mock_paths else None
                    mock_print_info.assert_any_call(
                        humble.CFG_LIST_ENTRY_VERBOSE.format(repo, os.path.normpath(path)), 
                        header=False
                    )
                else:
                    mock_print_info.assert_any_call(humble.CFG_LIST_ENTRY.format(repo), header=False)
            
            for repo in user_cfg_repos:
                if verbose:
                    path_index = len(cfg_repos) + user_cfg_repos.index(repo)
                    path = mock_paths[path_index] if mock_paths else None
                    mock_print_info.assert_any_call(
                        humble.USER_CFG_LIST_ENTRY_VERBOSE.format(repo, os.path.normpath(path)), 
                        header=False
                    )
                else:
                    mock_print_info.assert_any_call(humble.USER_CFG_LIST_ENTRY.format(repo), header=False)
        
        # Verify get_manifest_repo_path calls
        if verbose and (cfg_repos or user_cfg_repos):
            for repo in cfg_repos:
                mock_get_path.assert_any_call(repo, mock_config)
            for repo in user_cfg_repos:
                mock_get_path.assert_any_call(repo, mock_config)
        else:
            mock_get_path.assert_not_called()


class TestListManifestReposJson:
    """Unit tests for the ManifestRepos._list_manifest_repos_json method"""

    @pytest.fixture
    def manifest_repos_cmd(self):
        """Provide a ManifestRepos instance for testing"""
        return ManifestRepos()

    @pytest.fixture
    def mock_config(self):
        """Provide a mock config for testing"""
        return {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}

    @pytest.mark.parametrize("cfg_repos,user_cfg_repos,mock_paths", [
        (['repo1', 'repo2'], [], ['/path/to/repo1', '/path/to/repo2']),
        ([], ['user_repo1', 'user_repo2'], ['/path/to/user_repo1', '/path/to/user_repo2']),
        (['repo1', 'repo2'], ['user_repo1'], ['/path/to/repo1', '/path/to/repo2', '/path/to/user_repo1']),
        ([], [], []),
    ], ids=[
        "cfg_only",
        "user_cfg_only",
        "both",
        "empty_lists",
    ])
    @patch('builtins.print')
    @patch('edkrepo.commands.manifest_repos_command.manifest_repos_maintenance.get_manifest_repo_path')
    def test_list_manifest_repos_json(self, mock_get_path, mock_print, manifest_repos_cmd,
                                      mock_config, cfg_repos, user_cfg_repos, mock_paths):
        """Test _list_manifest_repos_json with various configurations"""
        # Setup mock paths
        if mock_paths:
            mock_get_path.side_effect = mock_paths
        
        # Execute method
        manifest_repos_cmd._list_manifest_repos_json(cfg_repos, user_cfg_repos, mock_config)
        
        # Build expected JSON output
        expected_output = {
            "edkrepo_cfg": {
                "manifest_repositories": []
            },
            "edkrepo_user_cfg": {
                "manifest_repositories": []
            }
        }
        
        # Add cfg repos to expected output
        for i, repo in enumerate(cfg_repos):
            path = os.path.normpath(mock_paths[i])
            expected_output["edkrepo_cfg"]["manifest_repositories"].append({
                "name": repo,
                "path": path
            })
        
        # Add user cfg repos to expected output
        for i, repo in enumerate(user_cfg_repos):
            path_index = len(cfg_repos) + i
            path = os.path.normpath(mock_paths[path_index])
            expected_output["edkrepo_user_cfg"]["manifest_repositories"].append({
                "name": repo,
                "path": path
            })
        
        # Verify print was called once with expected JSON
        mock_print.assert_called_once_with(json.dumps(expected_output, indent=2))
        
        # Verify the output is valid JSON and matches expected structure
        output_str = mock_print.call_args[0][0]
        output_data = json.loads(output_str)
        assert output_data == expected_output

