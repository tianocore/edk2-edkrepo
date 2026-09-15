#!/usr/bin/env python3
#
## @file
# test_sync_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_SYNC_COMMAND = 'edkrepo.commands.sync_command'


class TestSyncCommand(bt.BaseCommandTest):

    command_module = MODULE_SYNC_COMMAND

    @pytest.fixture
    def sync_cmd(self):
        """Return a fresh SyncCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_SYNC_COMMAND)
        return command_mod.SyncCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with update_local_manifest, skip_submodule, fetch, verbose, and override set."""
        args = MagicMock()
        args.update_local_manifest = False
        args.skip_submodule = True
        args.fetch = False
        args.verbose = False
        args.override = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(MODULE_SYNC_COMMAND)) as mock:
            manifest = MagicMock()
            manifest.get_repo_sources.return_value = []
            mock.return_value = manifest
            yield mock

    @pytest.fixture(autouse=True)
    def mock_pull_workspace_manifest_repo(self):
        """Patch pull_workspace_manifest_repo; always active since run_command calls it unconditionally."""
        with patch('{}.pull_workspace_manifest_repo'.format(MODULE_SYNC_COMMAND)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_find_source_manifest_repo(self):
        """Patch find_source_manifest_repo returning None; always active since run_command calls it unconditionally."""
        with patch('{}.find_source_manifest_repo'.format(MODULE_SYNC_COMMAND)) as mock:
            mock.return_value = None
            yield mock

    @pytest.fixture(autouse=True)
    def mock_check_for_new_manifest(self):
        """Patch SyncCommand.__check_for_new_manifest; always active since run_command calls it unconditionally."""
        command_mod = importlib.import_module(MODULE_SYNC_COMMAND)
        with patch.object(command_mod.SyncCommand, '_SyncCommand__check_for_new_manifest') as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_check_submodule_config(self):
        """Patch SyncCommand.__check_submodule_config; always active since run_command calls it unconditionally."""
        command_mod = importlib.import_module(MODULE_SYNC_COMMAND)
        with patch.object(command_mod.SyncCommand, '_SyncCommand__check_submodule_config') as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_clean_git_globalconfig(self):
        """Patch clean_git_globalconfig; always active since run_command calls it unconditionally."""
        with patch('{}.clean_git_globalconfig'.format(MODULE_SYNC_COMMAND)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_manifest_repo_path(self):
        """Patch get_manifest_repo_path; always active since run_command calls it unconditionally."""
        with patch('{}.get_manifest_repo_path'.format(MODULE_SYNC_COMMAND)) as mock:
            yield mock

    def test_run_command_calls_pull_workspace_manifest_repo_with_correct_args(self, sync_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_pull_workspace_manifest_repo, mock_get_workspace_path, mock_check_dirty_repos, mock_sparse_checkout_enabled):
        """run_command must call pull_workspace_manifest_repo with the initial manifest, config entries, and source_manifest_repo arg."""
        sync_cmd.run_command(mock_args, mock_config)

        mock_pull_workspace_manifest_repo.assert_called_once_with(
            mock_get_workspace_manifest.return_value,
            mock_config['cfg_file'],
            mock_config['user_cfg_file'],
            mock_args.source_manifest_repo,
            False,
        )

    def test_run_command_falls_back_to_pull_all_manifest_repos_on_pull_failure(self, sync_cmd, mock_args, mock_config, mock_pull_workspace_manifest_repo, mock_pull_all_manifest_repos, mock_get_workspace_path, mock_check_dirty_repos, mock_sparse_checkout_enabled):
        """When pull_workspace_manifest_repo raises, run_command must fall back to pull_all_manifest_repos."""
        mock_pull_workspace_manifest_repo.side_effect = Exception('network error')

        sync_cmd.run_command(mock_args, mock_config)

        mock_pull_all_manifest_repos.assert_called_once_with(
            mock_config['cfg_file'],
            mock_config['user_cfg_file'],
            False,
        )

    def test_run_command_calls_check_dirty_repos_with_initial_manifest_and_workspace_path(self, sync_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_check_dirty_repos, mock_get_workspace_path, mock_sparse_checkout_enabled):
        """run_command must call check_dirty_repos with the initial manifest and the workspace path."""
        sync_cmd.run_command(mock_args, mock_config)

        mock_check_dirty_repos.assert_called_once_with(
            mock_get_workspace_manifest.return_value,
            bt.FAKE_WORKSPACE_PATH,
        )

    @pytest.mark.parametrize('mock_name, assert_method', [
        pytest.param('mock_get_workspace_path', 'assert_called_once', id='get_workspace_path'),
        pytest.param('mock_get_workspace_manifest', 'assert_called', id='get_workspace_manifest'),
    ])
    def test_run_command_calls_unconditional_workspace_function(self, request, sync_cmd, mock_args, mock_config, mock_name, assert_method, mock_get_workspace_path, mock_check_dirty_repos, mock_sparse_checkout_enabled):
        """run_command must call each unconditional workspace function."""
        sync_cmd.run_command(mock_args, mock_config)

        getattr(request.getfixturevalue(mock_name), assert_method)()
