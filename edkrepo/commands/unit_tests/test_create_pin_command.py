#!/usr/bin/env python3
#
## @file
# test_create_pin_command.py
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
from edkrepo_manifest_parser.edk_manifest import ManifestXml, RepoSource


MODULE_CREATE_PIN_COMMAND = 'edkrepo.commands.create_pin_command'

FAKE_PIN_FILE = 'C:\\fake\\pins\\release.xml'
RESOLVED_PIN_FILE = 'C:\\resolved\\pins\\release.xml'
FAKE_DESCRIPTION = 'Test pin description'
REPO_ROOT_1 = 'repo1'
REPO_ROOT_2 = 'repo2'
REPO_ROOT_3 = 'repo3'
REMOTE_URL_1 = 'https://example.com/repo1.git'
REMOTE_URL_2 = 'https://example.com/repo2.git'
BRANCH_MAIN = 'main'
BRANCH_DEVELOP = 'develop'
PATCHSET_1 = 'patchset1'
PATCHSET_2 = 'patchset2'
FAKE_HEXSHA_1 = 'abc123def456'
FAKE_HEXSHA_2 = '789ghi012jkl'
FAKE_HEXSHA_3 = 'commit2sha'
FAKE_HEXSHA_4 = 'commit3sha'
PATCH_GENERATE_PIN_DATA = '_generate_pin_data'


