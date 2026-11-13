#!/usr/bin/env python3
#
## @file
# test_clone_utilities.py
#
# Copyright (c) 2025 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import RepoSource, ManifestXml
from edkrepo.common import common_repo_functions
from edkrepo.common.clone_utilities import generate_clone_order, calculate_source_manifest_repo_directory

@pytest.mark.parametrize('return_codes, destination_state, expected_attempts, expected_error', [
    ([0], 'absent', 1, None),
    ([128, 0], 'absent', 2, None),
    ([128, 128, 0], 'empty', 3, None),
    ([128, 128, 128], 'absent', 3, common_repo_functions.edkrepo_exception.EdkrepoNotFoundException),
    ([128, 128, 128], 'empty', 3, common_repo_functions.edkrepo_exception.EdkrepoNotFoundException),
    ([128], 'nonempty', 1, common_repo_functions.edkrepo_exception.EdkrepoNotFoundException),
    ([128], 'file', 1, common_repo_functions.edkrepo_exception.EdkrepoNotFoundException),
    ([KeyboardInterrupt()], 'absent', 1, KeyboardInterrupt),
])
def test_clone_single_repository_retries(tmp_path, return_codes, destination_state, expected_attempts, expected_error):
    source = SimpleNamespace(root='repo', remote_url='https://example.com/repo.git',
                             branch='main', commit=None, tag=None, patch_set=None)
    destination = tmp_path / source.root
    if destination_state in ('empty', 'nonempty'):
        destination.mkdir()
    if destination_state == 'nonempty':
        (destination / 'existing.txt').write_text('preserve me')
    elif destination_state == 'file':
        destination.write_text('preserve me')
    results = iter(return_codes)

    def run_clone(command, **kwargs):
        return_code = next(results)
        if isinstance(return_code, BaseException):
            raise return_code
        if return_code == 0:
            destination.mkdir(exist_ok=True)
        return subprocess.CompletedProcess(command, return_code, stdout='')

    with patch.object(common_repo_functions.subprocess, 'run', side_effect=run_clone) as run, \
         patch.object(common_repo_functions.time, 'sleep') as sleep, \
         patch.object(common_repo_functions, 'Repo') as repo, \
         patch.object(common_repo_functions.ui_functions, 'print_info_msg'):
        if expected_error:
            with pytest.raises(expected_error):
                common_repo_functions.clone_single_repository(None, source, str(tmp_path), None)
            repo.assert_not_called()
        else:
            common_repo_functions.clone_single_repository(None, source, str(tmp_path), None)
            repo.assert_called_once_with(str(destination))
        assert run.call_count == expected_attempts
        assert sleep.call_count == expected_attempts - 1
        assert all(call.args == (5,) for call in sleep.call_args_list)
        assert all(call == run.call_args_list[0] for call in run.call_args_list)
    if destination_state == 'nonempty':
        assert (destination / 'existing.txt').read_text() == 'preserve me'
    elif destination_state == 'file':
        assert destination.read_text() == 'preserve me'

class TestGenerateCloneOrder:

    NO_NESTED_MOCK_REPO_SOURCES = [
        RepoSource(root="repo1", remote_name="origin", remote_url="https://example.com/repo1.git", branch="main", commit=None, sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False),
        RepoSource(root="repo2", remote_name="origin", remote_url="https://example.com/repo2.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False)
    ]

    NESTED_MOCK_REPO_SOURCES = [
        RepoSource(root="repo2/repo1", remote_name="origin", remote_url="https://example.com/repo1.git", branch="main", commit=None, sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False),
        RepoSource(root="repo2", remote_name="origin", remote_url="https://example.com/repo2.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False),
        RepoSource(root="repo2/repo1/repo3", remote_name="origin", remote_url="https://example.com/repo3.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False)
    ]

    EXPECTED_NESTED_CLONE_ORDER = [
        RepoSource(root="repo2", remote_name="origin", remote_url="https://example.com/repo2.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False),
        RepoSource(root="repo2/repo1", remote_name="origin", remote_url="https://example.com/repo1.git", branch="main", commit=None, sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False),
        RepoSource(root="repo2/repo1/repo3", remote_name="origin", remote_url="https://example.com/repo3.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False)
    ]

    MOCK_MANIFEST = MagicMock(spec=ManifestXml)
    @staticmethod
    def mock_list_nested_repos(repo_sources_to_search):
        nested = []
        for source in repo_sources_to_search:
            for repo in repo_sources_to_search:
                if repo.root == source.root:
                    continue
                if source.root.startswith(repo.root + "/"):
                    nested.append(source)
                    break
        return nested
    MOCK_MANIFEST.list_nested_repos = MagicMock(side_effect=mock_list_nested_repos)

    def test_generate_clone_order_no_nesting(self):
        clone_order = generate_clone_order(self.MOCK_MANIFEST, self.NO_NESTED_MOCK_REPO_SOURCES)
        assert clone_order == self.NO_NESTED_MOCK_REPO_SOURCES

    def test_generate_clone_order_with_nesting(self):
        clone_order = generate_clone_order(self.MOCK_MANIFEST, self.NESTED_MOCK_REPO_SOURCES)
        print(clone_order)
        assert clone_order == self.EXPECTED_NESTED_CLONE_ORDER

class TestCalculateSourceManifestRepoDirectory:

    MOCK_MANIFEST = MagicMock(spec=ManifestXml)
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG = MagicMock()
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG.source_manifest_repo = 'missing manifest repo'
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG = MagicMock()
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG.source_manifest_repo = 'repo1'
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_USER_CFG = MagicMock()
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_USER_CFG.source_manifest_repo = 'repo2'
    MOCK_ARGS = MagicMock()
    MOCK_ARGS.source_manifest_repo = None
    MOCK_CONFIG = {
        'cfg_file': MagicMock(),
        'user_cfg_file': MagicMock()
    }
    MOCK_CONFIG["cfg_file"].manifest_repo_abs_path.return_value = '/path/to/manifest/repo1'
    MOCK_CONFIG["user_cfg_file"].manifest_repo_abs_path.return_value = '/path/to/manifest/repo2'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_cfg_no_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo1'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo1'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_cfg_source_manifest_repo_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo1'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo1'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_user_cfg_no_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo2'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo2'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_user_cfg_source_manifest_repo_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo2'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_USER_CFG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo2'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_found_manifest_repo_not_in_cfg(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo3'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        assert global_manifest_directory is None

    def test_source_manifest_repo_not_found_source_manifest_repo_flag(self):
        mock_find_source_manifest_repo = MagicMock()
        mock_find_source_manifest_repo.return_value = None

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        assert global_manifest_directory is None

    def test_source_manifest_repo_not_found(self):
        mock_find_source_manifest_repo = MagicMock()
        mock_find_source_manifest_repo.return_value = None

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        assert global_manifest_directory is None