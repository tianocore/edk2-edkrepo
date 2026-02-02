#!/usr/bin/env python3
#
## @file
# test_create_pin.py
#
# Copyright (c) 2017 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import RepoSource, ManifestXml
from edkrepo.commands.create_pin_command import CreatePinCommand
import edkrepo.common.edkrepo_exception as edkrepo_exception


class TestGeneratePinData:
    """
    Test suite for CreatePinCommand._generate_pin_data() method
    """

    # Mock repo sources without patchset (commit-based)
    MOCK_REPO_SOURCES_NO_PATCHSET = [
        RepoSource(
            root="repo1",
            remote_name="origin",
            remote_url="https://example.com/repo1.git",
            branch="main",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False
        ),
        RepoSource(
            root="repo2",
            remote_name="origin",
            remote_url="https://example.com/repo2.git",
            branch="develop",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False
        )
    ]

    # Mock repo sources with patchset
    MOCK_REPO_SOURCES_WITH_PATCHSET = [
        RepoSource(
            root="repo1",
            remote_name="origin",
            remote_url="https://example.com/repo1.git",
            branch="main",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set="patchset1",
            blobless=False,
            treeless=False,
            nested_repo=False
        ),
        RepoSource(
            root="repo2",
            remote_name="origin",
            remote_url="https://example.com/repo2.git",
            branch="develop",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set="patchset2",
            blobless=False,
            treeless=False,
            nested_repo=False
        )
    ]

    # Mixed repo sources (some with patchset, some without)
    MOCK_REPO_SOURCES_MIXED = [
        RepoSource(
            root="repo1",
            remote_name="origin",
            remote_url="https://example.com/repo1.git",
            branch="main",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set="patchset1",
            blobless=False,
            treeless=False,
            nested_repo=False
        ),
        RepoSource(
            root="repo2",
            remote_name="origin",
            remote_url="https://example.com/repo2.git",
            branch="develop",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False
        ),
        RepoSource(
            root="repo3",
            remote_name="origin",
            remote_url="https://example.com/repo3.git",
            branch="feature",
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False
        )
    ]

    @pytest.fixture
    def create_pin_command(self):
        """Fixture to create a CreatePinCommand instance"""
        return CreatePinCommand()

    @pytest.fixture
    def mock_args(self):
        """Fixture to create mock arguments"""
        args = MagicMock()
        args.verbose = False
        return args

    @pytest.fixture
    def mock_args_verbose(self):
        """Fixture to create mock arguments with verbose enabled"""
        args = MagicMock()
        args.verbose = True
        return args

    @pytest.fixture
    def mock_manifest(self):
        """Fixture to create a mock manifest"""
        manifest = MagicMock(spec=ManifestXml)
        manifest.project_info.codename = "TestProject"
        manifest.general_config.current_combo = "main"
        return manifest

    @pytest.fixture
    def workspace_path(self, tmp_path):
        """Fixture to create a temporary workspace path"""
        return str(tmp_path)

    def test_generate_pin_data_no_patchset(self, create_pin_command, mock_args, mock_manifest, workspace_path):
        """
        Test _generate_pin_data with repositories that have no patchset.
        Should retrieve commit SHA from Git repo and update repo sources.
        """
        # Setup
        manifest_clone = mock_manifest
        manifest_clone.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_NO_PATCHSET

        # Create temporary repo directories
        for repo_source in self.MOCK_REPO_SOURCES_NO_PATCHSET:
            repo_path = os.path.join(workspace_path, repo_source.root)
            os.makedirs(repo_path, exist_ok=True)

        # Mock Git Repo objects with different commit SHAs
        with patch('edkrepo.commands.create_pin_command.Repo') as mock_repo_class:
            mock_repo1 = MagicMock()
            mock_repo1.head.commit.hexsha = "abc123def456"
            
            mock_repo2 = MagicMock()
            mock_repo2.head.commit.hexsha = "789ghi012jkl"
            
            mock_repo_class.side_effect = [mock_repo1, mock_repo2]

            # Execute
            result = create_pin_command._generate_pin_data(mock_args, manifest_clone, workspace_path)

            # Verify
            assert len(result) == 2
            assert result[0].root == "repo1"
            assert result[0].commit == "abc123def456"
            assert result[1].root == "repo2"
            assert result[1].commit == "789ghi012jkl"

    def test_generate_pin_data_with_patchset(self, create_pin_command, mock_args, mock_manifest, workspace_path):
        """
        Test _generate_pin_data with repositories that have patchset.
        Should return repo sources as-is without querying Git repo.
        """
        # Setup
        manifest_clone = mock_manifest
        manifest_clone.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_WITH_PATCHSET

        # Create temporary repo directories
        for repo_source in self.MOCK_REPO_SOURCES_WITH_PATCHSET:
            repo_path = os.path.join(workspace_path, repo_source.root)
            os.makedirs(repo_path, exist_ok=True)

        # Execute
        result = create_pin_command._generate_pin_data(mock_args, manifest_clone, workspace_path)

        # Verify - Both repos with patchset should be added as-is to the result list
        assert len(result) == 2  # Both repos have patchset and should be added as-is
        assert result[0].root == "repo1"
        assert result[0].patch_set == "patchset1"
        assert result[0].commit is None  # Commit should not be modified for patchset repos
        assert result[1].root == "repo2"
        assert result[1].patch_set == "patchset2"
        assert result[1].commit is None  # Commit should not be modified for patchset repos

    def test_generate_pin_data_mixed_patchset(self, create_pin_command, mock_args, mock_manifest, workspace_path):
        """
        Test _generate_pin_data with mixed repositories (some with patchset, some without).
        """
        # Setup
        manifest_clone = mock_manifest
        manifest_clone.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_MIXED

        # Create temporary repo directories
        for repo_source in self.MOCK_REPO_SOURCES_MIXED:
            repo_path = os.path.join(workspace_path, repo_source.root)
            os.makedirs(repo_path, exist_ok=True)

        # Mock Git Repo objects for repos without patchset
        with patch('edkrepo.commands.create_pin_command.Repo') as mock_repo_class:
            mock_repo2 = MagicMock()
            mock_repo2.head.commit.hexsha = "commit2sha"
            
            mock_repo3 = MagicMock()
            mock_repo3.head.commit.hexsha = "commit3sha"
            
            mock_repo_class.side_effect = [mock_repo2, mock_repo3]

            # Execute
            result = create_pin_command._generate_pin_data(mock_args, manifest_clone, workspace_path)

            # Verify - All repos should be in result:
            # repo1 with patchset (as-is), repo2 and repo3 with updated commits
            assert len(result) == 3
            assert result[0].root == "repo1"
            assert result[0].patch_set == "patchset1"
            assert result[0].commit is None
            assert result[1].root == "repo2"
            assert result[1].commit == "commit2sha"
            assert result[2].root == "repo3"
            assert result[2].commit == "commit3sha"


    def test_generate_pin_data_verbose_mode_no_patchset(self, create_pin_command, mock_args_verbose, mock_manifest, workspace_path):
        """
        Test _generate_pin_data with verbose mode enabled for repos without patchset.
        Should print verbose information messages.
        """
        # Setup
        manifest_clone = mock_manifest
        manifest_clone.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_NO_PATCHSET

        # Create temporary repo directories
        for repo_source in self.MOCK_REPO_SOURCES_NO_PATCHSET:
            repo_path = os.path.join(workspace_path, repo_source.root)
            os.makedirs(repo_path, exist_ok=True)

        # Mock Git Repo objects
        with patch('edkrepo.commands.create_pin_command.Repo') as mock_repo_class:
            mock_repo1 = MagicMock()
            mock_repo1.head.commit.hexsha = "abc123"
            
            mock_repo2 = MagicMock()
            mock_repo2.head.commit.hexsha = "def456"
            
            mock_repo_class.side_effect = [mock_repo1, mock_repo2]

            # Mock ui_functions to verify verbose output
            with patch('edkrepo.commands.create_pin_command.ui_functions') as mock_ui:
                # Execute
                result = create_pin_command._generate_pin_data(mock_args_verbose, manifest_clone, workspace_path)

                # Verify ui_functions.print_info_msg was called (for verbose output)
                assert mock_ui.print_info_msg.call_count > 0

    def test_generate_pin_data_verbose_mode_with_patchset(self, create_pin_command, mock_args_verbose, mock_manifest, workspace_path):
        """
        Test _generate_pin_data with verbose mode enabled for repos with patchset.
        Should print verbose information about patchset.
        """
        # Setup
        manifest_clone = mock_manifest
        manifest_clone.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_WITH_PATCHSET

        # Create temporary repo directories
        for repo_source in self.MOCK_REPO_SOURCES_WITH_PATCHSET:
            repo_path = os.path.join(workspace_path, repo_source.root)
            os.makedirs(repo_path, exist_ok=True)

        # Mock ui_functions to verify verbose output
        with patch('edkrepo.commands.create_pin_command.ui_functions') as mock_ui:
            with patch('edkrepo.commands.create_pin_command.Repo') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.head.commit.hexsha = "abc123"
                mock_repo_class.return_value = mock_repo

                # Execute
                result = create_pin_command._generate_pin_data(mock_args_verbose, manifest_clone, workspace_path)

                # Verify ui_functions.print_info_msg was called (for verbose output)
                assert mock_ui.print_info_msg.call_count > 0
