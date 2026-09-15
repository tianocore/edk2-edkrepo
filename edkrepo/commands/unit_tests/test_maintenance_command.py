#!/usr/bin/env python3
#
## @file
# test_maintenance_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_MAINTENANCE_COMMAND = 'edkrepo.commands.maintenance_command'


class TestMaintenanceCommand(bt.BaseCommandTest):

    command_module = MODULE_MAINTENANCE_COMMAND

    @pytest.fixture
    def maintenance_cmd(self):
        """Return a fresh MaintenanceCommande instance for each test."""
        command_mod = importlib.import_module(MODULE_MAINTENANCE_COMMAND)
        return command_mod.MaintenanceCommande()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with no_gc set to False."""
        args = MagicMock()
        args.no_gc = False
        return args

    @pytest.fixture(autouse=True)
    def mock_set_long_path_support(self):
        """Patch set_long_path_support; always active since run_command calls it unconditionally."""
        with patch('{}.set_long_path_support'.format(MODULE_MAINTENANCE_COMMAND)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_clean_git_globalconfig(self):
        """Patch clean_git_globalconfig; always active since run_command calls it unconditionally."""
        with patch('{}.clean_git_globalconfig'.format(MODULE_MAINTENANCE_COMMAND)) as mock:
            yield mock

    @staticmethod
    def _run_no_gc(maintenance_cmd, mock_args, mock_config):
        """Set no_gc=True and execute run_command."""
        mock_args.no_gc = True
        maintenance_cmd.run_command(mock_args, mock_config)

    def test_run_command_always_calls_set_long_path_support(self, maintenance_cmd, mock_args, mock_config, mock_set_long_path_support, mock_print_info_msg):
        """set_long_path_support must be called unconditionally on every run."""
        self._run_no_gc(maintenance_cmd, mock_args, mock_config)

        mock_set_long_path_support.assert_called_once()

    def test_run_command_always_calls_clean_git_globalconfig(self, maintenance_cmd, mock_args, mock_config, mock_clean_git_globalconfig, mock_print_info_msg):
        """clean_git_globalconfig must be called unconditionally on every run."""
        self._run_no_gc(maintenance_cmd, mock_args, mock_config)

        mock_clean_git_globalconfig.assert_called_once()

    def test_run_command_skips_workspace_ops_when_no_gc_is_set(self, maintenance_cmd, mock_args, mock_config, mock_print_info_msg):
        """When --no-gc is set, get_workspace_path must never be called."""
        mock_args.no_gc = True

        with patch('{}.get_workspace_path'.format(MODULE_MAINTENANCE_COMMAND)) as mock_path:
            maintenance_cmd.run_command(mock_args, mock_config)

        mock_path.assert_not_called()

    def test_run_command_skips_gc_when_outside_workspace(self, maintenance_cmd, mock_args, mock_config, mock_print_info_msg):
        """When not in a valid workspace, get_workspace_manifest must never be called."""
        with patch('{}.get_workspace_path'.format(MODULE_MAINTENANCE_COMMAND),
                   side_effect=edkrepo_exception.EdkrepoWorkspaceInvalidException('not in workspace')), \
             patch('{}.get_workspace_manifest'.format(MODULE_MAINTENANCE_COMMAND)) as mock_manifest:
            maintenance_cmd.run_command(mock_args, mock_config)

        mock_manifest.assert_not_called()

    def test_run_command_runs_git_maintenance_for_each_repo_when_in_workspace(self, maintenance_cmd, mock_args, mock_config, mock_print_info_msg):
        """When in a valid workspace with gc enabled, each repo must have reflog expire, gc, and remote prune run."""
        fake_source = MagicMock()
        fake_source.root = 'repo1'
        manifest = MagicMock()
        manifest.get_repo_sources.return_value = [fake_source]

        with patch('{}.get_workspace_path'.format(MODULE_MAINTENANCE_COMMAND), return_value=bt.FAKE_WORKSPACE_PATH), \
             patch('{}.get_workspace_manifest'.format(MODULE_MAINTENANCE_COMMAND), return_value=manifest), \
             patch('{}.Repo'.format(MODULE_MAINTENANCE_COMMAND)) as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            maintenance_cmd.run_command(mock_args, mock_config)

        mock_repo.git.reflog.assert_called_once_with('expire', '--expire=now', '--all')
        mock_repo.git.gc.assert_called_once_with('--aggressive', '--prune=now')
        mock_repo.git.remote.assert_called_once_with('prune', 'origin')
