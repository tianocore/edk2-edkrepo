#!/usr/bin/env python3
#
## @file
# test_log_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_LOG_COMMAND = 'edkrepo.commands.log_command'


class TestLogCommand(bt.BaseCommandTest):

    command_module = MODULE_LOG_COMMAND

    @pytest.fixture
    def log_cmd(self):
        """Return a fresh LogCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_LOG_COMMAND)
        return command_mod.LogCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with number and oneline set to safe defaults."""
        args = MagicMock()
        args.number = None
        args.oneline = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(MODULE_LOG_COMMAND)) as mock:
            mock.return_value = MagicMock()
            yield mock

    @pytest.fixture(autouse=True)
    def mock_sort_commits(self):
        """Patch sort_commits returning an empty list; always active."""
        with patch('{}.sort_commits'.format(MODULE_LOG_COMMAND), return_value=[]) as mock:
            yield mock

    def test_run_command_returns_early_when_number_is_not_integer(self, log_cmd, mock_args, mock_config, mock_sort_commits):
        """When --number is not a valid integer, run_command must return without calling sort_commits."""
        mock_args.number = 'abc'

        log_cmd.run_command(mock_args, mock_config)

        mock_sort_commits.assert_not_called()

    def test_run_command_opens_less_when_available(self, log_cmd, mock_args, mock_config, mock_get_workspace_path, mock_find_less):
        """When find_less returns a valid path, subprocess.Popen must be called to display output."""
        mock_find_less.return_value = ('/usr/bin/less', True)

        with patch('{}.subprocess.Popen'.format(MODULE_LOG_COMMAND)) as mock_popen:
            mock_popen.return_value.communicate.return_value = (None, None)
            log_cmd.run_command(mock_args, mock_config)

        mock_popen.assert_called_once()

    @pytest.mark.parametrize('number, expected_number', [
        pytest.param('5', 5, id='integer_string'),
        pytest.param(None, None, id='none'),
    ])
    def test_run_command_calls_sort_commits_with_correct_number(self, log_cmd, mock_args, mock_config, mock_sort_commits, mock_get_workspace_path, mock_get_workspace_manifest, mock_find_less, number, expected_number):
        """sort_commits must receive the converted number; integer strings are converted to int."""
        mock_args.number = number

        log_cmd.run_command(mock_args, mock_config)

        mock_sort_commits.assert_called_once_with(
            mock_get_workspace_manifest.return_value,
            mock_get_workspace_path.return_value,
            expected_number,
        )
