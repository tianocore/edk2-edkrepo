#!/usr/bin/env python3
#
## @file
# test_clean_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt


MODULE_CLEAN_COMMAND = 'edkrepo.commands.clean_command'


class TestCleanCommand(bt.BaseCommandTest):

    command_module = MODULE_CLEAN_COMMAND

    @pytest.fixture
    def clean_cmd(self):
        """Return a fresh CleanCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_CLEAN_COMMAND)
        return command_mod.CleanCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with all clean flags set to False."""
        args = MagicMock()
        args.force = False
        args.quiet = False
        args.dirs = False
        args.include_ignored = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest returning a manifest with one repo source; always active."""
        with patch('{}.get_workspace_manifest'.format(MODULE_CLEAN_COMMAND)) as mock:
            source = MagicMock()
            source.root = 'repo1'
            manifest = MagicMock()
            manifest.get_repo_sources.return_value = [source]
            mock.return_value = manifest
            yield mock

    @pytest.fixture(autouse=True)
    def mock_repo(self):
        """Patch Repo constructor; always active."""
        with patch('{}.Repo'.format(MODULE_CLEAN_COMMAND)) as mock_cls:
            yield mock_cls

    def test_run_command_calls_git_clean_for_each_repo_source(self, clean_cmd, mock_args, mock_config, mock_repo, mock_get_workspace_manifest, mock_get_workspace_path, mock_print_info_msg):
        """git.clean must be called once for every repo source in the current combo, not just the first."""
        source1 = MagicMock()
        source1.root = 'repo1'
        source2 = MagicMock()
        source2.root = 'repo2'
        mock_get_workspace_manifest.return_value.get_repo_sources.return_value = [source1, source2]

        clean_cmd.run_command(mock_args, mock_config)

        assert mock_repo.return_value.git.clean.call_count == 2

    @pytest.mark.parametrize('clean_output, expect_print', [
        pytest.param('Would remove file.o', True, id='non_empty_output'),
        pytest.param('', False, id='empty_output'),
    ])
    def test_run_command_prints_info_msg_only_when_clean_returns_non_empty_output(self, clean_cmd, mock_args, mock_config, mock_repo, mock_get_workspace_path, mock_print_info_msg, clean_output, expect_print):
        """print_info_msg must be called with the clean output only when git.clean returns a non-empty string."""
        mock_repo.return_value.git.clean.return_value = clean_output

        clean_cmd.run_command(mock_args, mock_config)

        if expect_print:
            mock_print_info_msg.assert_called_once_with(clean_output, header=False)
        else:
            mock_print_info_msg.assert_not_called()

    @pytest.mark.parametrize('force, quiet, dirs, include_ignored, expected_n, expected_q', [
        pytest.param(False, False, False, False, True, False, id='no_force_dry_run'),
        pytest.param(True, False, False, False, False, False, id='force_disables_dry_run'),
        pytest.param(False, True, False, False, True, False, id='quiet_without_force'),
        pytest.param(True, True, False, False, False, True, id='force_and_quiet_enables_q'),
        pytest.param(False, False, True, False, True, False, id='dirs_flag'),
        pytest.param(False, False, False, True, True, False, id='include_ignored_flag'),
    ])
    def test_run_command_git_clean_respects_force_and_quiet_flags(self, clean_cmd, mock_args, mock_config, mock_repo, mock_get_workspace_path, mock_print_info_msg, force, quiet, dirs, include_ignored, expected_n, expected_q):
        """git.clean kwargs must reflect the force, quiet, dirs, and include_ignored flag values from args."""
        mock_args.force = force
        mock_args.quiet = quiet
        mock_args.dirs = dirs
        mock_args.include_ignored = include_ignored

        clean_cmd.run_command(mock_args, mock_config)

        mock_repo.return_value.git.clean.assert_called_once_with(
            f=force, d=dirs, n=expected_n, q=expected_q, x=include_ignored
        )
