#!/usr/bin/env python3
#
## @file
# test_update_manifest_repo_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_UPDATE_MANIFEST_REPO_COMMAND = 'edkrepo.commands.update_manifest_repo_command'


class TestUpdateManifestRepoCommand(bt.BaseCommandTest):

    command_module = MODULE_UPDATE_MANIFEST_REPO_COMMAND

    @pytest.fixture
    def update_manifest_repo_cmd(self):
        """Return a fresh UpdateManifestRepoCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_UPDATE_MANIFEST_REPO_COMMAND)
        return command_mod.UpdateManifestRepoCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with hard set to False."""
        args = MagicMock()
        args.hard = False
        return args

    @pytest.mark.parametrize('hard', [
        pytest.param(True, id='hard'),
        pytest.param(False, id='not_hard'),
    ])
    def test_run_command_passes_hard_flag_to_pull_all_manifest_repos(self, update_manifest_repo_cmd, mock_args, mock_config, mock_pull_all_manifest_repos, hard):
        """run_command must forward args.hard as reset_hard to pull_all_manifest_repos."""
        mock_args.hard = hard

        update_manifest_repo_cmd.run_command(mock_args, mock_config)

        mock_pull_all_manifest_repos.assert_called_once_with(
            mock_config['cfg_file'],
            mock_config['user_cfg_file'],
            reset_hard=hard,
        )
