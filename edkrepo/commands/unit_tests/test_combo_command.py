import sys
import os
from unittest.mock import MagicMock, patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import ManifestXml, RepoSource
from edkrepo.commands.combo_command import ComboCommand
from edkrepo.common.edkrepo_exception import EdkrepoPinFileNotFoundException


class TestIdentifyComboSources:
    """Unit tests for the ComboCommand._identify_combo_sources method"""

    @patch('edkrepo.commands.combo_command.get_checked_out_pin_file')
    @patch('edkrepo.commands.combo_command.get_workspace_path')
    def test_identify_combo_sources_with_pin(self, mock_workspace_path, mock_get_pin_file):
        """Test _identify_combo_sources when a pin file is checked out"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        mock_workspace_path.return_value = '/path/to/workspace'
        
        mock_pin_manifest = MagicMock(spec=ManifestXml)
        mock_pin_combo = MagicMock()
        mock_pin_combo.name = 'combo1'
        mock_pin_manifest.combinations = [mock_pin_combo]
        
        mock_source1 = MagicMock(spec=RepoSource)
        mock_source1.root = 'repo1'
        mock_source1.commit = 'abc123'
        mock_source1.branch = None
        mock_source1.tag = None
        mock_source1.patch_set = None
        
        mock_source2 = MagicMock(spec=RepoSource)
        mock_source2.root = 'repo2'
        mock_source2.commit = 'def456'
        mock_source2.branch = None
        mock_source2.tag = None
        mock_source2.patch_set = None
        
        mock_pin_manifest.get_repo_sources = MagicMock(return_value=[mock_source1, mock_source2])
        mock_get_pin_file.return_value = mock_pin_manifest
        
        combo_cmd = ComboCommand()
        result = combo_cmd._identify_combo_sources('Pin: test_pin.xml', mock_manifest, mock_config)
        
        assert result == [mock_source1, mock_source2]
        mock_get_pin_file.assert_called_once_with('test_pin.xml', mock_manifest, mock_config, '/path/to/workspace')
        mock_pin_manifest.get_repo_sources.assert_called_once_with('combo1')

    def test_identify_combo_sources_with_regular_combo(self):
        """Test _identify_combo_sources when a regular combo is checked out"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        
        mock_source1 = MagicMock(spec=RepoSource)
        mock_source1.root = 'repo1'
        mock_source1.branch = 'main'
        mock_source1.commit = None
        mock_source1.tag = None
        mock_source1.patch_set = None
        
        mock_source2 = MagicMock(spec=RepoSource)
        mock_source2.root = 'repo2'
        mock_source2.branch = 'development'
        mock_source2.commit = None
        mock_source2.tag = None
        mock_source2.patch_set = None
        
        mock_manifest.get_repo_sources = MagicMock(return_value=[mock_source1, mock_source2])
        
        combo_cmd = ComboCommand()
        result = combo_cmd._identify_combo_sources('combo1', mock_manifest, mock_config)
        
        assert result == [mock_source1, mock_source2]
        mock_manifest.get_repo_sources.assert_called_once_with('combo1')

    @patch('edkrepo.commands.combo_command.get_checked_out_pin_file')
    @patch('edkrepo.commands.combo_command.get_workspace_path')
    @patch('edkrepo.commands.combo_command.ui_functions.print_warning_msg')
    def test_identify_combo_sources_pin_not_found(self, mock_print_warning, mock_workspace_path, mock_get_pin_file):
        """Test _identify_combo_sources when a pin file cannot be found"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        mock_workspace_path.return_value = '/path/to/workspace'
        
        mock_source1 = MagicMock(spec=RepoSource)
        mock_source1.root = 'repo1'
        mock_source1.branch = 'main'
        mock_source1.commit = None
        mock_source1.tag = None
        mock_source1.patch_set = None
        
        mock_manifest.get_repo_sources = MagicMock(return_value=[mock_source1])
        
        mock_get_pin_file.side_effect = EdkrepoPinFileNotFoundException("Pin file 'test_pin.xml' not found")
        
        combo_cmd = ComboCommand()
        result = combo_cmd._identify_combo_sources('Pin: test_pin.xml', mock_manifest, mock_config)
        
        assert result == [mock_source1]
        mock_get_pin_file.assert_called_once_with('test_pin.xml', mock_manifest, mock_config, '/path/to/workspace')
        mock_print_warning.assert_called_once()
        assert "Failed to load pin file 'test_pin.xml'" in str(mock_print_warning.call_args)

        mock_manifest.get_repo_sources.assert_called_once_with('Pin: test_pin.xml')
