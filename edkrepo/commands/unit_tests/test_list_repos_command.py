#!/usr/bin/env python3
#
## @file
# test_list_repos_command.py
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


MODULE_LIST_REPOS_COMMAND = 'edkrepo.commands.list_repos_command'
FAKE_MANIFEST_REPO_NAME = 'my_repo'
FAKE_PROJECT_NAME = 'ProjectA'


class TestListReposCommand(bt.BaseCommandTest):

    command_module = MODULE_LIST_REPOS_COMMAND

    @pytest.fixture
    def list_repos_cmd(self):
        """Return a fresh ListReposCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_LIST_REPOS_COMMAND)
        return command_mod.ListReposCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with all list-repos arguments set to safe defaults."""
        args = MagicMock()
        args.format = ['json']
        args.repos = None
        args.archived = False
        args.verbose = False
        return args

    @pytest.fixture
    def run_command_setup(self, list_repos_cmd):
        """Activate patches for a successful run with no manifest content; yields key mocks as a namespace."""
        list_repos_cmd.repo_names = {}
        with patch('{}.list_available_manifest_repos'.format(MODULE_LIST_REPOS_COMMAND),
                   return_value=([], [], [])), \
             patch.object(list_repos_cmd, 'generate_repo_names') as mock_generate:
            yield SimpleNamespace(generate_repo_names=mock_generate)

    @staticmethod
    def _run_collect_manifests(list_repos_cmd, args, mock_manifest):
        """Create CI-index mock, run _collect_manifests_from_repo, and return (found_manifests, repo_urls)."""
        found_manifests = {}
        repo_urls = set()
        mock_ci_index = MagicMock()
        mock_ci_index.project_list = [FAKE_PROJECT_NAME]
        mock_ci_index.get_project_xml.return_value = '{}/Manifest.xml'.format(FAKE_PROJECT_NAME)
        with patch('{}.CiIndexXml'.format(MODULE_LIST_REPOS_COMMAND), return_value=mock_ci_index), \
             patch('{}.ManifestXml'.format(MODULE_LIST_REPOS_COMMAND), return_value=mock_manifest):
            list_repos_cmd._collect_manifests_from_repo(
                FAKE_MANIFEST_REPO_NAME, '/fake/dir', args, found_manifests, repo_urls)
        return found_manifests, repo_urls

    def test_run_command_raises_for_invalid_format_type(self, list_repos_cmd, mock_args, mock_config):
        """When an unrecognised format type is passed, EdkrepoInvalidParametersException must be raised."""
        mock_args.format = ['badformat']

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            list_repos_cmd.run_command(mock_args, mock_config)

    def test_run_command_pulls_all_manifest_repos(self, list_repos_cmd, mock_args, mock_config, mock_pull_all_manifest_repos, run_command_setup):
        """run_command must call pull_all_manifest_repos to refresh all configured manifest repos."""
        list_repos_cmd.run_command(mock_args, mock_config)

        mock_pull_all_manifest_repos.assert_called_once()

    def test_run_command_calls_generate_repo_names(self, list_repos_cmd, mock_args, mock_config, run_command_setup, mock_pull_all_manifest_repos):
        """run_command must call generate_repo_names after processing the manifest repos."""
        list_repos_cmd.run_command(mock_args, mock_config)

        run_command_setup.generate_repo_names.assert_called_once()

    def test_run_command_raises_when_requested_repos_not_in_manifest(self, list_repos_cmd, mock_args, mock_config, run_command_setup, mock_pull_all_manifest_repos):
        """When --repos lists names absent from the manifest, EdkrepoInvalidParametersException must be raised."""
        mock_args.repos = ['NonExistentRepo']

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            list_repos_cmd.run_command(mock_args, mock_config)

        run_command_setup.generate_repo_names.assert_called_once()

    def test_collect_manifests_from_repo_populates_found_manifests(self, list_repos_cmd, mock_args):
        """_collect_manifests_from_repo must add an entry to found_manifests keyed by 'repo:project'."""
        mock_manifest = MagicMock()
        mock_manifest.combinations = []

        found_manifests, _ = self._run_collect_manifests(list_repos_cmd, mock_args, mock_manifest)

        assert '{}:{}'.format(FAKE_MANIFEST_REPO_NAME, FAKE_PROJECT_NAME) in found_manifests

    def test_collect_manifests_from_repo_collects_repo_urls(self, list_repos_cmd, mock_args):
        """_collect_manifests_from_repo must add the normalized repo URL to repo_urls."""
        mock_source = MagicMock()
        mock_source.remote_url = 'https://example.com/repo.git'
        mock_combo = MagicMock()
        mock_combo.name = 'ComboA'
        mock_manifest = MagicMock()
        mock_manifest.combinations = [mock_combo]
        mock_manifest.get_repo_sources.return_value = [mock_source]

        _, repo_urls = self._run_collect_manifests(list_repos_cmd, mock_args, mock_manifest)

        assert 'https://example.com/repo' in repo_urls

    def test_generate_repo_names_orders_edk2_and_intel_prefixes_first(self, list_repos_cmd):
        """generate_repo_names sorts names alphabetically, then moves 'edk2'* and 'intel'* names to the front."""
        src_edk2 = SimpleNamespace(root='edk2', remote_url='https://x/edk2.git')
        src_intel = SimpleNamespace(root='inteltools', remote_url='https://x/inteltools.git')
        src_other = SimpleNamespace(root='zztop', remote_url='https://x/zztop.git')
        combo = SimpleNamespace(name='Main')
        manifest = MagicMock()
        manifest.combinations = [combo]
        manifest.get_repo_sources.return_value = [src_edk2, src_intel, src_other]
        manifests = {'ProjA': manifest}
        repo_urls = {'https://x/edk2', 'https://x/inteltools', 'https://x/zztop'}

        list_repos_cmd.generate_repo_names(repo_urls, manifests)

        assert list(list_repos_cmd.repo_names.keys()) == ['inteltools', 'edk2', 'zztop']

    @pytest.mark.parametrize('repo_url, expected', [
        pytest.param('https://example.com/repo.git', 'https://example.com/repo', id='lowercase_git'),
        pytest.param('https://example.com/repo.GIT', 'https://example.com/repo', id='uppercase_git'),
        pytest.param('https://example.com/repo', 'https://example.com/repo', id='no_suffix'),
    ])
    def test_get_repo_url_strips_dot_git_suffix(self, list_repos_cmd, repo_url, expected):
        """get_repo_url must strip a trailing '.git' suffix case-insensitively and leave other URLs unchanged."""
        assert list_repos_cmd.get_repo_url(repo_url) == expected
