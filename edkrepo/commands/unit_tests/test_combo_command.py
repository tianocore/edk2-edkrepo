#!/usr/bin/env python3
#
## @file
# test_combo_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#


import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.combo_command import ComboCommand
from edkrepo.common.edkrepo_exception import EdkrepoPinFileNotFoundException
from edkrepo_manifest_parser.edk_manifest import ManifestXml, RepoSource


class TestIdentifyComboSources:
    """Unit tests for the ComboCommand._identify_combo_sources method"""

    @pytest.fixture
    def combo_cmd(self):
        """Provide a ComboCommand instance for testing"""
        return ComboCommand()

    @pytest.fixture
    def mock_config(self):
        """Provide a fresh mock config for each test"""
        return {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}

    @pytest.fixture
    def mock_manifest(self):
        """Provide a mock ManifestXml object"""
        return MagicMock(spec=ManifestXml)

    @pytest.fixture
    def mock_repo_source(self):
        """Factory fixture for creating mock RepoSource objects"""
        def _create_source(root='repo1', commit=None, branch=None, tag=None, patch_set=None):
            source = MagicMock(spec=RepoSource)
            source.root = root
            source.commit = commit
            source.branch = branch
            source.tag = tag
            source.patch_set = patch_set
            return source
        return _create_source

    @patch('edkrepo.commands.combo_command.get_checked_out_pin_file')
    @patch('edkrepo.commands.combo_command.get_workspace_path')
    def test_identify_combo_sources_with_pin(self, mock_workspace_path, mock_get_pin_file,
                                            combo_cmd, mock_manifest, mock_config, mock_repo_source):
        """Test _identify_combo_sources when a pin file is checked out"""
        mock_workspace_path.return_value = '/path/to/workspace'

        mock_pin_manifest = MagicMock(spec=ManifestXml)
        mock_pin_combo = MagicMock()
        mock_pin_combo.name = 'combo1'
        mock_pin_manifest.combinations = [mock_pin_combo]

        mock_source1 = mock_repo_source(root='repo1', commit='abc123')
        mock_source2 = mock_repo_source(root='repo2', commit='def456')

        mock_pin_manifest.get_repo_sources = MagicMock(return_value=[mock_source1, mock_source2])
        mock_get_pin_file.return_value = mock_pin_manifest

        result = combo_cmd._identify_combo_sources('Pin: test_pin.xml', mock_manifest, mock_config)

        assert result == [mock_source1, mock_source2]
        mock_get_pin_file.assert_called_once_with('test_pin.xml', mock_manifest, mock_config, '/path/to/workspace')
        mock_pin_manifest.get_repo_sources.assert_called_once_with('combo1')

    def test_identify_combo_sources_with_regular_combo(self, combo_cmd, mock_manifest,
                                                       mock_config, mock_repo_source):
        """Test _identify_combo_sources when a regular combo is checked out"""
        mock_source1 = mock_repo_source(root='repo1', branch='main')
        mock_source2 = mock_repo_source(root='repo2', branch='development')

        mock_manifest.get_repo_sources = MagicMock(return_value=[mock_source1, mock_source2])

        result = combo_cmd._identify_combo_sources('combo1', mock_manifest, mock_config)

        assert result == [mock_source1, mock_source2]
        mock_manifest.get_repo_sources.assert_called_once_with('combo1')

    @patch('edkrepo.commands.combo_command.get_checked_out_pin_file')
    @patch('edkrepo.commands.combo_command.get_workspace_path')
    @patch('edkrepo.commands.combo_command.ui_functions.print_warning_msg')
    def test_identify_combo_sources_pin_not_found(self, mock_print_warning, mock_workspace_path,
                                                  mock_get_pin_file, combo_cmd, mock_manifest,
                                                  mock_config, mock_repo_source):
        """Test _identify_combo_sources when a pin file cannot be found"""
        mock_workspace_path.return_value = '/path/to/workspace'

        mock_source1 = mock_repo_source(root='repo1', branch='main')

        mock_manifest.get_repo_sources = MagicMock(return_value=[mock_source1])

        mock_get_pin_file.side_effect = EdkrepoPinFileNotFoundException("Pin file 'test_pin.xml' not found")

        result = combo_cmd._identify_combo_sources('Pin: test_pin.xml', mock_manifest, mock_config)

        assert result == [mock_source1]
        mock_get_pin_file.assert_called_once_with('test_pin.xml', mock_manifest, mock_config, '/path/to/workspace')
        mock_print_warning.assert_called_once()
        assert "Failed to load pin file 'test_pin.xml'" in str(mock_print_warning.call_args)

        mock_manifest.get_repo_sources.assert_called_once_with('Pin: test_pin.xml')
