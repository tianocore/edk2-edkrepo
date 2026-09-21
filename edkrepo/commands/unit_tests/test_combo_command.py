#!/usr/bin/env python3
#
## @file
# test_combo_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.humble import combo_humble as humble
from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception
from edkrepo_manifest_parser.edk_manifest import ManifestXml


MODULE_COMBO_COMMAND = 'edkrepo.commands.combo_command'

FAKE_COMBO_NAME = 'ComboA'
FAKE_OTHER_COMBO_NAME = 'ComboB'
FAKE_ARCHIVED_COMBO_NAME = 'ArchivedCombo'
FAKE_EXTRA_COMBO_NAME = 'ExtraCombo'
FAKE_PIN_COMBO_NAME = 'Pin: test_pin.xml'
FAKE_PIN_FILENAME = 'test_pin.xml'
FAKE_REPO_ROOT_1 = 'repo1'
FAKE_REPO_ROOT_2 = 'repo2'
FAKE_BRANCH_MAIN = 'main'


class TestComboCommand(bt.BaseCommandTest):

    command_module = MODULE_COMBO_COMMAND

    @pytest.fixture
    def combo_cmd(self):
        """Return a fresh ComboCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_COMBO_COMMAND)
        return command_mod.ComboCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with archived and verbose set to default False."""
        args = MagicMock()
        args.archived = False
        args.verbose = False
        return args

    @pytest.fixture
    def fake_combo(self):
        """Return a mock combination object with name FAKE_COMBO_NAME."""
        combo = MagicMock()
        combo.name = FAKE_COMBO_NAME
        combo.description = 'A fake combo description'
        return combo

    @pytest.fixture
    def fake_archived_combo(self):
        """Return a mock archived combination object with name FAKE_ARCHIVED_COMBO_NAME."""
        combo = MagicMock()
        combo.name = FAKE_ARCHIVED_COMBO_NAME
        combo.description = 'An archived combo description'
        return combo

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self, fake_combo):
        """Patch get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(MODULE_COMBO_COMMAND)) as mock:
            manifest = MagicMock()
            manifest.combinations = [fake_combo]
            manifest.archived_combinations = []
            manifest.general_config.current_combo = FAKE_COMBO_NAME
            mock.return_value = manifest
            yield mock

    @pytest.fixture(autouse=True)
    def mock_display_current_project(self):
        """Patch display_current_project to suppress output; always active."""
        with patch('{}.ui_functions.display_current_project'.format(MODULE_COMBO_COMMAND)) as mock:
            yield mock

    @pytest.fixture
    def mock_find_source_manifest_repo(self):
        """Patch find_source_manifest_repo; yields the mock."""
        with patch('{}.find_source_manifest_repo'.format(MODULE_COMBO_COMMAND)) as mock:
            mock.return_value = MagicMock()
            yield mock

    @pytest.fixture
    def mock_get_manifest_repo_path(self):
        """Patch get_manifest_repo_path; yields the mock."""
        with patch('{}.get_manifest_repo_path'.format(MODULE_COMBO_COMMAND)) as mock:
            mock.return_value = MagicMock()
            yield mock

    @pytest.fixture
    def mock_get_manifest_repo_info_from_config(self):
        """Patch get_manifest_repo_info_from_config returning a (url, branch, None) triple; yields the mock."""
        with patch('{}.get_manifest_repo_info_from_config'.format(MODULE_COMBO_COMMAND)) as mock:
            mock.return_value = (MagicMock(), MagicMock(), None)
            yield mock

    @pytest.fixture
    def mock_identify_combo_sources(self, combo_cmd):
        """Patch _identify_combo_sources on the ComboCommand instance to return one fake source."""
        source = MagicMock()
        source.root = 'fake/root'
        with patch.object(combo_cmd, '_identify_combo_sources', return_value=[source]) as mock:
            yield mock

    @pytest.fixture
    def mock_manifest(self):
        """Return a mock ManifestXml instance for direct _identify_combo_sources calls."""
        return MagicMock(spec=ManifestXml)

    @pytest.fixture
    def mock_get_checked_out_pin_file(self):
        """Patch get_checked_out_pin_file in combo_command; yields the mock."""
        with patch('{}.get_checked_out_pin_file'.format(MODULE_COMBO_COMMAND)) as mock:
            yield mock

    @staticmethod
    def _make_mock_repo_source(root=FAKE_REPO_ROOT_1, commit=None, branch=None, tag=None, patch_set=None):
        """Build a mock repo source with configurable root, commit, branch, tag, and patch_set fields."""
        source = MagicMock()
        source.root = root
        source.commit = commit
        source.branch = branch
        source.tag = tag
        source.patch_set = patch_set
        return source

    @staticmethod
    def _run_and_assert_any_print(combo_cmd, mock_args, mock_config, mock_print_info_msg, expected_msg):
        """Execute run_command and assert print_info_msg was called with expected_msg."""
        combo_cmd.run_command(mock_args, mock_config)
        mock_print_info_msg.assert_any_call(expected_msg, header=False)

    def test_run_command_prints_current_combo_with_marker(self, combo_cmd, mock_args, mock_config, mock_print_info_msg):
        """The active combination must be printed using the CURRENT_COMBO format."""
        combo_cmd.run_command(mock_args, mock_config)

        mock_print_info_msg.assert_called_once_with(humble.CURRENT_COMBO.format(FAKE_COMBO_NAME), header=False)

    def test_run_command_non_current_combo_printed_as_regular(self, combo_cmd, mock_args, mock_config, mock_get_workspace_manifest, fake_combo, mock_print_info_msg):
        """A combination that is not current_combo must be printed using the COMBO format."""
        other_combo = MagicMock()
        other_combo.name = FAKE_OTHER_COMBO_NAME
        mock_get_workspace_manifest.return_value.combinations = [fake_combo, other_combo]

        self._run_and_assert_any_print(combo_cmd, mock_args, mock_config, mock_print_info_msg, humble.COMBO.format(FAKE_OTHER_COMBO_NAME))

    def test_run_command_archived_flag_includes_archived_combos(self, combo_cmd, mock_args, mock_config, mock_get_workspace_manifest, fake_archived_combo, mock_print_info_msg):
        """With args.archived=True, archived combinations must be printed using the ARCHIVED_COMBO format."""
        mock_get_workspace_manifest.return_value.archived_combinations = [fake_archived_combo]
        mock_args.archived = True

        self._run_and_assert_any_print(combo_cmd, mock_args, mock_config, mock_print_info_msg, humble.ARCHIVED_COMBO.format(FAKE_ARCHIVED_COMBO_NAME))

    def test_run_command_current_combo_not_in_combinations_is_appended(self, combo_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_print_info_msg):
        """If current_combo is absent from the combinations list, it must be appended and displayed as current."""
        mock_get_workspace_manifest.return_value.general_config.current_combo = FAKE_EXTRA_COMBO_NAME

        self._run_and_assert_any_print(combo_cmd, mock_args, mock_config, mock_print_info_msg, humble.CURRENT_COMBO.format(FAKE_EXTRA_COMBO_NAME))

    def test_run_command_verbose_calls_find_source_manifest_repo(self, combo_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_find_source_manifest_repo, mock_get_manifest_repo_path, mock_get_manifest_repo_info_from_config, mock_identify_combo_sources, mock_print_info_msg):
        """When verbose is True, find_source_manifest_repo must be called with the manifest and config keys."""
        mock_args.verbose = True

        combo_cmd.run_command(mock_args, mock_config)

        mock_find_source_manifest_repo.assert_called_once_with(
            mock_get_workspace_manifest.return_value,
            mock_config['cfg_file'],
            mock_config['user_cfg_file'],
        )

    def test_identify_combo_sources_pin_loads_from_pin_manifest(self, combo_cmd, mock_manifest, mock_config, mock_get_workspace_path, mock_get_checked_out_pin_file):
        """When the combo name contains 'pin:', sources must be loaded from the resolved pin manifest."""
        pin_combo = MagicMock()
        pin_combo.name = FAKE_COMBO_NAME
        pin_manifest = MagicMock(spec=ManifestXml)
        pin_manifest.combinations = [pin_combo]
        source1 = self._make_mock_repo_source(root=FAKE_REPO_ROOT_1, commit='abc123')
        source2 = self._make_mock_repo_source(root=FAKE_REPO_ROOT_2, commit='def456')
        pin_manifest.get_repo_sources.return_value = [source1, source2]
        mock_get_checked_out_pin_file.return_value = pin_manifest

        result = combo_cmd._identify_combo_sources(FAKE_PIN_COMBO_NAME, mock_manifest, mock_config)

        assert result == [source1, source2]
        mock_get_checked_out_pin_file.assert_called_once_with(
            FAKE_PIN_FILENAME, mock_manifest, mock_config, bt.FAKE_WORKSPACE_PATH
        )
        pin_manifest.get_repo_sources.assert_called_once_with(FAKE_COMBO_NAME)

    def test_identify_combo_sources_regular_combo_returns_manifest_sources(self, combo_cmd, mock_manifest, mock_config):
        """For a non-pin combo, sources must be loaded directly from the manifest."""
        source1 = self._make_mock_repo_source(root=FAKE_REPO_ROOT_1, branch=FAKE_BRANCH_MAIN)
        source2 = self._make_mock_repo_source(root=FAKE_REPO_ROOT_2, branch='development')
        mock_manifest.get_repo_sources.return_value = [source1, source2]

        result = combo_cmd._identify_combo_sources(FAKE_COMBO_NAME, mock_manifest, mock_config)

        assert result == [source1, source2]
        mock_manifest.get_repo_sources.assert_called_once_with(FAKE_COMBO_NAME)

    def test_identify_combo_sources_pin_not_found_falls_back_to_manifest(self, combo_cmd, mock_manifest, mock_config, mock_get_workspace_path, mock_get_checked_out_pin_file, mock_print_warning_msg):
        """When the pin file is not found, sources must fall back to the workspace manifest and a warning must be emitted."""
        source1 = self._make_mock_repo_source(root=FAKE_REPO_ROOT_1, branch=FAKE_BRANCH_MAIN)
        mock_manifest.get_repo_sources.return_value = [source1]
        mock_get_checked_out_pin_file.side_effect = edkrepo_exception.EdkrepoPinFileNotFoundException(
            "Pin file '{}' not found".format(FAKE_PIN_FILENAME)
        )

        result = combo_cmd._identify_combo_sources(FAKE_PIN_COMBO_NAME, mock_manifest, mock_config)

        assert result == [source1]
        mock_get_checked_out_pin_file.assert_called_once_with(
            FAKE_PIN_FILENAME, mock_manifest, mock_config, bt.FAKE_WORKSPACE_PATH
        )
        mock_print_warning_msg.assert_called_once()
        assert "Failed to load pin file '{}'".format(FAKE_PIN_FILENAME) in str(mock_print_warning_msg.call_args)
        mock_manifest.get_repo_sources.assert_called_once_with(FAKE_PIN_COMBO_NAME)
