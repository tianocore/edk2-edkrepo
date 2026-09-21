#!/usr/bin/env python3
#
## @file
# test_reset_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_RESET_COMMAND = 'edkrepo.commands.reset_command'

FAKE_REPO_ROOT = 'project/repo'


class TestResetCommand(bt.BaseCommandTest):

    command_module = MODULE_RESET_COMMAND

    @pytest.fixture
    def reset_cmd(self):
        """Return a fresh ResetCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_RESET_COMMAND)
        return command_mod.ResetCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with hard and verbose set to safe defaults."""
        args = MagicMock()
        args.hard = False
        args.verbose = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest with empty repo sources; always active."""
        with patch('{}.get_workspace_manifest'.format(MODULE_RESET_COMMAND)) as mock:
            mock.return_value.get_repo_sources.return_value = []
            yield mock

    @pytest.fixture
    def run_command_setup(self, mock_get_workspace_manifest):
        """Configure one repo source and patch Repo; yields key mocks as a namespace."""
        fake_source = MagicMock()
        fake_source.root = FAKE_REPO_ROOT
        mock_get_workspace_manifest.return_value.get_repo_sources.return_value = [fake_source]
        with patch('{}.Repo'.format(MODULE_RESET_COMMAND)) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            yield SimpleNamespace(mock_repo=mock_repo, mock_repo_class=mock_repo_class)

    def test_run_command_creates_repo_at_correct_local_path(self, reset_cmd, mock_args, mock_config, run_command_setup, mock_get_workspace_path):
        """Repo must be instantiated with the absolute path formed from workspace root and repo root."""
        reset_cmd.run_command(mock_args, mock_config)

        run_command_setup.mock_repo_class.assert_called_once_with(
            os.path.join(bt.FAKE_WORKSPACE_PATH, FAKE_REPO_ROOT)
        )

    @pytest.mark.parametrize('mock_name', [
        pytest.param('mock_get_workspace_path', id='get_workspace_path'),
        pytest.param('mock_get_workspace_manifest', id='get_workspace_manifest'),
    ])
    def test_run_command_calls_unconditional_workspace_function(self, reset_cmd, mock_args, mock_config, mock_name, request, mock_get_workspace_path):
        """get_workspace_path and get_workspace_manifest must each be called unconditionally."""
        reset_cmd.run_command(mock_args, mock_config)

        request.getfixturevalue(mock_name).assert_called_once()

    @pytest.mark.parametrize('hard, expected_working_tree', [
        pytest.param(False, False, id='soft_reset'),
        pytest.param(True, True, id='hard_reset'),
    ])
    def test_run_command_resets_repos_with_correct_working_tree(self, reset_cmd, mock_args, mock_config, run_command_setup, hard, expected_working_tree, mock_get_workspace_path):
        """Each repo source must have its head reset; hard flag controls working_tree."""
        mock_args.hard = hard

        reset_cmd.run_command(mock_args, mock_config)

        run_command_setup.mock_repo.head.reset.assert_called_once_with(working_tree=expected_working_tree)

