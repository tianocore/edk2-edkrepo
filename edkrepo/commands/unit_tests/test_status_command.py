#!/usr/bin/env python3
#
## @file
# test_status_command.py
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


MODULE_STATUS_COMMAND = 'edkrepo.commands.status_command'

FAKE_REPO_ROOT = 'project/repo'


class TestStatusCommand(bt.BaseCommandTest):

    command_module = MODULE_STATUS_COMMAND

    @pytest.fixture
    def status_cmd(self):
        """Return a fresh StatusCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_STATUS_COMMAND)
        return command_mod.StatusCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with verbose set to a safe default."""
        args = MagicMock()
        args.verbose = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest with empty repo sources; always active."""
        with patch('{}.get_workspace_manifest'.format(MODULE_STATUS_COMMAND)) as mock:
            mock.return_value.get_repo_sources.return_value = []
            yield mock

    @pytest.fixture
    def run_command_setup(self, mock_get_workspace_manifest):
        """Configure one repo source and patch Repo; yields key mocks as a namespace."""
        fake_source = MagicMock()
        fake_source.root = FAKE_REPO_ROOT
        mock_get_workspace_manifest.return_value.get_repo_sources.return_value = [fake_source]
        with patch('{}.Repo'.format(MODULE_STATUS_COMMAND)) as mock_repo_class:
            yield SimpleNamespace(mock_repo_class=mock_repo_class)

    def test_run_command_queries_repo_sources_from_current_combo(self, status_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_get_workspace_path):
        """get_repo_sources must be called with the current combo from the manifest."""
        status_cmd.run_command(mock_args, mock_config)

        mock_get_workspace_manifest.return_value.get_repo_sources.assert_called_once_with(
            mock_get_workspace_manifest.return_value.general_config.current_combo
        )

    def test_run_command_creates_repo_at_correct_local_path(self, status_cmd, mock_args, mock_config, run_command_setup, mock_get_workspace_path):
        """Repo must be instantiated with the absolute path formed from workspace root and repo root."""
        status_cmd.run_command(mock_args, mock_config)

        run_command_setup.mock_repo_class.assert_called_once_with(
            os.path.join(bt.FAKE_WORKSPACE_PATH, FAKE_REPO_ROOT)
        )

    @pytest.mark.parametrize('mock_name', [
        pytest.param('mock_get_workspace_path', id='get_workspace_path'),
        pytest.param('mock_get_workspace_manifest', id='get_workspace_manifest'),
    ])
    def test_run_command_calls_unconditional_workspace_function(self, status_cmd, mock_args, mock_config, mock_name, request, mock_get_workspace_path):
        """get_workspace_path and get_workspace_manifest must each be called unconditionally."""
        status_cmd.run_command(mock_args, mock_config)

        request.getfixturevalue(mock_name).assert_called_once()
