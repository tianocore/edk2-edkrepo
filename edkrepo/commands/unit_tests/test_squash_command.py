#!/usr/bin/env python3
#
## @file
# test_squash_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.humble import squash_humble as humble
from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_SQUASH_COMMAND = 'edkrepo.commands.squash_command'

FAKE_REPO_PATH = '/fake/repo/path'
FAKE_NEW_BRANCH = 'feature/new-pr'
EXISTING_BRANCH_NAME = 'existing_branch'


class TestSquashCommand(bt.BaseCommandTest):

    command_module = MODULE_SQUASH_COMMAND

    @pytest.fixture
    def squash_cmd(self):
        """Return a fresh SquashCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_SQUASH_COMMAND)
        return command_mod.SquashCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with squash arguments set via __dict__ for hyphenated names."""
        args = MagicMock()
        args.__dict__['commit-ish'] = 'HEAD~3..HEAD'
        args.__dict__['new-branch'] = FAKE_NEW_BRANCH
        args.__dict__['oneline'] = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_git_repo_root(self):
        """Patch get_git_repo_root returning FAKE_REPO_PATH; always active."""
        with patch('{}.get_git_repo_root'.format(MODULE_SQUASH_COMMAND),
                   return_value=FAKE_REPO_PATH) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_repo_class(self):
        """Patch Repo; always active since run_command instantiates it unconditionally."""
        with patch('{}.Repo'.format(MODULE_SQUASH_COMMAND)) as mock:
            yield mock

    @pytest.fixture
    def mock_branch_name_exists(self):
        """Patch branch_name_exists returning True; request explicitly to short-circuit run_command."""
        with patch('{}.branch_name_exists'.format(MODULE_SQUASH_COMMAND),
                   return_value=True) as mock:
            yield mock

    @staticmethod
    def _run_and_expect_invalid_params(squash_cmd, mock_args, mock_config):
        """Execute run_command and assert EdkrepoInvalidParametersException is raised."""
        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            squash_cmd.run_command(mock_args, mock_config)

    def test_run_command_calls_get_git_repo_root(self, squash_cmd, mock_args, mock_config, mock_get_git_repo_root, mock_branch_name_exists):
        """get_git_repo_root must be called unconditionally to locate the repository root."""
        self._run_and_expect_invalid_params(squash_cmd, mock_args, mock_config)

        mock_get_git_repo_root.assert_called_once()

    def test_run_command_creates_repo_at_git_root_path(self, squash_cmd, mock_args, mock_config, mock_repo_class, mock_branch_name_exists):
        """Repo must be instantiated with the path returned by get_git_repo_root."""
        self._run_and_expect_invalid_params(squash_cmd, mock_args, mock_config)

        mock_repo_class.assert_called_once_with(FAKE_REPO_PATH)

    def test_run_command_branch_already_exists_raises_exception_and_names_branch(self, squash_cmd, mock_args, mock_config, mock_branch_name_exists):
        """When the target branch name already exists, EdkrepoInvalidParametersException must be raised with the branch name."""
        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            squash_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == humble.BRANCH_EXISTS.format(FAKE_NEW_BRANCH)

    def test_run_command_branch_exists_check_uses_new_branch_and_repo(self, squash_cmd, mock_args, mock_config, mock_branch_name_exists, mock_repo_class):
        """branch_name_exists must be called with the new-branch arg and the Repo instance."""
        self._run_and_expect_invalid_params(squash_cmd, mock_args, mock_config)

        mock_branch_name_exists.assert_called_once_with(FAKE_NEW_BRANCH, mock_repo_class.return_value)

    def test_run_command_single_commit_raises_multiple_commits_required(self, squash_cmd, mock_args, mock_config, mock_branch_name_exists):
        """When commit-ish resolves to a single commit, EdkrepoInvalidParametersException must name that a range is required."""
        mock_branch_name_exists.return_value = False

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            squash_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == humble.MULTIPLE_COMMITS_REQUIRED

    @pytest.mark.parametrize('branch_name, expected', [
        pytest.param(EXISTING_BRANCH_NAME, True, id='branch_exists'),
        pytest.param('missing_branch', False, id='branch_missing'),
    ])
    def test_branch_name_exists_reports_whether_name_matches_an_existing_head(self, branch_name, expected):
        """branch_name_exists must return True only when the name matches an existing repo head."""
        command_mod = importlib.import_module(MODULE_SQUASH_COMMAND)
        repo = MagicMock()
        existing_head = MagicMock()
        existing_head.name = EXISTING_BRANCH_NAME
        repo.heads = [existing_head]

        assert command_mod.branch_name_exists(branch_name, repo) is expected
