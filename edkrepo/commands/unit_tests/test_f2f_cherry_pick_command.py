#!/usr/bin/env python3
#
## @file
# test_f2f_cherry_pick_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import os
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_F2F_CHERRY_PICK_COMMAND = 'edkrepo.commands.f2f_cherry_pick_command'


class TestF2fCherryPickCommand(bt.BaseCommandTest):

    command_module = MODULE_F2F_CHERRY_PICK_COMMAND

    @pytest.fixture
    def f2f_cmd(self):
        """Return a fresh F2fCherryPickCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
        return command_mod.F2fCherryPickCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with all run_command attributes set to safe defaults."""
        args = MagicMock()
        args.list_templates = False
        args.abort = False
        args.__dict__['continue'] = False
        args.__dict__['commit-ish'] = 'abc123def456'
        return args

    @pytest.fixture
    def mock_complete_cherry_pick(self):
        """Patch module-level _complete_cherry_pick; yields the mock."""
        with patch('{}.{}'.format(MODULE_F2F_CHERRY_PICK_COMMAND, '_complete_cherry_pick')) as mock:
            yield mock

    @pytest.fixture
    def mock_list_templates(self):
        """Patch module-level _list_templates; yields the mock."""
        with patch('{}.{}'.format(MODULE_F2F_CHERRY_PICK_COMMAND, '_list_templates')) as mock:
            yield mock

    @staticmethod
    def _run_and_assert_not_complete(f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick):
        """Execute run_command and assert _complete_cherry_pick was not called."""
        f2f_cmd.run_command(mock_args, mock_config)
        mock_complete_cherry_pick.assert_not_called()

    @staticmethod
    def _run_and_assert_complete(f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick):
        """Execute run_command and assert _complete_cherry_pick was called exactly once."""
        f2f_cmd.run_command(mock_args, mock_config)
        mock_complete_cherry_pick.assert_called_once()

    @staticmethod
    def _make_folder_cherry_pick(source):
        """Build a FolderCherryPick with the given source folder and placeholder other fields."""
        command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
        return command_mod.FolderCherryPick(source=source, destination='dest', intermediate='intermediate', source_excludes=[])

    def test_run_command_list_templates_calls_list_templates_and_returns(self, f2f_cmd, mock_args, mock_config, mock_list_templates, mock_complete_cherry_pick):
        """When list_templates is set, _list_templates must be called and the command must return early."""
        mock_args.list_templates = True

        self._run_and_assert_not_complete(f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick)

        mock_list_templates.assert_called_once()

    def test_run_command_raises_when_commit_missing_without_continue_or_abort(self, f2f_cmd, mock_args, mock_config):
        """When no commit is given and neither --continue nor --abort is set, EdkrepoInvalidParametersException must be raised."""
        mock_args.__dict__['commit-ish'] = None

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            f2f_cmd.run_command(mock_args, mock_config)

    def test_run_command_new_cherry_pick_calls_complete_cherry_pick(self, f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick):
        """A new cherry pick (commit provided, no continue/abort) must call _complete_cherry_pick."""
        with patch('{}.{}'.format(MODULE_F2F_CHERRY_PICK_COMMAND, '_start_new_cherry_pick'),
                   return_value=(MagicMock(), [])), \
             patch('{}.{}'.format(MODULE_F2F_CHERRY_PICK_COMMAND, '_prep_new_cherry_pick'),
                   return_value=(MagicMock(), [])):
            self._run_and_assert_complete(f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick)

    def test_run_command_continue_resumes_and_calls_complete_cherry_pick(self, f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick):
        """When --continue is set, _resume_cherry_pick must be called and _complete_cherry_pick must follow."""
        mock_args.__dict__['continue'] = True

        with patch('{}.{}'.format(MODULE_F2F_CHERRY_PICK_COMMAND, '_resume_cherry_pick'),
                   return_value=(MagicMock(), MagicMock(), MagicMock())) as mock_resume:
            self._run_and_assert_complete(f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick)

        mock_resume.assert_called_once()

    def test_run_command_abort_returns_without_calling_complete_cherry_pick(self, f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick):
        """When _resume_cherry_pick raises EdkrepoAbortCherryPickException, run_command must return without calling _complete_cherry_pick."""
        mock_args.abort = True

        with patch('{}.{}'.format(MODULE_F2F_CHERRY_PICK_COMMAND, '_resume_cherry_pick'),
                   side_effect=edkrepo_exception.EdkrepoAbortCherryPickException('aborted')):
            self._run_and_assert_not_complete(f2f_cmd, mock_args, mock_config, mock_complete_cherry_pick)

    def test_cherry_pick_operations_to_include_folder_list_flattens_sources(self):
        """cherry_pick_operations_to_include_folder_list must flatten the source folder of every operation entry."""
        command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
        operation_one = [self._make_folder_cherry_pick('src_a'), self._make_folder_cherry_pick('src_b')]
        operation_two = [self._make_folder_cherry_pick('src_c')]

        result = command_mod.cherry_pick_operations_to_include_folder_list([operation_one, operation_two])

        assert result == ['src_a', 'src_b', 'src_c']

    def test_strip_commit_message_removes_gerrit_trailers_and_converts_change_id(self):
        """strip_commit_message must drop Gerrit trailers and rewrite Change-Id as Original-chg-id."""
        repo = MagicMock()
        commit_obj = MagicMock()
        commit_obj.message = '\n'.join([
            'Subject line',
            '',
            'Body text',
            'Original-chg-id: Iold000',
            'Change-Id: Iabc123',
            'Reviewed-on: https://review.example.com/1',
            'Tested-by: Continuous Integration',
            'Reviewed-by: A Maintainer',
        ])
        repo.commit.return_value = commit_obj
        captured = {}

        def fake_run(command, check):
            """Capture the COMMIT_MESSAGE environment variable set by strip_commit_message."""
            captured['message'] = os.environ['COMMIT_MESSAGE']

        with patch('{}.os.path.isfile'.format(MODULE_F2F_CHERRY_PICK_COMMAND), return_value=True), \
             patch('{}.run'.format(MODULE_F2F_CHERRY_PICK_COMMAND), side_effect=fake_run):
            command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
            command_mod.strip_commit_message('HEAD', repo)

        assert 'Original-chg-id: Iabc123' in captured['message']
        assert 'Iold000' not in captured['message']
        assert 'Change-Id:' not in captured['message']
        assert 'Reviewed-on:' not in captured['message']
        assert 'Tested-by:' not in captured['message']
        assert 'Reviewed-by:' not in captured['message']

    def test_strip_commit_message_appends_source_sha_when_requested(self):
        """strip_commit_message must append the cherry-pick source SHA when append_sha is set."""
        repo = MagicMock()
        commit_obj = MagicMock()
        commit_obj.message = 'Subject line\n\nBody text\n'
        repo.commit.return_value = commit_obj
        captured = {}

        def fake_run(command, check):
            """Capture the COMMIT_MESSAGE environment variable set by strip_commit_message."""
            captured['message'] = os.environ['COMMIT_MESSAGE']

        with patch('{}.os.path.isfile'.format(MODULE_F2F_CHERRY_PICK_COMMAND), return_value=True), \
             patch('{}.run'.format(MODULE_F2F_CHERRY_PICK_COMMAND), side_effect=fake_run):
            command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
            command_mod.strip_commit_message('HEAD', repo, source_commit='deadbeef', append_sha=True)

        assert '(cherry picked from commit deadbeef)' in captured['message']

    @pytest.mark.parametrize('parent_path, child_path, expected', [
        pytest.param('foo/bar', 'foo/bar/baz', True, id='child_inside_parent'),
        pytest.param('foo/bar', 'foo/barbaz', False, id='sibling_with_shared_prefix'),
        pytest.param('foo/bar', 'other/path', False, id='unrelated_paths'),
    ])
    def test_inside_directory(self, parent_path, child_path, expected):
        """inside_directory must report whether child_path is nested within parent_path."""
        command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
        assert command_mod.inside_directory(parent_path, child_path) is expected

    @pytest.mark.parametrize('folder1, folder2, ignored_folders, expected', [
        pytest.param('PlatformA', 'PlatformB', [], 'Platform', id='longest_common_substring'),
        pytest.param('RepoIntel', 'SrcIntel', ['Intel'], '', id='ignored_folder_removes_common_part'),
        pytest.param('abc', 'xyz', [], '', id='no_common_substring'),
    ])
    def test_get_common_folder_name(self, folder1, folder2, ignored_folders, expected):
        """get_common_folder_name must return the longest common substring, honoring ignored folders."""
        command_mod = importlib.import_module(MODULE_F2F_CHERRY_PICK_COMMAND)
        config = {'cfg_file': MagicMock()}
        config['cfg_file'].f2f_cp_ignored_folders = ignored_folders

        assert command_mod.get_common_folder_name(folder1, folder2, config) == expected
