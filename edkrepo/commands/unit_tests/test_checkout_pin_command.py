#!/usr/bin/env python3
#
## @file
# test_checkout_pin_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import os
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.humble import checkout_pin_humble as humble
from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_CHECKOUT_PIN_COMMAND = 'edkrepo.commands.checkout_pin_command'

FAKE_PINFILE = 'test_pin.xml'
FAKE_MANIFEST_REPO_PATH = '/fake/manifest_repo'
FAKE_PIN_SUBDIR = 'pins'
FAKE_RESOLVED_PIN_PATH = '/fake/manifest_repo/pins/test_pin.xml'
FAKE_COMBO = 'combo1'
FAKE_CODENAME = 'ProjectX'
FAKE_REMOTE_NAME = 'origin'
FAKE_ROOT_REPO = 'repo1'
PATCH_COMBINATIONS_IN_MANIFEST = '{}.combinations_in_manifest'.format(MODULE_CHECKOUT_PIN_COMMAND)
PATCH_OS_PATH_ISABS = 'os.path.isabs'
PATCH_OS_PATH_ISFILE = 'os.path.isfile'


class TestCheckoutPinCommand(bt.BaseCommandTest):

    command_module = MODULE_CHECKOUT_PIN_COMMAND

    @pytest.fixture
    def pin_cmd(self):
        """Return a fresh CheckoutPinCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_CHECKOUT_PIN_COMMAND)
        return command_mod.CheckoutPinCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with pinfile, verbose, override, and source_manifest_repo set."""
        args = MagicMock()
        args.pinfile = FAKE_PINFILE
        args.verbose = False
        args.override = False
        args.source_manifest_repo = None
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest returning a manifest with empty sources; always active."""
        with patch('{}.get_workspace_manifest'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock:
            manifest = MagicMock()
            manifest.general_config.source_manifest_repo = bt.FAKE_MANIFEST_REPO
            manifest.general_config.current_combo = FAKE_COMBO
            manifest.get_repo_sources.return_value = []
            mock.return_value = manifest
            yield mock

    @pytest.fixture(autouse=True)
    def mock_find_source_manifest_repo(self):
        """Patch find_source_manifest_repo returning bt.FAKE_MANIFEST_REPO; always active."""
        with patch('{}.find_source_manifest_repo'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock:
            mock.return_value = bt.FAKE_MANIFEST_REPO
            yield mock

    @pytest.fixture(autouse=True)
    def mock_list_available_manifest_repos(self):
        """Patch list_available_manifest_repos returning bt.FAKE_MANIFEST_REPO in cfg; always active."""
        with patch('{}.list_available_manifest_repos'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock:
            mock.return_value = ([bt.FAKE_MANIFEST_REPO], [], [])
            yield mock

    @pytest.fixture(autouse=True)
    def mock_manifest_xml(self):
        """Patch ManifestXml returning a pre-configured pin mock; always active."""
        with patch('{}.ManifestXml'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock_cls:
            pin = MagicMock()
            pin.general_config.current_combo = FAKE_COMBO
            pin.get_repo_sources.return_value = []
            mock_cls.return_value = pin
            yield mock_cls

    @pytest.fixture(autouse=True)
    def mock_deinit_full(self):
        """Patch deinit_full; always active."""
        with patch('{}.deinit_full'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_maintain_submodules(self):
        """Patch maintain_submodules; always active."""
        with patch('{}.maintain_submodules'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_checkout_repos(self):
        """Patch checkout_repos; always active."""
        with patch('{}.checkout_repos'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock:
            yield mock

    @pytest.fixture
    def pin_cmd_isolated(self):
        """Return a CheckoutPinCommand with private methods patched for run_command tests."""
        command_mod = importlib.import_module(MODULE_CHECKOUT_PIN_COMMAND)
        cmd = command_mod.CheckoutPinCommand()
        with patch.object(cmd, '_CheckoutPinCommand__get_pin_path', return_value=FAKE_PINFILE), \
             patch.object(cmd, '_CheckoutPinCommand__pin_matches_project'):
            yield cmd

    @staticmethod
    def _make_mock_remote(name=FAKE_REMOTE_NAME, url='https://fake.repo/project.git'):
        """Build a mock remote object with name and url."""
        remote = MagicMock()
        remote.name = name
        remote.url = url
        return remote

    @staticmethod
    def _make_mock_source(root=FAKE_ROOT_REPO, remote_name=FAKE_REMOTE_NAME, commit='abc123'):
        """Build a mock repo source with configurable root, remote_name, and commit."""
        source = MagicMock()
        source.root = root
        source.remote_name = remote_name
        source.commit = commit
        return source

    @staticmethod
    def _make_matching_pin_and_manifest():
        """Build a pin/manifest MagicMock pair sharing the same codename, remotes, and a single repo source."""
        remote = TestCheckoutPinCommand._make_mock_remote()
        source = TestCheckoutPinCommand._make_mock_source()
        pin = MagicMock()
        pin.project_info.codename = FAKE_CODENAME
        pin.remotes = [remote]
        pin.general_config.current_combo = FAKE_COMBO
        pin.get_repo_sources.return_value = [source]
        manifest = MagicMock()
        manifest.project_info.codename = FAKE_CODENAME
        manifest.remotes = [remote]
        manifest.get_repo_sources.return_value = [source]
        return pin, manifest

    @staticmethod
    def _assert_pin_mismatch_raises(pin_cmd, pin, manifest):
        """Assert that __pin_matches_project raises EdkrepoProjectMismatchException."""
        with pytest.raises(edkrepo_exception.EdkrepoProjectMismatchException):
            pin_cmd._CheckoutPinCommand__pin_matches_project(pin, manifest, bt.FAKE_WORKSPACE_PATH)

    def test_run_command_calls_check_dirty_repos(self, pin_cmd_isolated, mock_args, mock_config, mock_get_workspace_manifest, mock_check_dirty_repos, mock_get_workspace_path, mock_sparse_checkout_enabled):
        """check_dirty_repos must be called with the workspace manifest and workspace path."""
        pin_cmd_isolated.run_command(mock_args, mock_config)

        mock_check_dirty_repos.assert_called_once_with(
            mock_get_workspace_manifest.return_value, bt.FAKE_WORKSPACE_PATH
        )

    def test_run_command_writes_pin_combo_name(self, pin_cmd_isolated, mock_args, mock_config, mock_get_workspace_manifest, mock_get_workspace_path, mock_sparse_checkout_enabled, mock_check_dirty_repos):
        """write_current_combo must be called using PIN_COMBO format with the pin filename."""
        pin_cmd_isolated.run_command(mock_args, mock_config)

        mock_get_workspace_manifest.return_value.write_current_combo.assert_called_once_with(
            humble.PIN_COMBO.format(FAKE_PINFILE)
        )

    def test_run_command_performs_sparse_reset_when_enabled(self, pin_cmd_isolated, mock_args, mock_config, mock_sparse_checkout_enabled, mock_reset_sparse_checkout, mock_get_workspace_path, mock_check_dirty_repos, mock_sparse_checkout):
        """When sparse checkout is enabled, reset_sparse_checkout must be called before checkout."""
        mock_sparse_checkout_enabled.return_value = True

        pin_cmd_isolated.run_command(mock_args, mock_config)

        mock_reset_sparse_checkout.assert_called_once()

    def test_run_command_deinit_error_does_not_stop_checkout(self, pin_cmd_isolated, mock_args, mock_config, mock_deinit_full, mock_checkout_repos, mock_get_workspace_path, mock_sparse_checkout_enabled, mock_check_dirty_repos):
        """An exception from deinit_full must be caught and checkout_repos must still be called."""
        mock_deinit_full.side_effect = Exception('deinit failed')

        pin_cmd_isolated.run_command(mock_args, mock_config)

        mock_checkout_repos.assert_called_once()

    def test_run_command_maintains_submodules_even_when_checkout_raises(self, pin_cmd_isolated, mock_args, mock_config, mock_maintain_submodules, mock_checkout_repos, mock_get_workspace_path, mock_sparse_checkout_enabled, mock_check_dirty_repos):
        """maintain_submodules must be called in the finally block even when checkout_repos raises."""
        mock_checkout_repos.side_effect = Exception('checkout failed')

        with pytest.raises(Exception):
            pin_cmd_isolated.run_command(mock_args, mock_config)

        mock_maintain_submodules.assert_called_once()

    def test_pin_matches_project_raises_when_codename_differs(self, pin_cmd):
        """When pin and manifest codenames differ, EdkrepoProjectMismatchException must be raised."""
        pin = MagicMock()
        pin.project_info.codename = 'OtherProject'
        manifest = MagicMock()
        manifest.project_info.codename = FAKE_CODENAME

        self._assert_pin_mismatch_raises(pin_cmd, pin, manifest)

    def test_pin_matches_project_raises_when_pin_remotes_not_subset(self, pin_cmd):
        """When pin remotes are not a subset of manifest remotes, EdkrepoProjectMismatchException must be raised."""
        remote = self._make_mock_remote()
        pin = MagicMock()
        pin.project_info.codename = FAKE_CODENAME
        pin.remotes = [remote]
        manifest = MagicMock()
        manifest.project_info.codename = FAKE_CODENAME
        manifest.remotes = []

        self._assert_pin_mismatch_raises(pin_cmd, pin, manifest)

    def test_pin_matches_project_warns_when_combo_not_in_manifest(self, pin_cmd, mock_print_warning_msg):
        """When the pin combo is not in the manifest, print_warning_msg must be called with the combo name."""
        pin, manifest = self._make_matching_pin_and_manifest()
        with patch(PATCH_COMBINATIONS_IN_MANIFEST, return_value=[]), \
             patch('{}.Repo'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock_repo:
            mock_repo.return_value.commit.return_value = MagicMock()
            pin_cmd._CheckoutPinCommand__pin_matches_project(pin, manifest, bt.FAKE_WORKSPACE_PATH)

        mock_print_warning_msg.assert_called_once()
        assert FAKE_COMBO in str(mock_print_warning_msg.call_args)

    def test_pin_matches_project_raises_when_root_remote_pairs_disjoint(self, pin_cmd):
        """When pin and manifest source root/remote pairs share nothing, EdkrepoProjectMismatchException must be raised."""
        remote = self._make_mock_remote()
        pin_source = self._make_mock_source(root=FAKE_ROOT_REPO, remote_name=FAKE_REMOTE_NAME)
        manifest_source = self._make_mock_source(root='repo2', remote_name='other_remote')
        pin = MagicMock()
        pin.project_info.codename = FAKE_CODENAME
        pin.remotes = [remote]
        pin.general_config.current_combo = FAKE_COMBO
        pin.get_repo_sources.return_value = [pin_source]
        manifest = MagicMock()
        manifest.project_info.codename = FAKE_CODENAME
        manifest.remotes = [remote]
        manifest.get_repo_sources.return_value = [manifest_source]
        with patch(PATCH_COMBINATIONS_IN_MANIFEST, return_value=[FAKE_COMBO]):
            self._assert_pin_mismatch_raises(pin_cmd, pin, manifest)

    def test_pin_matches_project_raises_when_pin_commit_not_found_in_repo(self, pin_cmd):
        """When the pinned commit cannot be found in the local repo, EdkrepoProjectMismatchException must be raised."""
        pin, manifest = self._make_matching_pin_and_manifest()
        with patch(PATCH_COMBINATIONS_IN_MANIFEST, return_value=[FAKE_COMBO]), \
             patch('{}.Repo'.format(MODULE_CHECKOUT_PIN_COMMAND)) as mock_repo:
            mock_repo.return_value.commit.return_value = None

            self._assert_pin_mismatch_raises(pin_cmd, pin, manifest)

    def test_get_pin_path_returns_normalized_path_when_pinfile_is_absolute_existing_file(self, pin_cmd, mock_get_workspace_manifest):
        """When args.pinfile is an absolute path to an existing file, it must be returned normalized without delegating."""
        args = MagicMock()
        args.pinfile = '/abs/path/test_pin.xml'
        with patch(PATCH_OS_PATH_ISABS, return_value=True), \
             patch(PATCH_OS_PATH_ISFILE, return_value=True):
            result = pin_cmd._CheckoutPinCommand__get_pin_path(
                args, bt.FAKE_WORKSPACE_PATH, None,
                mock_get_workspace_manifest.return_value,
            )

        assert result == os.path.normpath(args.pinfile)

    def test_get_pin_path_delegates_to_find_pin_in_manifest_repo_when_manifest_repo_path_given(self, pin_cmd, mock_get_workspace_manifest):
        """When manifest_repo_path is given, __get_pin_path must delegate to __find_pin_in_manifest_repo."""
        args = MagicMock()
        args.pinfile = FAKE_PINFILE
        manifest = mock_get_workspace_manifest.return_value
        manifest.general_config.pin_path = FAKE_PIN_SUBDIR
        with patch(PATCH_OS_PATH_ISABS, return_value=False), \
             patch.object(pin_cmd, '_CheckoutPinCommand__find_pin_in_manifest_repo', return_value=FAKE_RESOLVED_PIN_PATH) as mock_find:
            result = pin_cmd._CheckoutPinCommand__get_pin_path(
                args, bt.FAKE_WORKSPACE_PATH, FAKE_MANIFEST_REPO_PATH, manifest,
            )

        mock_find.assert_called_once_with(FAKE_PINFILE, FAKE_MANIFEST_REPO_PATH, FAKE_PIN_SUBDIR)
        assert result == FAKE_RESOLVED_PIN_PATH

    @pytest.mark.parametrize('which_exists', [
        pytest.param('subdir', id='found_in_pin_path_subdir'),
        pytest.param('root', id='found_at_manifest_repo_root'),
        pytest.param(None, id='not_found'),
    ])
    def test_find_pin_in_manifest_repo_checks_subdir_then_root(self, pin_cmd, which_exists):
        """__find_pin_in_manifest_repo must check the pin_path subdir first, fall back to the repo root, then return None."""
        expected_subdir_path = os.path.normpath(os.path.join(FAKE_MANIFEST_REPO_PATH, FAKE_PIN_SUBDIR, FAKE_PINFILE))
        expected_root_path = os.path.normpath(os.path.join(FAKE_MANIFEST_REPO_PATH, FAKE_PINFILE))

        def fake_isfile(path):
            """Report the subdir or root path as existing based on which_exists."""
            if which_exists == 'subdir':
                return path == expected_subdir_path
            if which_exists == 'root':
                return path == expected_root_path
            return False

        with patch(PATCH_OS_PATH_ISFILE, side_effect=fake_isfile):
            result = pin_cmd._CheckoutPinCommand__find_pin_in_manifest_repo(
                FAKE_PINFILE, FAKE_MANIFEST_REPO_PATH, FAKE_PIN_SUBDIR
            )

        if which_exists == 'subdir':
            assert result == expected_subdir_path
        elif which_exists == 'root':
            assert result == expected_root_path
        else:
            assert result is None

    @pytest.mark.parametrize('which_exists', [
        pytest.param('root', id='found_at_workspace_root'),
        pytest.param('repo_dir', id='found_in_repo_dir'),
        pytest.param(None, id='not_found'),
    ])
    def test_find_pin_in_workspace_checks_root_then_repo_dir(self, pin_cmd, which_exists):
        """__find_pin_in_workspace must check the workspace root first, fall back to the repo/ dir, then return None."""
        expected_root_path = os.path.normpath(os.path.join(bt.FAKE_WORKSPACE_PATH, FAKE_PINFILE))
        expected_repo_dir_path = os.path.normpath(os.path.join(bt.FAKE_WORKSPACE_PATH, 'repo', FAKE_PINFILE))

        def fake_isfile(path):
            """Report the workspace root or repo/ dir path as existing based on which_exists."""
            if which_exists == 'root':
                return path == expected_root_path
            if which_exists == 'repo_dir':
                return path == expected_repo_dir_path
            return False

        with patch(PATCH_OS_PATH_ISFILE, side_effect=fake_isfile):
            result = pin_cmd._CheckoutPinCommand__find_pin_in_workspace(bt.FAKE_WORKSPACE_PATH, FAKE_PINFILE)

        if which_exists == 'root':
            assert result == expected_root_path
        elif which_exists == 'repo_dir':
            assert result == expected_repo_dir_path
        else:
            assert result is None

    @pytest.mark.parametrize('pinfile', [
        pytest.param('test_pin', id='no_xml_extension'),
        pytest.param(FAKE_PINFILE, id='with_xml_extension'),
    ])
    def test_get_pin_path_raises_when_pin_cannot_be_located(self, pin_cmd, mock_get_workspace_manifest, pinfile):
        """When the pin file cannot be found in the workspace, EdkrepoInvalidParametersException must be raised."""
        args = MagicMock()
        args.pinfile = pinfile
        with patch(PATCH_OS_PATH_ISABS, return_value=False), \
             patch.object(pin_cmd, '_CheckoutPinCommand__find_pin_in_workspace', return_value=None), \
             pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            pin_cmd._CheckoutPinCommand__get_pin_path(
                args, bt.FAKE_WORKSPACE_PATH, None,
                mock_get_workspace_manifest.return_value,
            )

        assert humble.NOT_FOUND in str(exc_info.value)