class TestCreatePinCommand(bt.BaseCommandTest):

    command_module = MODULE_CREATE_PIN_COMMAND

    @pytest.fixture
    def create_pin_cmd(self):
        """Return a fresh CreatePinCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_CREATE_PIN_COMMAND)
        return command_mod.CreatePinCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with PinFileName, Description, and verbose set."""
        args = MagicMock()
        args.PinFileName = FAKE_PIN_FILE
        args.Description = FAKE_DESCRIPTION
        args.verbose = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_path(self):
        """Patch get_workspace_path; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_path'.format(MODULE_CREATE_PIN_COMMAND),
                   return_value='C:\\fake\\workspace') as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(MODULE_CREATE_PIN_COMMAND)) as mock:
            manifest = MagicMock()
            manifest.general_config.current_combo = 'main'
            mock.return_value = manifest
            yield mock

    @pytest.fixture
    def run_command_setup(self, create_pin_cmd, mock_get_workspace_manifest):
        """Activate all external patches for a successful run; yields key mocks as a namespace."""
        manifest = mock_get_workspace_manifest.return_value
        with patch('{}.os.path.isfile'.format(MODULE_CREATE_PIN_COMMAND), return_value=False), \
             patch('{}.os.path.exists'.format(MODULE_CREATE_PIN_COMMAND), return_value=True), \
             patch('{}.os.mkdir'.format(MODULE_CREATE_PIN_COMMAND)) as mock_mkdir, \
             patch('{}.ui_functions.print_info_msg'.format(MODULE_CREATE_PIN_COMMAND)), \
             patch.object(create_pin_cmd, PATCH_GENERATE_PIN_DATA, return_value=[]):
            yield SimpleNamespace(
                generate_pin_xml=manifest.generate_pin_xml,
                mkdir=mock_mkdir,
                manifest=manifest,
            )

    @pytest.fixture
    def mock_args_verbose(self):
        """Return a mock args namespace with verbose set to True."""
        args = MagicMock()
        args.verbose = True
        return args

    @pytest.fixture
    def mock_manifest(self):
        """Return a mock ManifestXml with codename and current_combo pre-configured."""
        manifest = MagicMock(spec=ManifestXml)
        manifest.project_info.codename = 'TestProject'
        manifest.general_config.current_combo = BRANCH_MAIN
        return manifest

    @pytest.fixture
    def workspace_path(self):
        """Return a fake workspace root path; repo directory existence is mocked."""
        return bt.FAKE_WORKSPACE_PATH

    @staticmethod
    def _patch_repo_dirs_exist():
        """Return a patch context making every repo source directory appear to exist."""
        return patch('{}.os.path.exists'.format(MODULE_CREATE_PIN_COMMAND), return_value=True)

    @staticmethod
    def _assert_pin_data_entries(result, expected):
        """Assert each result entry's root, commit, and patch_set match the expected (root, commit, patch_set) tuples."""
        assert len(result) == len(expected)
        for entry, (root, commit, patch_set) in zip(result, expected):
            assert entry.root == root
            assert entry.commit == commit
            assert entry.patch_set == patch_set

    @staticmethod
    def _make_repo_source(root, remote_url, branch, patch_set=None):
        """Return a RepoSource with default field values except root, remote_url, branch, and patch_set."""
        return RepoSource(
            root=root,
            remote_name='origin',
            remote_url=remote_url,
            branch=branch,
            commit=None,
            sparse=False,
            enable_submodule=False,
            tag=None,
            venv_cfg=None,
            patch_set=patch_set,
            blobless=False,
            treeless=False
        )

    MOCK_REPO_SOURCES_NO_PATCHSET = [
        _make_repo_source(REPO_ROOT_1, REMOTE_URL_1, BRANCH_MAIN),
        _make_repo_source(REPO_ROOT_2, REMOTE_URL_2, BRANCH_DEVELOP),
    ]

    MOCK_REPO_SOURCES_WITH_PATCHSET = [
        _make_repo_source(REPO_ROOT_1, REMOTE_URL_1, BRANCH_MAIN, PATCHSET_1),
        _make_repo_source(REPO_ROOT_2, REMOTE_URL_2, BRANCH_DEVELOP, PATCHSET_2),
    ]

    def test_run_command_raises_when_pin_file_exists(self, create_pin_cmd, mock_args, mock_config):
        """When the pin file already exists, EdkrepoInvalidParametersException must be raised."""
        with patch('{}.os.path.isfile'.format(MODULE_CREATE_PIN_COMMAND), return_value=True):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                create_pin_cmd.run_command(mock_args, mock_config)

    def test_run_command_creates_directory_when_parent_missing(self, create_pin_cmd, mock_args, mock_config):
        """When the pin file's parent directory does not exist, os.mkdir must be called."""
        with patch('{}.os.path.isfile'.format(MODULE_CREATE_PIN_COMMAND), return_value=False), \
             patch('{}.os.path.exists'.format(MODULE_CREATE_PIN_COMMAND), return_value=False), \
             patch('{}.os.mkdir'.format(MODULE_CREATE_PIN_COMMAND)) as mock_mkdir, \
             patch('{}.ui_functions.print_info_msg'.format(MODULE_CREATE_PIN_COMMAND)), \
             patch.object(create_pin_cmd, PATCH_GENERATE_PIN_DATA, return_value=[]):
            create_pin_cmd.run_command(mock_args, mock_config)

        mock_mkdir.assert_called_once()

    def test_run_command_calls_generate_pin_xml(self, create_pin_cmd, mock_args, mock_config, run_command_setup):
        """generate_pin_xml must be called with the description, current combo, and resolved pin file path."""
        create_pin_cmd.run_command(mock_args, mock_config)

        run_command_setup.generate_pin_xml.assert_called_once_with(
            FAKE_DESCRIPTION,
            run_command_setup.manifest.general_config.current_combo,
            [],
            filename=FAKE_PIN_FILE,
        )

    def test_run_command_skips_mkdir_when_parent_directory_exists(self, create_pin_cmd, mock_args, mock_config, run_command_setup):
        """When the pin file's parent directory already exists, os.mkdir must not be called."""
        create_pin_cmd.run_command(mock_args, mock_config)

        run_command_setup.mkdir.assert_not_called()

    def test_run_command_resolves_relative_pin_path_to_absolute(self, create_pin_cmd, mock_args, mock_config, mock_get_workspace_manifest):
        """A relative PinFileName must be resolved to an absolute path before the pin is written."""
        mock_args.PinFileName = 'pins\\release.xml'
        with patch('{}.os.path.isfile'.format(MODULE_CREATE_PIN_COMMAND), return_value=False), \
             patch('{}.os.path.exists'.format(MODULE_CREATE_PIN_COMMAND), return_value=True), \
             patch('{}.os.path.abspath'.format(MODULE_CREATE_PIN_COMMAND), return_value=RESOLVED_PIN_FILE), \
             patch('{}.ui_functions.print_info_msg'.format(MODULE_CREATE_PIN_COMMAND)), \
             patch.object(create_pin_cmd, PATCH_GENERATE_PIN_DATA, return_value=[]):
            create_pin_cmd.run_command(mock_args, mock_config)

        manifest = mock_get_workspace_manifest.return_value
        assert manifest.generate_pin_xml.call_args.kwargs['filename'] == RESOLVED_PIN_FILE

    def test_generate_pin_data_with_patchset(self, create_pin_cmd, mock_args, mock_manifest, workspace_path):
        """Sources with patchset must be returned as-is without querying the repository HEAD."""
        mock_manifest.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_WITH_PATCHSET

        with self._patch_repo_dirs_exist():
            result = create_pin_cmd._generate_pin_data(mock_args, mock_manifest, workspace_path)

        self._assert_pin_data_entries(result, [
            (REPO_ROOT_1, None, PATCHSET_1),
            (REPO_ROOT_2, None, PATCHSET_2),
        ])

    def test_generate_pin_data_missing_repo_raises_workspace_corrupt(self, create_pin_cmd, mock_args, mock_manifest, workspace_path):
        """When a repo source directory is absent from the workspace, EdkrepoWorkspaceCorruptException must be raised."""
        mock_manifest.get_repo_sources.return_value = self.MOCK_REPO_SOURCES_NO_PATCHSET

        with patch('{}.os.path.exists'.format(MODULE_CREATE_PIN_COMMAND), return_value=False), \
             pytest.raises(edkrepo_exception.EdkrepoWorkspaceCorruptException):
            create_pin_cmd._generate_pin_data(mock_args, mock_manifest, workspace_path)

    @pytest.mark.parametrize('sources, hexshas, expected', [
        pytest.param(
            MOCK_REPO_SOURCES_NO_PATCHSET, [FAKE_HEXSHA_1, FAKE_HEXSHA_2],
            [(REPO_ROOT_1, FAKE_HEXSHA_1, None), (REPO_ROOT_2, FAKE_HEXSHA_2, None)],
            id='no_patchset'
        ),
        pytest.param(
            [
                _make_repo_source(REPO_ROOT_1, REMOTE_URL_1, BRANCH_MAIN, PATCHSET_1),
                _make_repo_source(REPO_ROOT_2, REMOTE_URL_2, BRANCH_DEVELOP),
                _make_repo_source(REPO_ROOT_3, 'https://example.com/repo3.git', 'feature'),
            ], [FAKE_HEXSHA_3, FAKE_HEXSHA_4],
            [(REPO_ROOT_1, None, PATCHSET_1), (REPO_ROOT_2, FAKE_HEXSHA_3, None), (REPO_ROOT_3, FAKE_HEXSHA_4, None)],
            id='mixed_patchset'
        ),
    ])
    def test_generate_pin_data_resolves_commit_for_non_patchset_sources(self, create_pin_cmd, mock_args, mock_manifest, workspace_path, sources, hexshas, expected):
        """Sources without a patchset must have their commit SHA read from HEAD; sources with a patchset must be left untouched."""
        mock_manifest.get_repo_sources.return_value = sources
        repo_mocks = [MagicMock() for _ in hexshas]
        for m, sha in zip(repo_mocks, hexshas):
            m.head.commit.hexsha = sha
        with self._patch_repo_dirs_exist(), \
             patch('{}.Repo'.format(MODULE_CREATE_PIN_COMMAND)) as mock_repo_class:
            mock_repo_class.side_effect = repo_mocks
            result = create_pin_cmd._generate_pin_data(mock_args, mock_manifest, workspace_path)

        self._assert_pin_data_entries(result, expected)

    @pytest.mark.parametrize('sources', [
        pytest.param(MOCK_REPO_SOURCES_NO_PATCHSET, id='no_patchset'),
        pytest.param(MOCK_REPO_SOURCES_WITH_PATCHSET, id='with_patchset'),
    ])
    def test_generate_pin_data_verbose_mode_prints_info_msg(self, create_pin_cmd, mock_args_verbose, mock_manifest, workspace_path, sources):
        """verbose=True must cause print_info_msg to be called at least once regardless of whether sources have patchsets."""
        mock_manifest.get_repo_sources.return_value = sources
        with self._patch_repo_dirs_exist(), \
             patch('{}.Repo'.format(MODULE_CREATE_PIN_COMMAND)) as mock_repo_class, \
             patch('{}.ui_functions'.format(MODULE_CREATE_PIN_COMMAND)) as mock_ui:
            mock_repo_class.return_value.head.commit.hexsha = 'abc123'
            create_pin_cmd._generate_pin_data(mock_args_verbose, mock_manifest, workspace_path)

        assert mock_ui.print_info_msg.call_count > 0
