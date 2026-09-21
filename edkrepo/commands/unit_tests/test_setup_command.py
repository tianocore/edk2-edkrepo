#!/usr/bin/env python3
#
## @file
# test_setup_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_SETUP_COMMAND = 'edkrepo.commands.setup_command'


class TestSetupCommand(bt.BaseCommandTest):

    command_module = MODULE_SETUP_COMMAND

    @pytest.fixture
    def setup_cmd(self):
        """Return a fresh SetupCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_SETUP_COMMAND)
        return command_mod.SetupCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace; run_command does not access any args attributes."""
        return MagicMock()

    @pytest.fixture(autouse=True)
    def mock_handle_setup(self):
        """Patch install_functions.handle_setup; always active to prevent real installation."""
        with patch('edkrepo.common.install_functions.handle_setup') as mock:
            yield mock

    def test_run_command_calls_handle_setup_with_remaining_argv(self, setup_cmd, mock_args, mock_config, mock_handle_setup, mock_sys_exit):
        """handle_setup must be called with sys.argv[2:] to forward the remaining command-line args."""
        setup_cmd.run_command(mock_args, mock_config)

        mock_handle_setup.assert_called_once_with(sys.argv[2:])

    def test_run_command_calls_sys_exit_with_handle_setup_result(self, setup_cmd, mock_args, mock_config, mock_handle_setup, mock_sys_exit):
        """sys.exit must be called with the return value of handle_setup."""
        setup_cmd.run_command(mock_args, mock_config)

        mock_sys_exit.assert_called_once_with(mock_handle_setup.return_value)
