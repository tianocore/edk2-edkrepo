import sys
import os
from unittest.mock import MagicMock, patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import ManifestXml, GeneralConfig
from edkrepo.config.config_factory import get_checked_out_pin_file


class TestGetCheckedOutPinFile:
    """Unit tests for the get_checked_out_pin_file function"""

    MOCK_CONFIG = {
        'cfg_file': MagicMock(),
        'user_cfg_file': MagicMock()
    }

    def test_get_checked_out_pin_file_from_manifest_repo_pin_folder(self):
        """Test loading pin file from manifest repo pin folder"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_general_config = MagicMock(spec=GeneralConfig)
        mock_general_config.pin_path = 'pins'
        mock_manifest.general_config = mock_general_config

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_path = os.path.join(manifest_repo_path, 'pins', 'test_pin.xml')
        
        mock_pin_manifest = MagicMock(spec=ManifestXml)
        
        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile') as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path
                        mock_isfile.return_value = True
                        
                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, self.MOCK_CONFIG, workspace_path)
                        
                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_path)

    def test_get_checked_out_pin_file_from_workspace_root(self):
        """Test loading pin file from workspace root when not in manifest repo"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_general_config = MagicMock(spec=GeneralConfig)
        mock_general_config.pin_path = 'pins'
        mock_manifest.general_config = mock_general_config

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_path = os.path.join(workspace_path, 'test_pin.xml')
        
        mock_pin_manifest = MagicMock(spec=ManifestXml)
        
        def isfile_side_effect(path):
            return path == pin_file_path
        
        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', side_effect=isfile_side_effect) as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path
                        
                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, self.MOCK_CONFIG, workspace_path)
                        
                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_path)

    def test_get_checked_out_pin_file_not_found(self):
        """Test get_checked_out_pin_file raises exception when pin file doesn't exist"""
        from edkrepo.common.edkrepo_exception import EdkrepoPinFileNotFoundException
        
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_general_config = MagicMock(spec=GeneralConfig)
        mock_general_config.pin_path = 'pins'
        mock_manifest.general_config = mock_general_config

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'

        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', return_value=False) as mock_isfile:
                    mock_find.return_value = 'test_repo'
                    mock_get_path.return_value = manifest_repo_path
                    
                    try:
                        result = get_checked_out_pin_file('nonexistent_pin.xml', mock_manifest, self.MOCK_CONFIG, workspace_path)
                        assert False, "Expected EdkrepoPinFileNotFoundException to be raised"
                    except EdkrepoPinFileNotFoundException as e:
                        assert 'nonexistent_pin.xml' in str(e)

    def test_get_checked_out_pin_file_no_pin_path_in_config(self):
        """Test loading pin file when pin_path is not configured"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_general_config = MagicMock(spec=GeneralConfig)
        mock_general_config.pin_path = None
        mock_manifest.general_config = mock_general_config

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_path = os.path.join(workspace_path, 'test_pin.xml')
        
        mock_pin_manifest = MagicMock(spec=ManifestXml)
        
        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', return_value=True) as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path
                        
                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, self.MOCK_CONFIG, workspace_path)
                        
                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_path)

    def test_get_checked_out_pin_file_prefers_manifest_repo_over_workspace(self):
        """Test that manifest repo pin folder is checked before workspace root"""
        mock_manifest = MagicMock(spec=ManifestXml)
        mock_general_config = MagicMock(spec=GeneralConfig)
        mock_general_config.pin_path = 'pins'
        mock_manifest.general_config = mock_general_config

        manifest_repo_path = '/path/to/manifest_repo'
        workspace_path = '/path/to/workspace'
        pin_file_manifest_repo = os.path.join(manifest_repo_path, 'pins', 'test_pin.xml')
        pin_file_workspace = os.path.join(workspace_path, 'test_pin.xml')
        
        mock_pin_manifest = MagicMock(spec=ManifestXml)
        
        def isfile_side_effect(path):
            return path in [pin_file_manifest_repo, pin_file_workspace]
        
        with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo') as mock_find:
            with patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.get_manifest_repo_path') as mock_get_path:
                with patch('edkrepo.config.config_factory.os.path.isfile', side_effect=isfile_side_effect) as mock_isfile:
                    with patch('edkrepo.config.config_factory.edk_manifest.ManifestXml', return_value=mock_pin_manifest) as mock_manifest_xml:
                        mock_find.return_value = 'test_repo'
                        mock_get_path.return_value = manifest_repo_path
                        
                        result = get_checked_out_pin_file('test_pin.xml', mock_manifest, self.MOCK_CONFIG, workspace_path)
                        
                        assert result is not None
                        assert result == mock_pin_manifest
                        mock_manifest_xml.assert_called_once_with(pin_file_manifest_repo)
