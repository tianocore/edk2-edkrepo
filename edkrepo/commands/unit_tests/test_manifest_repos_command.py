#!/usr/bin/env python3
#
## @file
# test_manifest_repos_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.humble import manifest_repos_humble as humble
from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_MANIFEST_REPOS_COMMAND = 'edkrepo.commands.manifest_repos_command'

FAKE_REPO_NAME = 'fake_repo'
ACTION_ADD = 'add'
ACTION_REMOVE = 'remove'


class TestManifestReposCommand(bt.BaseCommandTest):

    command_module = MODULE_MANIFEST_REPOS_COMMAND

    @pytest.fixture
    def manifest_repos_cmd(self):
        """Return a fresh ManifestRepos instance for each test."""
        command_mod = importlib.import_module(MODULE_MANIFEST_REPOS_COMMAND)
        return command_mod.ManifestRepos()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with list action and safe defaults."""
        args = MagicMock()
        args.action = 'list'
        args.format = None
        args.verbose = False
        args.name = None
        args.branch = None
        args.url = None
        args.path = None
        return args

    @pytest.fixture(autouse=True)
    def mock_list_available_manifest_repos(self):
        """Patch list_available_manifest_repos returning empty lists; always active."""
        with patch(
            '{}.manifest_repos_maintenance.list_available_manifest_repos'.format(
                MODULE_MANIFEST_REPOS_COMMAND
            ),
            return_value=([], [], []),
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_list_manifest_repos(self):
        """Patch ManifestRepos._list_manifest_repos on the class; yields the mock."""
        command_mod = importlib.import_module(MODULE_MANIFEST_REPOS_COMMAND)
        with patch.object(command_mod.ManifestRepos, '_list_manifest_repos') as mock:
            yield mock

    def test_run_command_list_action_calls_list_available_manifest_repos(self, manifest_repos_cmd, mock_args, mock_config, mock_list_available_manifest_repos):
        """list_available_manifest_repos must be called with cfg_file and user_cfg_file from config."""
        manifest_repos_cmd.run_command(mock_args, mock_config)

        mock_list_available_manifest_repos.assert_called_once_with(
            mock_config['cfg_file'], mock_config['user_cfg_file']
        )

    def test_run_command_list_action_text_format_calls_list_manifest_repos(self, manifest_repos_cmd, mock_args, mock_config, mock_list_manifest_repos):
        """list action with no explicit format must route to _list_manifest_repos for text output."""
        manifest_repos_cmd.run_command(mock_args, mock_config)

        mock_list_manifest_repos.assert_called_once()

    def test_run_command_list_action_invalid_format_raises_exception(self, manifest_repos_cmd, mock_args, mock_config):
        """list action with an unrecognised format type must raise EdkrepoInvalidParametersException."""
        mock_args.format = ['badformat']

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            manifest_repos_cmd.run_command(mock_args, mock_config)

    def test_run_command_remove_nonexistent_repo_raises_exception(self, manifest_repos_cmd, mock_args, mock_config):
        """remove of a repo absent from the user cfg manifest_repo_list must raise EdkrepoInvalidParametersException."""
        mock_args.action = ACTION_REMOVE
        mock_args.name = FAKE_REPO_NAME
        mock_config['user_cfg_file'].manifest_repo_list = []

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            manifest_repos_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == humble.REMOVE_NOT_EXIST

    def test_list_manifest_repos_json_builds_structure_with_names_and_paths(self, manifest_repos_cmd, mock_config):
        """_list_manifest_repos_json must return JSON grouping cfg and user-cfg repos, each with its name and normalized path."""
        with patch('{}.manifest_repos_maintenance.get_manifest_repo_path'.format(MODULE_MANIFEST_REPOS_COMMAND),
                   side_effect=lambda repo, config: '/root/{}'.format(repo)):
            result = manifest_repos_cmd._list_manifest_repos_json(['cfg_repo'], ['user_repo'], mock_config)

        parsed = json.loads(result)

        assert parsed['edkrepo_cfg']['manifest_repositories'] == [{'name': 'cfg_repo', 'path': os.path.normpath('/root/cfg_repo')}]
        assert parsed['edkrepo_user_cfg']['manifest_repositories'] == [{'name': 'user_repo', 'path': os.path.normpath('/root/user_repo')}]

    @pytest.mark.parametrize('action', [
        pytest.param(ACTION_ADD, id='add'),
        pytest.param(ACTION_REMOVE, id='remove'),
    ])
    def test_run_command_action_without_name_raises_exception(self, manifest_repos_cmd, mock_args, mock_config, action):
        """add or remove action without a name argument must raise EdkrepoInvalidParametersException."""
        mock_args.action = action

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            manifest_repos_cmd.run_command(mock_args, mock_config)

    @pytest.mark.parametrize('action, expected_msg', [
        pytest.param(ACTION_REMOVE, humble.CANNOT_REMOVE_CFG, id='remove_cfg_repo'),
        pytest.param(ACTION_ADD, humble.ALREADY_EXISTS.format(FAKE_REPO_NAME), id='add_existing_repo'),
    ])
    def test_run_command_raises_for_conflict_with_existing_repos(self, manifest_repos_cmd, mock_args, mock_config, mock_list_available_manifest_repos, action, expected_msg):
        """remove of a cfg repo or add of an existing repo must raise EdkrepoInvalidParametersException."""
        mock_args.action = action
        mock_args.name = FAKE_REPO_NAME
        mock_args.branch = ['main']
        mock_args.url = ['http://example.git']
        mock_args.path = ['/local/path']
        mock_list_available_manifest_repos.return_value = ([FAKE_REPO_NAME], [], [])

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            manifest_repos_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == expected_msg

    @pytest.mark.parametrize('branch, url, path', [
        pytest.param(None, ['http://example.git'], ['/local/path'], id='missing_branch'),
        pytest.param(['main'], None, ['/local/path'], id='missing_url'),
        pytest.param(['main'], ['http://example.git'], None, id='missing_path'),
    ])
    def test_run_command_add_without_required_fields_raises_exception(self, manifest_repos_cmd, mock_args, mock_config, branch, url, path):
        """add action missing any of branch, url, or path must raise EdkrepoInvalidParametersException."""
        mock_args.action = ACTION_ADD
        mock_args.name = FAKE_REPO_NAME
        mock_args.branch = branch
        mock_args.url = url
        mock_args.path = path

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            manifest_repos_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == humble.ADD_REQUIRED
