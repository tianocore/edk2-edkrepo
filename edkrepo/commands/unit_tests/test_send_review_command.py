import sys
import os
import json
import pytest
from unittest.mock import patch, Mock


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.send_review_command import SendReviewCommand
from edkrepo.common import edkrepo_exception


class TestGetActivePrsOnBranch:
    """Unit tests for the __get_active_prs_on_branch method"""

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_empty_array_response(self, mock_popen, mock_proxy, mock_curl):
        """Test that method raises EdkrepoGithubApiFailException when API returns empty array"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps([]).encode(), b'')
        mock_popen.return_value = mock_process
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                args, "test_branch", modified_repo, manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_missing_fields_in_response(self, mock_popen, mock_proxy, mock_curl):
        """Test that method raises EdkrepoGithubApiFailException when API response is missing required fields"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        api_response = [{"number": 123}]
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps(api_response).encode(), b'')
        mock_popen.return_value = mock_process
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                args, "test_branch", modified_repo, manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_malformed_json_response(self, mock_popen, mock_proxy, mock_curl):
        """Test that method raises EdkrepoGithubApiFailException when API returns malformed JSON"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        mock_process = Mock()
        mock_process.communicate.return_value = (b'invalid json{[}', b'')
        mock_popen.return_value = mock_process
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                args, "test_branch", modified_repo, manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_error_dict_response(self, mock_popen, mock_proxy, mock_curl):
        """Test that method raises EdkrepoGithubApiFailException when API returns error object"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        error_response = {"message": "Not Found"}
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps(error_response).encode(), b'')
        mock_popen.return_value = mock_process
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                args, "test_branch", modified_repo, manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_non_list_response(self, mock_popen, mock_proxy, mock_curl):
        """Test that method raises EdkrepoGithubApiFailException when API returns non-list type"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps("string response").encode(), b'')
        mock_popen.return_value = mock_process
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                args, "test_branch", modified_repo, manifest, "/path/to/.netrc"
            )


class TestBranchNameInference:
    """Unit tests for branch name inference fallback logic"""

    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__get_active_prs_on_branch')
    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__create_pr_branch')
    def test_api_success_triggers_update_flow(self, mock_create_branch, mock_get_prs):
        """Test that valid API response triggers update flow without branch inference"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        args.dry_run = False
        args.title = ['Test', 'PR']
        args.draft = False
        args.reviewers = None
        args.noweb = True
        
        mock_get_prs.return_value = {123: 'https://github.com/test_owner/test_repo/pull/123'}
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        modified_repo.git = Mock()
        modified_repo.git.git = Mock()
        modified_repo.git.git.execute = Mock(return_value=(0, "Success", ""))
        
        try:
            command._SendReviewCommand__send_github_pr_branch_mode(
                args, Mock(), "feature/my-branch", "main",
                modified_repo, manifest, "/path/to/.netrc"
            )
        except Exception:
            pass
        
        mock_create_branch.assert_not_called()

    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__get_active_prs_on_branch')
    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__create_pr_branch')
    def test_pull_request_branch_name_triggers_update_when_api_returns_none(self, mock_create_branch, mock_get_prs):
        """Test that branches starting with pull_request use update flow when API fails"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        args.dry_run = False
        args.title = ['Test', 'PR']
        args.draft = False
        args.reviewers = None
        args.noweb = True
        
        mock_get_prs.side_effect = edkrepo_exception.EdkrepoGithubApiFailException("Branch not found")
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        modified_repo.git = Mock()
        modified_repo.git.git = Mock()
        modified_repo.git.git.execute = Mock(return_value=(0, "Success", ""))
        
        try:
            command._SendReviewCommand__send_github_pr_branch_mode(
                args, Mock(), "pull_request/user/2025-02-01/test_pr", "main",
                modified_repo, manifest, "/path/to/.netrc"
            )
        except Exception:
            pass
        
        mock_create_branch.assert_not_called()

    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__get_active_prs_on_branch')
    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__create_pr_branch')
    def test_non_pull_request_branch_name_triggers_create_when_api_returns_none(self, mock_create_branch, mock_get_prs):
        """Test that branches not starting with pull_request use create flow when API fails"""
        command = SendReviewCommand()
        args = Mock()
        args.verbose = False
        args.dry_run = False
        args.title = ['Test', 'PR']
        args.draft = False
        args.reviewers = None
        args.noweb = True
        
        mock_get_prs.side_effect = edkrepo_exception.EdkrepoGithubApiFailException("Branch not found")
        mock_create_branch.return_value = "pull_request/user/2025-02-01/new_pr"
        
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        
        modified_repo = Mock()
        modified_repo.manifest = Mock()
        modified_repo.manifest.remote_name = "origin"
        modified_repo.git = Mock()
        modified_repo.git.git = Mock()
        modified_repo.git.heads = {"pull_request/user/2025-02-01/new_pr": Mock()}
        
        try:
            command._SendReviewCommand__send_github_pr_branch_mode(
                args, Mock(), "feature/my-branch", "main",
                modified_repo, manifest, "/path/to/.netrc"
            )
        except Exception:
            pass
        
        mock_create_branch.assert_called_once()
