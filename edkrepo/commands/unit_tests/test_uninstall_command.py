#!/usr/bin/env python3
#
## @file
# test_uninstall_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_UNINSTALL_COMMAND = 'edkrepo.commands.uninstall_command'


class TestUninstallCommand(bt.BaseCommandTest):

    command_module = MODULE_UNINSTALL_COMMAND

    @pytest.fixture
    def uninstall_cmd(self):
        """Return a fresh UninstallCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_UNINSTALL_COMMAND)
        return command_mod.UninstallCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a minimal mock args namespace."""
        return MagicMock()

    @pytest.fixture(autouse=True)
    def mock_handle_uninstall(self):
        """Patch handle_uninstall; always active since run_command calls it unconditionally."""
        with patch('edkrepo.common.install_functions.handle_uninstall') as mock:
            yield mock

    def test_run_command_calls_handle_uninstall_with_remaining_argv(self, uninstall_cmd, mock_args, mock_config, mock_handle_uninstall, mock_sys_exit):
        """run_command must call handle_uninstall with sys.argv[2:]."""
        uninstall_cmd.run_command(mock_args, mock_config)

        mock_handle_uninstall.assert_called_once_with(sys.argv[2:])

    def test_run_command_calls_sys_exit_with_handle_uninstall_result(self, uninstall_cmd, mock_args, mock_config, mock_sys_exit, mock_handle_uninstall):
        """run_command must pass the return value of handle_uninstall directly to sys.exit."""
        uninstall_cmd.run_command(mock_args, mock_config)

        mock_sys_exit.assert_called_once_with(mock_handle_uninstall.return_value)
