import sys
import os
from unittest.mock import MagicMock, patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import RepoSource, ManifestXml
from edkrepo.common.clone_utilities import generate_clone_order, calculate_source_manifest_repo_directory

class TestGenerateCloneOrder:

    NO_NESTED_MOCK_REPO_SOURCES = [
        RepoSource(root="repo1", remote_name="origin", remote_url="https://example.com/repo1.git", branch="main", commit=None, sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=False),
        RepoSource(root="repo2", remote_name="origin", remote_url="https://example.com/repo2.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=False)
    ]

    NESTED_MOCK_REPO_SOURCES = [
        RepoSource(root="repo2/repo1", remote_name="origin", remote_url="https://example.com/repo1.git", branch="main", commit=None, sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=True),
        RepoSource(root="repo2", remote_name="origin", remote_url="https://example.com/repo2.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=False),
        RepoSource(root="repo2/repo1/repo3", remote_name="origin", remote_url="https://example.com/repo3.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=True)
    ]

    EXPECTED_NESTED_CLONE_ORDER = [
        RepoSource(root="repo2", remote_name="origin", remote_url="https://example.com/repo2.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=False),
        RepoSource(root="repo2/repo1", remote_name="origin", remote_url="https://example.com/repo1.git", branch="main", commit=None, sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=True),
        RepoSource(root="repo2/repo1/repo3", remote_name="origin", remote_url="https://example.com/repo3.git", branch=None, commit="def456", sparse=False, enable_submodule=False, tag=None, venv_cfg=None, patch_set=None, blobless=False, treeless=False, nested_repo=True)
    ]

    MOCK_MANIFEST = MagicMock(spec=ManifestXml)
    @staticmethod
    def mock_get_parent_of_nested_repo(repo_sources_to_search, repo_local_root):
        for repo in repo_sources_to_search:
            if repo.root == "repo2":
                raise ValueError("Not a nested repo")
            if repo.root == "repo2/repo1":
                return TestGenerateCloneOrder.NESTED_MOCK_REPO_SOURCES[1]
            if repo.root == "repo2/repo1/repo3":
                return TestGenerateCloneOrder.NESTED_MOCK_REPO_SOURCES[2]
    MOCK_MANIFEST.get_parent_of_nested_repo = MagicMock(side_effect=mock_get_parent_of_nested_repo)

    def test_generate_clone_order_no_nesting(self):
        clone_order = generate_clone_order(self.MOCK_MANIFEST, self.NO_NESTED_MOCK_REPO_SOURCES)
        assert clone_order == self.NO_NESTED_MOCK_REPO_SOURCES

    def test_generate_clone_order_with_nesting(self):
        clone_order = generate_clone_order(self.MOCK_MANIFEST, self.NESTED_MOCK_REPO_SOURCES)
        print(clone_order)
        assert clone_order == self.EXPECTED_NESTED_CLONE_ORDER

class TestCalculateSourceManifestRepoDirectory:

    MOCK_MANIFEST = MagicMock(spec=ManifestXml)
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG = MagicMock()
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG.source_manifest_repo = 'missing manifest repo'
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG = MagicMock()
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG.source_manifest_repo = 'repo1'
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_USER_CFG = MagicMock()
    MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_USER_CFG.source_manifest_repo = 'repo2'
    MOCK_ARGS = MagicMock()
    MOCK_ARGS.source_manifest_repo = None
    MOCK_CONFIG = {
        'cfg_file': MagicMock(),
        'user_cfg_file': MagicMock()
    }
    MOCK_CONFIG["cfg_file"].manifest_repo_abs_path.return_value = '/path/to/manifest/repo1'
    MOCK_CONFIG["user_cfg_file"].manifest_repo_abs_path.return_value = '/path/to/manifest/repo2'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_cfg_no_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo1'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo1'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_cfg_source_manifest_repo_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo1'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo1'
  
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_user_cfg_no_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo2'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo2'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_source_manifest_repo_found_in_user_cfg_source_manifest_repo_flag(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo2'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_USER_CFG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        print(global_manifest_directory)
        assert global_manifest_directory == '/path/to/manifest/repo2'

    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.list_available_manifest_repos')
    @patch('edkrepo.common.workspace_maintenance.manifest_repos_maintenance.find_source_manifest_repo')
    def test_found_manifest_repo_not_in_cfg(self, mock_find_source_manifest_repo, mock_list_available_manifest_repos):
        mock_find_source_manifest_repo.return_value = 'repo3'
        mock_list_available_manifest_repos.return_value = (['repo1'], ['repo2'], [])

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG_CFG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        assert global_manifest_directory is None

    def test_source_manifest_repo_not_found_source_manifest_repo_flag(self):
        mock_find_source_manifest_repo = MagicMock()
        mock_find_source_manifest_repo.return_value = None

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS_SOURCE_MANIFEST_REPO_FLAG, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        assert global_manifest_directory is None
    
    def test_source_manifest_repo_not_found(self):
        mock_find_source_manifest_repo = MagicMock()
        mock_find_source_manifest_repo.return_value = None

        global_manifest_directory = calculate_source_manifest_repo_directory(self.MOCK_ARGS, self.MOCK_CONFIG, self.MOCK_MANIFEST)
        assert global_manifest_directory is None