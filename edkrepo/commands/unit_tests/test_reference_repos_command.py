#!/usr/bin/env python3
#
## @file
# test_reference_repos_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.humble import reference_repos_humble as humble
from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_REFERENCE_REPOS_COMMAND = 'edkrepo.commands.reference_repos_command'

FAKE_REPO_NAME = 'fake_repo'
FAKE_URL = 'http://example.git'
FAKE_PATH = '/local/path'
ACTION_ADD = 'add'
ACTION_REMOVE = 'remove'


class TestReferenceReposCommand(bt.BaseCommandTest):

    command_module = MODULE_REFERENCE_REPOS_COMMAND

    @pytest.fixture
    def reference_repos_cmd(self):
        """Return a fresh ReferenceRepos instance for each test."""
        command_mod = importlib.import_module(MODULE_REFERENCE_REPOS_COMMAND)
        return command_mod.ReferenceRepos()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with list action and safe defaults."""
        args = MagicMock()
        args.action = 'list'
        args.name = None
        args.url = None
        args.path = None
        return args

    @pytest.fixture
    def mock_list_reference_repos(self):
        """Patch ReferenceRepos._list_reference_repos on the class; yields the mock."""
        command_mod = importlib.import_module(MODULE_REFERENCE_REPOS_COMMAND)
        with patch.object(command_mod.ReferenceRepos, '_list_reference_repos') as mock:
            yield mock

    @staticmethod
    def _run_list_reference_repos(reference_repos_cmd, enabled_for):
        """Build a mock user_cfg with the given enabled_for list, run _list_reference_repos with print_info_msg patched, and return (user_cfg, mock_print)."""
        user_cfg = MagicMock()
        user_cfg.reference_repos_enabled_for = enabled_for

        with patch('{}.ui_functions.print_info_msg'.format(MODULE_REFERENCE_REPOS_COMMAND)) as mock_print:
            reference_repos_cmd._list_reference_repos(user_cfg)

        return user_cfg, mock_print

    def test_run_command_list_action_calls_list_reference_repos(self, reference_repos_cmd, mock_args, mock_config, mock_list_reference_repos):
        """list action must delegate to _list_reference_repos with the user_cfg_file from config."""
        reference_repos_cmd.run_command(mock_args, mock_config)

        mock_list_reference_repos.assert_called_once_with(mock_config['user_cfg_file'])

    @pytest.mark.parametrize('action, enabled_for, expected_method, expected_args', [
        pytest.param(ACTION_ADD, [], 'add_reference_repo', (FAKE_REPO_NAME, FAKE_URL, FAKE_PATH), id='add'),
        pytest.param(ACTION_REMOVE, [FAKE_REPO_NAME], 'remove_reference_repo', (FAKE_REPO_NAME,), id='remove'),
    ])
    def test_run_command_valid_repo_operation_calls_expected_method(self, reference_repos_cmd, mock_args, mock_config, action, enabled_for, expected_method, expected_args):
        """add/remove action for a valid repo must call the matching method on user_cfg_file with the expected arguments."""
        mock_args.action = action
        mock_args.name = FAKE_REPO_NAME
        mock_args.url = FAKE_URL
        mock_args.path = FAKE_PATH
        mock_config['user_cfg_file'].reference_repos_enabled_for = enabled_for

        reference_repos_cmd.run_command(mock_args, mock_config)

        getattr(mock_config['user_cfg_file'], expected_method).assert_called_once_with(*expected_args)

    @pytest.mark.parametrize('enabled_for, populated', [
        pytest.param([FAKE_REPO_NAME], True, id='populated'),
        pytest.param([], False, id='empty'),
    ])
    def test_list_reference_repos(self, reference_repos_cmd, enabled_for, populated):
        """_list_reference_repos must look up each enabled repo's URL/path when populated, or print the no-repos message when empty."""
        user_cfg, mock_print = self._run_list_reference_repos(reference_repos_cmd, enabled_for)

        if populated:
            user_cfg.get_reference_repo_url.assert_called_once_with(FAKE_REPO_NAME)
            user_cfg.get_reference_repo_path.assert_called_once_with(FAKE_REPO_NAME)
        else:
            mock_print.assert_any_call(humble.NO_REPOS_CONFIGURED, header=False)
            user_cfg.get_reference_repo_url.assert_not_called()

    @pytest.mark.parametrize('action', [
        pytest.param(ACTION_ADD, id='add'),
        pytest.param(ACTION_REMOVE, id='remove'),
    ])
    def test_run_command_action_without_name_raises_exception(self, reference_repos_cmd, mock_args, mock_config, action):
        """add or remove action without a name argument must raise EdkrepoInvalidParametersException."""
        mock_args.action = action

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            reference_repos_cmd.run_command(mock_args, mock_config)

    @pytest.mark.parametrize('action, url, path, enabled_for, expected_msg', [
        pytest.param(ACTION_ADD, FAKE_URL, FAKE_PATH, [FAKE_REPO_NAME], humble.ALREADY_EXISTS.format(FAKE_REPO_NAME), id='add_existing'),
        pytest.param(ACTION_REMOVE, FAKE_URL, FAKE_PATH, [], humble.REMOVE_NOT_EXIST.format(FAKE_REPO_NAME), id='remove_nonexistent'),
        pytest.param(ACTION_ADD, None, FAKE_PATH, [], humble.ADD_REQUIRED, id='missing_url'),
        pytest.param(ACTION_ADD, FAKE_URL, None, [], humble.ADD_REQUIRED, id='missing_path'),
    ])
    def test_run_command_raises_for_invalid_repo_operation(self, reference_repos_cmd, mock_args, mock_config, action, url, path, enabled_for, expected_msg):
        """Invalid add/remove operations (existing repo, nonexistent repo, or missing required fields) must raise EdkrepoInvalidParametersException."""
        mock_args.action = action
        mock_args.name = FAKE_REPO_NAME
        mock_args.url = url
        mock_args.path = path
        mock_config['user_cfg_file'].reference_repos_enabled_for = enabled_for

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            reference_repos_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == expected_msg

    @pytest.mark.parametrize('action, setter_name, expected_value', [
        pytest.param('enable', 'set_reference_repos_enable_by_default', True, id='enable'),
        pytest.param('disable', 'set_reference_repos_enable_by_default', False, id='disable'),
        pytest.param('enable-dissociate', 'set_reference_repos_dissociate_by_default', True, id='enable_dissociate'),
        pytest.param('disable-dissociate', 'set_reference_repos_dissociate_by_default', False, id='disable_dissociate'),
    ])
    def test_run_command_toggle_actions_call_setter_with_expected_value(self, reference_repos_cmd, mock_args, mock_config, action, setter_name, expected_value):
        """enable/disable and dissociate toggle actions must call the matching setter with the expected boolean."""
        mock_args.action = action

        reference_repos_cmd.run_command(mock_args, mock_config)

        getattr(mock_config['user_cfg_file'], setter_name).assert_called_once_with(expected_value)
