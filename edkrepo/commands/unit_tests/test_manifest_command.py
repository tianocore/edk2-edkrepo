#!/usr/bin/env python3
#
## @file
# test_manifest_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_MANIFEST_COMMAND = 'edkrepo.commands.manifest_command'


class TestManifestCommand(bt.BaseCommandTest):

    command_module = MODULE_MANIFEST_COMMAND

    @pytest.fixture
    def manifest_cmd(self):
        """Return a fresh ManifestCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_MANIFEST_COMMAND)
        return command_mod.ManifestCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with archived and verbose set to safe defaults."""
        args = MagicMock()
        args.archived = False
        args.verbose = False
        return args

    @pytest.fixture(autouse=True)
    def mock_list_available_manifest_repos(self):
        """Patch list_available_manifest_repos returning empty lists; always active."""
        with patch('{}.list_available_manifest_repos'.format(MODULE_MANIFEST_COMMAND),
                   return_value=([], [], [])) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(MODULE_MANIFEST_COMMAND)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_find_source_manifest_repo(self):
        """Patch find_source_manifest_repo; always active to prevent real manifest lookups."""
        with patch('{}.find_source_manifest_repo'.format(MODULE_MANIFEST_COMMAND)) as mock:
            yield mock

    def test_run_command_calls_list_available_manifest_repos(self, manifest_cmd, mock_args, mock_config, mock_list_available_manifest_repos, mock_pull_all_manifest_repos):
        """list_available_manifest_repos must be called with the cfg and user_cfg files from config."""
        manifest_cmd.run_command(mock_args, mock_config)

        mock_list_available_manifest_repos.assert_called_once_with(
            mock_config['cfg_file'], mock_config['user_cfg_file']
        )

    def test_run_command_calls_pull_all_manifest_repos(self, manifest_cmd, mock_args, mock_config, mock_pull_all_manifest_repos):
        """pull_all_manifest_repos must be called unconditionally to refresh all manifest repos."""
        manifest_cmd.run_command(mock_args, mock_config)

        mock_pull_all_manifest_repos.assert_called_once()

    @pytest.mark.parametrize('exc', [
        pytest.param(edkrepo_exception.EdkrepoWorkspaceInvalidException('not in workspace'), id='workspace_invalid'),
        pytest.param(edkrepo_exception.EdkrepoManifestNotFoundException('manifest not found'), id='manifest_not_found'),
    ])
    def test_run_command_handles_get_workspace_manifest_exception_gracefully(self, manifest_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_pull_all_manifest_repos, exc):
        """Exceptions from get_workspace_manifest must not propagate to the caller."""
        mock_get_workspace_manifest.side_effect = exc

        manifest_cmd.run_command(mock_args, mock_config)
