#!/usr/bin/env python3
#
## @file
# test_clean_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.clean_command import CleanCommand


class TestCleanCommand:
    """Unit tests for all methods in edkrepo/commands/clean_command.py."""

    WORKSPACE_PATH = '/workspace'
    COMBO_A = 'COMBO_A'
    REPO_ROOT_1 = 'repo1'
    REPO_ROOT_2 = 'repo2'
    DRY_RUN_OUTPUT = 'Would remove file.txt'
    FORCE_OUTPUT = 'Removing file.txt'
    NO_OUTPUT = ''
    COMMAND_NAME = 'clean'
    META_NAME = 'name'
    META_HELP_TEXT = 'help-text'
    META_ARGUMENTS = 'arguments'
    ARG_FORCE = 'force'
    ARG_QUIET = 'quiet'
    ARG_DIRS = 'dirs'
    ARG_INCLUDE_IGNORED = 'include-ignored'

    # helpers

    def _make_args(self, force=False, dirs=False, quiet=False, include_ignored=False):
        args = MagicMock()
        args.force = force
        args.dirs = dirs
        args.quiet = quiet
        args.include_ignored = include_ignored
        return args

    def _setup_workspace(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls,
                         clean_output=None, roots=None):
        if clean_output is None:
            clean_output = self.NO_OUTPUT
        if roots is None:
            roots = [self.REPO_ROOT_1]
        mock_get_workspace_path.return_value = self.WORKSPACE_PATH
        manifest = MagicMock()
        manifest.general_config.current_combo = self.COMBO_A
        sources = []
        for root in roots:
            source = MagicMock()
            source.root = root
            sources.append(source)
        manifest.get_repo_sources.return_value = sources
        mock_get_workspace_manifest.return_value = manifest
        mock_repo = MagicMock()
        mock_repo.git.clean.return_value = clean_output
        mock_repo_cls.return_value = mock_repo
        return mock_repo

    # get_metadata

    def test_get_metadata_returns_expected_structure(self):
        cmd = CleanCommand()
        metadata = cmd.get_metadata()

        assert metadata[self.META_NAME] == self.COMMAND_NAME
        assert self.META_HELP_TEXT in metadata
        arg_names = [
            a[self.META_NAME] if isinstance(a, dict) and self.META_NAME in a else None
            for a in metadata[self.META_ARGUMENTS]
        ]
        assert self.ARG_FORCE in arg_names
        assert self.ARG_QUIET in arg_names
        assert self.ARG_DIRS in arg_names
        assert self.ARG_INCLUDE_IGNORED in arg_names

    # run_command

    @patch('edkrepo.commands.clean_command.ui_functions')
    @patch('edkrepo.commands.clean_command.Repo')
    @patch('edkrepo.commands.clean_command.get_workspace_manifest')
    @patch('edkrepo.commands.clean_command.get_workspace_path')
    def test_dry_run_produces_output_print_called(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, mock_ui):
        mock_repo = self._setup_workspace(mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, clean_output=self.DRY_RUN_OUTPUT)
        args = self._make_args()

        CleanCommand().run_command(args, {})

        mock_repo.git.clean.assert_called_once_with(f=False, d=False, n=True, q=False, x=False)
        mock_ui.print_info_msg.assert_called_once_with(self.DRY_RUN_OUTPUT, header=False)

    @patch('edkrepo.commands.clean_command.ui_functions')
    @patch('edkrepo.commands.clean_command.Repo')
    @patch('edkrepo.commands.clean_command.get_workspace_manifest')
    @patch('edkrepo.commands.clean_command.get_workspace_path')
    def test_force_mode_produces_output_print_called(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, mock_ui):
        mock_repo = self._setup_workspace(mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, clean_output=self.FORCE_OUTPUT)
        args = self._make_args(force=True, dirs=True)

        CleanCommand().run_command(args, {})

        mock_repo.git.clean.assert_called_once_with(f=True, d=True, n=False, q=False, x=False)
        mock_ui.print_info_msg.assert_called_once_with(self.FORCE_OUTPUT, header=False)

    @patch('edkrepo.commands.clean_command.ui_functions')
    @patch('edkrepo.commands.clean_command.Repo')
    @patch('edkrepo.commands.clean_command.get_workspace_manifest')
    @patch('edkrepo.commands.clean_command.get_workspace_path')
    def test_clean_produces_no_output_print_not_called(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, mock_ui):
        self._setup_workspace(mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls)
        args = self._make_args(force=True)

        CleanCommand().run_command(args, {})

        mock_ui.print_info_msg.assert_not_called()

    @patch('edkrepo.commands.clean_command.ui_functions')
    @patch('edkrepo.commands.clean_command.Repo')
    @patch('edkrepo.commands.clean_command.get_workspace_manifest')
    @patch('edkrepo.commands.clean_command.get_workspace_path')
    def test_quiet_and_force_passes_q_true(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, mock_ui):
        mock_repo = self._setup_workspace(mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls)
        args = self._make_args(force=True, quiet=True)

        CleanCommand().run_command(args, {})

        mock_repo.git.clean.assert_called_once_with(f=True, d=False, n=False, q=True, x=False)

    @patch('edkrepo.commands.clean_command.ui_functions')
    @patch('edkrepo.commands.clean_command.Repo')
    @patch('edkrepo.commands.clean_command.get_workspace_manifest')
    @patch('edkrepo.commands.clean_command.get_workspace_path')
    def test_multiple_repos_each_cleaned(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, mock_ui):
        mock_repo = self._setup_workspace(mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls,
                                          roots=[self.REPO_ROOT_1, self.REPO_ROOT_2])
        args = self._make_args(force=True)

        CleanCommand().run_command(args, {})

        assert mock_repo_cls.call_count == 2
        assert mock_repo.git.clean.call_count == 2

    @patch('edkrepo.commands.clean_command.ui_functions')
    @patch('edkrepo.commands.clean_command.Repo')
    @patch('edkrepo.commands.clean_command.get_workspace_manifest')
    @patch('edkrepo.commands.clean_command.get_workspace_path')
    def test_include_ignored_passes_x_true(self, mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls, mock_ui):
        mock_repo = self._setup_workspace(mock_get_workspace_path, mock_get_workspace_manifest, mock_repo_cls)
        args = self._make_args(force=True, include_ignored=True)

        CleanCommand().run_command(args, {})

        mock_repo.git.clean.assert_called_once_with(f=True, d=False, n=False, q=False, x=True)
