#!/usr/bin/env python3
#
## @file
# test_composite_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.edkrepo_command import ColorArgument, PerformanceArgument, VerboseArgument


MODULE_COMPOSITE_COMMAND = 'edkrepo.commands.composite_command'

FAKE_COMMAND_NAME = 'fake-cmd'
FAKE_ALIAS = 'fc'


class TestCompositeCommand:

    @pytest.fixture
    def composite(self):
        """Return a fresh CompositeCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_COMPOSITE_COMMAND)
        return command_mod.CompositeCommand()

    @pytest.fixture
    def mock_cmd(self):
        """Return a mock command with FAKE_COMMAND_NAME and an empty arguments list."""
        cmd = MagicMock()
        cmd.get_metadata.return_value = {'name': FAKE_COMMAND_NAME, 'arguments': []}
        return cmd

    @pytest.fixture
    def mock_init_color_console(self):
        """Patch ui_functions.init_color_console returning (False, False) by default; yields the mock."""
        with patch('{}.ui_functions.init_color_console'.format(MODULE_COMPOSITE_COMMAND),
                   return_value=(False, False)) as mock:
            yield mock

    @staticmethod
    def _add_and_get_metadata(composite, mock_cmd):
        """Add mock_cmd to composite and return the metadata dict for FAKE_COMMAND_NAME."""
        composite.add(mock_cmd)
        return composite.get_metadata(FAKE_COMMAND_NAME)

    @staticmethod
    def _run_and_assert_routing(composite, cmd, command_key, mock_init_color_console):
        """Add cmd, run by command_key, and assert both cmd.run_command and init_color_console were called."""
        composite.add(cmd)
        composite.run_command(command_key, MagicMock(), MagicMock())
        cmd.run_command.assert_called_once()
        mock_init_color_console.assert_called_once()

    def test_get_metadata_returns_metadata_for_registered_command(self, composite, mock_cmd):
        """get_metadata must return the metadata dict for a command that has been added."""
        metadata = self._add_and_get_metadata(composite, mock_cmd)

        assert metadata['name'] == FAKE_COMMAND_NAME

    def test_get_metadata_returns_none_for_unknown_command(self, composite):
        """get_metadata must return None when no command matches the given name."""
        result = composite.get_metadata(FAKE_COMMAND_NAME)

        assert result is None

    def test_run_command_routes_by_name(self, composite, mock_cmd, mock_init_color_console):
        """run_command must delegate to the matching command when called by name."""
        self._run_and_assert_routing(composite, mock_cmd, FAKE_COMMAND_NAME, mock_init_color_console)

    def test_run_command_routes_by_alias(self, composite, mock_init_color_console):
        """run_command must delegate to the matching command when called by alias."""
        cmd_with_alias = MagicMock()
        cmd_with_alias.get_metadata.return_value = {'name': 'other-cmd', 'alias': FAKE_ALIAS, 'arguments': []}

        self._run_and_assert_routing(composite, cmd_with_alias, FAKE_ALIAS, mock_init_color_console)

    def test_run_command_sets_color_attributes_on_args(self, composite, mock_cmd, mock_init_color_console):
        """run_command must set strip_color and convert_ansi on args from init_color_console."""
        mock_init_color_console.return_value = (True, False)
        mock_args = MagicMock()
        composite.add(mock_cmd)

        composite.run_command(FAKE_COMMAND_NAME, mock_args, MagicMock())

        assert mock_args.strip_color is True
        assert mock_args.convert_ansi is False

    def test_command_list_returns_sorted_names(self, composite):
        """command_list must return command names in alphabetical order regardless of insertion order."""
        for name in ('zeta', 'alpha', 'mu'):
            cmd = MagicMock()
            cmd.get_metadata.return_value = {'name': name}
            composite.add(cmd)

        assert composite.command_list() == ['alpha', 'mu', 'zeta']

    @pytest.mark.parametrize('argument_class', [
        pytest.param(PerformanceArgument, id='performance'),
        pytest.param(VerboseArgument, id='verbose'),
        pytest.param(ColorArgument, id='color'),
    ])
    def test_get_metadata_includes_standard_argument(self, composite, mock_cmd, argument_class):
        """get_metadata must include the standard argument class in the metadata arguments list."""
        metadata = self._add_and_get_metadata(composite, mock_cmd)

        assert argument_class in metadata['arguments']
