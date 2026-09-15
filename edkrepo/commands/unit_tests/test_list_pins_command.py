#!/usr/bin/env python3
#
## @file
# test_list_pins_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_LIST_PINS_COMMAND = 'edkrepo.commands.list_pins_command'

FAKE_MANIFEST_REPO = 'fake_repo'
FAKE_NOT_IN_WORKSPACE = 'not in workspace'


class TestListPinsCommand(bt.BaseCommandTest):

    command_module = MODULE_LIST_PINS_COMMAND

    @pytest.fixture
    def list_pins_cmd(self):
        """Return a fresh ListPinsCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_LIST_PINS_COMMAND)
        return command_mod.ListPinsCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with all list-pins arguments set to safe defaults."""
        args = MagicMock()
        args.source_manifest_repo = None
        args.project = None
        args.verbose = False
        args.description = False
        return args

    @pytest.fixture(autouse=True)
    def mock_list_available_manifest_repos(self):
        """Patch list_available_manifest_repos; always active since run_command calls it unconditionally."""
        with patch('{}.list_available_manifest_repos'.format(MODULE_LIST_PINS_COMMAND),
                   return_value=([FAKE_MANIFEST_REPO], [], [])) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest with a manifest whose pin_path is set; always active."""
        with patch('{}.get_workspace_manifest'.format(MODULE_LIST_PINS_COMMAND)) as mock:
            manifest = MagicMock()
            manifest.general_config.pin_path = 'pins'
            mock.return_value = manifest
            yield mock

    @pytest.fixture
    def run_command_setup(self, mock_config):
        """Activate patches for a successful workspace-based run; yields key mocks as a namespace."""
        mock_config['cfg_file'].manifest_repo_abs_path.return_value = 'C:\\fake\\manifest\\repo'
        with patch('{}.pull_workspace_manifest_repo'.format(MODULE_LIST_PINS_COMMAND)) as mock_pull, \
             patch('{}.find_source_manifest_repo'.format(MODULE_LIST_PINS_COMMAND),
                   return_value=FAKE_MANIFEST_REPO), \
             patch('{}.os.walk'.format(MODULE_LIST_PINS_COMMAND), return_value=iter([])) as mock_os_walk:
            yield SimpleNamespace(pull=mock_pull, os_walk=mock_os_walk)

    @staticmethod
    def _set_outside_workspace_with_project(mock_get_workspace_manifest, mock_args):
        """Configure mocks so get_workspace_manifest raises and --project is provided (the outside-workspace fallback path)."""
        mock_get_workspace_manifest.side_effect = edkrepo_exception.EdkrepoWorkspaceInvalidException(FAKE_NOT_IN_WORKSPACE)
        mock_args.project = ['TestProject']

    @staticmethod
    def _patch_find_project_fallback(manifest_path):
        """Return the (find_project_in_all_indices, ManifestXml) patches for the --project fallback path."""
        return (
            patch('{}.find_project_in_all_indices'.format(MODULE_LIST_PINS_COMMAND),
                  return_value=(FAKE_MANIFEST_REPO, MagicMock(), manifest_path)),
            patch('{}.ManifestXml'.format(MODULE_LIST_PINS_COMMAND)),
        )

    def test_run_command_returns_early_when_pin_path_is_none(self, list_pins_cmd, mock_args, mock_config, mock_get_workspace_manifest, run_command_setup, mock_find_less):
        """When manifest.general_config.pin_path is None, run_command must return before walking any directories."""
        mock_get_workspace_manifest.return_value.general_config.pin_path = None

        list_pins_cmd.run_command(mock_args, mock_config)

        run_command_setup.os_walk.assert_not_called()

    def test_run_command_pulls_workspace_manifest_repo(self, list_pins_cmd, mock_args, mock_config, run_command_setup, mock_find_less):
        """run_command must call pull_workspace_manifest_repo to refresh the manifest repo."""
        list_pins_cmd.run_command(mock_args, mock_config)

        run_command_setup.pull.assert_called_once()

    def test_resolve_manifest_and_directory_returns_workspace_manifest(self, list_pins_cmd, mock_args, mock_config, mock_get_workspace_manifest):
        """_resolve_manifest_and_directory must return the workspace manifest when inside a workspace."""
        mock_config['cfg_file'].manifest_repo_abs_path.return_value = bt.FAKE_MANIFEST_REPO_PATH
        with patch('{}.pull_workspace_manifest_repo'.format(MODULE_LIST_PINS_COMMAND)), \
             patch('{}.find_source_manifest_repo'.format(MODULE_LIST_PINS_COMMAND),
                   return_value=FAKE_MANIFEST_REPO):
            manifest, manifest_directory = list_pins_cmd._resolve_manifest_and_directory(
                mock_args, mock_config, [FAKE_MANIFEST_REPO], [])

        assert manifest is mock_get_workspace_manifest.return_value
        assert manifest_directory == bt.FAKE_MANIFEST_REPO_PATH

    def test_resolve_manifest_and_directory_uses_project_arg_as_fallback(self, list_pins_cmd, mock_args, mock_config, mock_get_workspace_manifest):
        """When not in workspace but --project is given, _resolve_manifest_and_directory must use find_project_in_all_indices."""
        self._set_outside_workspace_with_project(mock_get_workspace_manifest, mock_args)
        mock_config['cfg_file'].manifest_repo_abs_path.return_value = '/fake/dir'
        find_patch, manifest_patch = self._patch_find_project_fallback('/fake/test.xml')
        with find_patch as mock_find, manifest_patch as mock_manifest_xml:
            manifest, _ = list_pins_cmd._resolve_manifest_and_directory(
                mock_args, mock_config, [FAKE_MANIFEST_REPO], [])

        mock_find.assert_called_once()
        assert manifest is mock_manifest_xml.return_value

    def test_run_command_calls_find_project_when_outside_workspace_with_project(self, list_pins_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_find_less):
        """When not in a workspace but --project is provided, find_project_in_all_indices must be called."""
        self._set_outside_workspace_with_project(mock_get_workspace_manifest, mock_args)

        find_patch, manifest_patch = self._patch_find_project_fallback('/fake/manifest.xml')
        with find_patch as mock_find_proj, manifest_patch as mock_manifest_xml:
            mock_manifest_xml.return_value.general_config.pin_path = None
            list_pins_cmd.run_command(mock_args, mock_config)

        mock_find_proj.assert_called_once()

    @pytest.mark.parametrize('method, call_args', [
        pytest.param('run_command', (), id='run_command'),
        pytest.param('_resolve_manifest_and_directory', ([], []), id='resolve_manifest_and_directory'),
    ])
    def test_raises_when_not_in_workspace_without_project(self, list_pins_cmd, mock_args, mock_config, mock_get_workspace_manifest, method, call_args, mock_find_less):
        """When not in a workspace and no --project is given, EdkrepoInvalidParametersException must be raised."""
        mock_get_workspace_manifest.side_effect = edkrepo_exception.EdkrepoWorkspaceInvalidException(FAKE_NOT_IN_WORKSPACE)
        mock_args.project = None
        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            getattr(list_pins_cmd, method)(mock_args, mock_config, *call_args)
