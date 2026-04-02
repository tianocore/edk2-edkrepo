#!/usr/bin/env python3
#
## @file
# test_workspace_pin_file_operations.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from edkrepo.common.workspace_maintenance.workspace_pin_file_operations import (
    get_checked_out_pin_file,
)
from edkrepo_manifest_parser.edk_manifest import GeneralConfig, ManifestXml


class TestGetCheckedOutPinFile:
    """Unit tests for the get_checked_out_pin_file function"""

    @pytest.fixture
    def mock_config(self):
        """Provide a fresh mock config for each test"""
        return {
            'cfg_file': MagicMock(),
            'user_cfg_file': MagicMock()
        }

    @pytest.fixture
    def mock_workspace_manifest(self):
        """Factory fixture for creating mock workspace manifests"""
        def _create_manifest(pin_path='pins'):
            manifest = MagicMock(spec=ManifestXml)
            general_config = MagicMock(spec=GeneralConfig)
            general_config.pin_path = pin_path
            manifest.general_config = general_config
            return manifest
        return _create_manifest

    @pytest.fixture
    def mock_pin_manifest(self):
        """Provide a mock pin manifest object"""
        return MagicMock(spec=ManifestXml)

    def test_get_checked_out_pin_file_from_manifest_repo_pin_folder(self, mock_config,
                                                                    mock_workspace_manifest,
                                                                    mock_pin_manifest):
        """Test loading pin file from manifest repo pin folder"""
        mock_manifest = mock_workspace_manifest(pin_path='pins')

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_path = os.path.join(manifest_repo_path, 'pins', 'test_pin.xml')

        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile') as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path
                        mock_isfile.return_value = True

                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, mock_config, workspace_path)

                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_path)

    def test_get_checked_out_pin_file_from_workspace_root(self, mock_config,
                                                          mock_workspace_manifest,
                                                          mock_pin_manifest):
        """Test loading pin file from workspace root when not in manifest repo"""
        mock_manifest = mock_workspace_manifest(pin_path='pins')

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_path = os.path.join(workspace_path, 'test_pin.xml')

        def isfile_side_effect(path):
            return path == pin_file_path

        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', side_effect=isfile_side_effect) as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path

                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, mock_config, workspace_path)

                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_path)

    def test_get_checked_out_pin_file_not_found(self, mock_config, mock_workspace_manifest):
        """Test get_checked_out_pin_file raises exception when pin file doesn't exist"""
        from edkrepo.common.edkrepo_exception import EdkrepoPinFileNotFoundException

        mock_manifest = mock_workspace_manifest(pin_path='pins')

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'

        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', return_value=False) as mock_isfile:
                    mock_find.return_value = 'test_repo'
                    mock_get_path.return_value = manifest_repo_path

                    try:
                        result = get_checked_out_pin_file('nonexistent_pin.xml', mock_manifest, mock_config, workspace_path)
                        assert False, "Expected EdkrepoPinFileNotFoundException to be raised"
                    except EdkrepoPinFileNotFoundException as e:
                        assert 'nonexistent_pin.xml' in str(e)

    def test_get_checked_out_pin_file_no_pin_path_in_config(self, mock_config,
                                                            mock_workspace_manifest,
                                                            mock_pin_manifest):
        """Test loading pin file when pin_path is not configured"""
        mock_manifest = mock_workspace_manifest(pin_path=None)

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_path = os.path.join(workspace_path, 'test_pin.xml')

        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', return_value=True) as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path

                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, mock_config, workspace_path)

                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_path)

    def test_get_checked_out_pin_file_prefers_manifest_repo_over_workspace(self, mock_config,
                                                                          mock_workspace_manifest,
                                                                          mock_pin_manifest):
        """Test that manifest repo pin folder is checked before workspace root"""
        mock_manifest = mock_workspace_manifest(pin_path='pins')

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_manifest_repo = os.path.join(manifest_repo_path, 'pins', 'test_pin.xml')
        pin_file_workspace = os.path.join(workspace_path, 'test_pin.xml')

        def isfile_side_effect(path):
            return path in [pin_file_manifest_repo, pin_file_workspace]

        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', side_effect=isfile_side_effect) as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path

                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, mock_config, workspace_path)

                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_manifest_repo)
