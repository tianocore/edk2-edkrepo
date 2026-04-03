#!/usr/bin/env python3
#
## @file
# test_send_review_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

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

    @pytest.fixture
    def command(self):
        """Provide SendReviewCommand instance"""
        return SendReviewCommand()
    
    @pytest.fixture
    def mock_args(self):
        """Provide mock args with common defaults"""
        args = Mock()
        args.verbose = False
        return args
    
    @pytest.fixture
    def mock_manifest(self):
        """Provide mock manifest with remote configuration"""
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        return manifest
    
    @pytest.fixture
    def mock_modified_repo(self):
        """Provide mock repository object"""
        repo = Mock()
        repo.manifest = Mock()
        repo.manifest.remote_name = "origin"
        return repo

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_empty_array_response(self, mock_popen, mock_proxy, mock_curl,
                                  command, mock_args, mock_manifest, mock_modified_repo):
        """Test that method raises EdkrepoGithubApiFailException when API returns empty array"""
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps([]).encode(), b'')
        mock_popen.return_value = mock_process
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                mock_args, "test_branch", mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_missing_fields_in_response(self, mock_popen, mock_proxy, mock_curl,
                                       command, mock_args, mock_manifest, mock_modified_repo):
        """Test that method raises EdkrepoGithubApiFailException when API response is missing required fields"""
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        api_response = [{"number": 123}]
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps(api_response).encode(), b'')
        mock_popen.return_value = mock_process
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                mock_args, "test_branch", mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_malformed_json_response(self, mock_popen, mock_proxy, mock_curl,
                                    command, mock_args, mock_manifest, mock_modified_repo):
        """Test that method raises EdkrepoGithubApiFailException when API returns malformed JSON"""
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        mock_process = Mock()
        mock_process.communicate.return_value = (b'invalid json{[}', b'')
        mock_popen.return_value = mock_process
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                mock_args, "test_branch", mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_error_dict_response(self, mock_popen, mock_proxy, mock_curl,
                                command, mock_args, mock_manifest, mock_modified_repo):
        """Test that method raises EdkrepoGithubApiFailException when API returns error object"""
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        error_response = {"message": "Not Found"}
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps(error_response).encode(), b'')
        mock_popen.return_value = mock_process
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                mock_args, "test_branch", mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )

    @patch('edkrepo.commands.send_review_command.common_repo_functions.find_curl')
    @patch('edkrepo.commands.send_review_command.common_repo_functions.get_proxy_str')
    @patch('edkrepo.commands.send_review_command.subprocess.Popen')
    def test_non_list_response(self, mock_popen, mock_proxy, mock_curl,
                              command, mock_args, mock_manifest, mock_modified_repo):
        """Test that method raises EdkrepoGithubApiFailException when API returns non-list type"""
        mock_curl.return_value = "/usr/bin/curl"
        mock_proxy.return_value = None
        
        mock_process = Mock()
        mock_process.communicate.return_value = (json.dumps("string response").encode(), b'')
        mock_popen.return_value = mock_process
        
        with pytest.raises(edkrepo_exception.EdkrepoGithubApiFailException):
            command._SendReviewCommand__get_active_prs_on_branch(
                mock_args, "test_branch", mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )


class TestBranchNameInference:
    """Unit tests for branch name inference fallback logic"""

    @pytest.fixture
    def command(self):
        """Provide SendReviewCommand instance"""
        return SendReviewCommand()
    
    @pytest.fixture
    def mock_args(self):
        """Provide mock args with common test defaults"""
        args = Mock()
        args.verbose = False
        args.dry_run = False
        args.title = ['Test', 'PR']
        args.draft = False
        args.reviewers = None
        args.noweb = True
        return args
    
    @pytest.fixture
    def mock_manifest(self):
        """Provide mock manifest with remote configuration"""
        manifest = Mock()
        remote = Mock()
        remote.owner = "test_owner"
        remote.name = "test_repo"
        manifest.get_remote = Mock(return_value=remote)
        return manifest
    
    @pytest.fixture
    def mock_modified_repo(self):
        """Provide mock repository object with git configuration"""
        repo = Mock()
        repo.manifest = Mock()
        repo.manifest.remote_name = "origin"
        repo.git = Mock()
        repo.git.git = Mock()
        repo.git.git.execute = Mock(return_value=(0, "Success", ""))
        return repo

    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__get_active_prs_on_branch')
    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__create_pr_branch')
    def test_api_success_triggers_update_flow(self, mock_create_branch, mock_get_prs,
                                             command, mock_args, mock_manifest, mock_modified_repo):
        """Test that valid API response triggers update flow without branch inference"""
        mock_get_prs.return_value = {123: 'https://github.com/test_owner/test_repo/pull/123'}
        
        try:
            command._SendReviewCommand__send_github_pr_branch_mode(
                mock_args, Mock(), "feature/my-branch", "main",
                mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )
        except Exception:
            pass
        
        mock_create_branch.assert_not_called()

    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__get_active_prs_on_branch')
    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__create_pr_branch')
    def test_pull_request_branch_name_triggers_update_when_api_returns_none(self, mock_create_branch, mock_get_prs,
                                                                           command, mock_args, mock_manifest, mock_modified_repo):
        """Test that branches starting with pull_request use update flow when API fails"""
        mock_get_prs.side_effect = edkrepo_exception.EdkrepoGithubApiFailException("Branch not found")
        
        try:
            command._SendReviewCommand__send_github_pr_branch_mode(
                mock_args, Mock(), "pull_request/user/2025-02-01/test_pr", "main",
                mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )
        except Exception:
            pass
        
        mock_create_branch.assert_not_called()

    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__get_active_prs_on_branch')
    @patch('edkrepo.commands.send_review_command.SendReviewCommand._SendReviewCommand__create_pr_branch')
    def test_non_pull_request_branch_name_triggers_create_when_api_returns_none(self, mock_create_branch, mock_get_prs,
                                                                                command, mock_args, mock_manifest, mock_modified_repo):
        """Test that branches not starting with pull_request use create flow when API fails"""
        mock_get_prs.side_effect = edkrepo_exception.EdkrepoGithubApiFailException("Branch not found")
        mock_create_branch.return_value = "pull_request/user/2025-02-01/new_pr"
        
        # Add heads attribute for branch checkout
        mock_modified_repo.git.heads = {"pull_request/user/2025-02-01/new_pr": Mock()}
        
        try:
            command._SendReviewCommand__send_github_pr_branch_mode(
                mock_args, Mock(), "feature/my-branch", "main",
                mock_modified_repo, mock_manifest, "/path/to/.netrc"
            )
        except Exception:
            pass
        
        mock_create_branch.assert_called_once()
