#!/usr/bin/env python3
#
## @file
# test_checkout_pin_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.checkout_pin_command import (
    CheckoutPinCommand,
    _get_pin_path,
    _find_pin_in_manifest_repo,
    _find_pin_in_workspace,
    _pin_matches_project,
)
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoProjectMismatchException


class TestCheckoutPinCommand:
    """Unit tests for all methods and helper functions in edkrepo/commands/checkout_pin_command.py."""

    WORKSPACE_PATH = '/workspace'
    MANIFEST_REPO_PATH = '/manifest/repo'
    PIN_PATH_SUBDIR = 'pins'
    PIN_FILE_XML = 'test.xml'
    PIN_FILE_NO_EXT = 'test'
    PIN_FILE_MISSING = 'missing.xml'
    ABS_PIN_PATH = '/absolute/path/test.xml'
    PROJECT_A = 'ProjectA'
    PROJECT_B = 'ProjectB'
    REMOTE_NAME = 'origin'
    REMOTE_URL = 'https://example.git'
    EXTRA_REMOTE_URL = 'https://extra.git'
    UPSTREAM_REMOTE = 'upstream'
    COMBO_X = 'COMBO_X'
    COMBO_Y = 'COMBO_Y'
    REPO_ROOT_A = 'repo_a'
    REPO_ROOT_PIN = 'repo_pin'
    REPO_ROOT_MANIFEST = 'repo_manifest'
    COMMIT_SHA = 'abc'
    COMMAND_NAME = 'checkout-pin'
    COMMAND_ALIAS = 'chp'
    META_NAME = 'name'
    META_HELP_TEXT = 'help-text'
    META_ALIAS = 'alias'
    META_ARGUMENTS = 'arguments'
    ARG_PINFILE = 'pinfile'
    ARG_OVERRIDE = 'override'
    ARG_SOURCE_MANIFEST_REPO = 'source-manifest-repo'
    CFG_FILE = 'cfg_file'
    USER_CFG_FILE = 'user_cfg_file'
    PIN_RESOLVED_PATH = '/workspace/pins/test.xml'
    MANIFEST_REPO_NAME = 'repo1'
    REPO_SUBDIR = 'repo'
    COMBO_NOT_FOUND_MSG = 'combo not found'

    def _make_remote(self, name, url):
        r = MagicMock()
        r.name = name
        r.url = url
        return r

    def _make_source(self, root, remote_name, commit='abc'):
        s = MagicMock()
        s.root = root
        s.remote_name = remote_name
        s.commit = commit
        return s

    def _make_pin_args(self, pinfile):
        args = MagicMock()
        args.pinfile = pinfile
        return args

    @pytest.fixture
    def default_remote(self):
        r = MagicMock()
        r.name = self.REMOTE_NAME
        r.url = self.REMOTE_URL
        return r

    @pytest.fixture
    def default_source(self, default_remote):
        s = MagicMock()
        s.root = self.REPO_ROOT_A
        s.remote_name = default_remote.name
        s.commit = self.COMMIT_SHA
        return s

    @pytest.fixture
    def matched_pin_manifest(self, default_remote):
        pin = MagicMock()
        manifest = MagicMock()
        pin.project_info.codename = self.PROJECT_A
        manifest.project_info.codename = self.PROJECT_A
        pin.remotes = [default_remote]
        manifest.remotes = [default_remote]
        pin.general_config.current_combo = self.COMBO_X
        return pin, manifest

    @pytest.fixture
    def mock_pin_repo(self):
        with patch('edkrepo.commands.checkout_pin_command.Repo') as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.commit.return_value = MagicMock()
            mock_repo_cls.return_value = mock_repo
            yield mock_repo

    def test_get_metadata_returns_expected_structure(self):
        cmd = CheckoutPinCommand()
        metadata = cmd.get_metadata()

        assert metadata[self.META_NAME] == self.COMMAND_NAME
        assert metadata[self.META_ALIAS] == self.COMMAND_ALIAS
        assert self.META_HELP_TEXT in metadata
        arg_names = [arg[self.META_NAME] for arg in metadata[self.META_ARGUMENTS]]
        assert self.ARG_PINFILE in arg_names
        assert self.ARG_OVERRIDE in arg_names
        assert self.ARG_SOURCE_MANIFEST_REPO in arg_names

    @patch('edkrepo.commands.checkout_pin_command.maintain_submodules')
    @patch('edkrepo.commands.checkout_pin_command.get_repo_cache_obj', return_value=None)
    @patch('edkrepo.commands.checkout_pin_command.checkout_repos')
    @patch('edkrepo.commands.checkout_pin_command.deinit_full')
    @patch('edkrepo.commands.checkout_pin_command.sparse_checkout_enabled', return_value=False)
    @patch('edkrepo.commands.checkout_pin_command._pin_matches_project')
    @patch('edkrepo.commands.checkout_pin_command.Repo')
    @patch('edkrepo.commands.checkout_pin_command.check_dirty_repos')
    @patch('edkrepo.commands.checkout_pin_command.ManifestXml')
    @patch('edkrepo.commands.checkout_pin_command._get_pin_path', return_value=PIN_RESOLVED_PATH)
    @patch('edkrepo.commands.checkout_pin_command.list_available_manifest_repos')
    @patch('edkrepo.commands.checkout_pin_command.find_source_manifest_repo', return_value=MANIFEST_REPO_NAME)
    @patch('edkrepo.commands.checkout_pin_command.get_workspace_manifest')
    @patch('edkrepo.commands.checkout_pin_command.get_workspace_path', return_value=WORKSPACE_PATH)
    def test_run_command_performs_checkout_and_writes_combo(
        self, mock_gwp, mock_gwm, mock_fsmr, mock_lavmr, mock_gpp,
        mock_manifest_xml_cls, mock_cdr, mock_repo_cls, mock_pmp,
        mock_sce, mock_deinit, mock_checkout_repos, mock_grco, mock_ms,
        default_source
    ):
        mock_manifest = MagicMock()
        mock_manifest.general_config.current_combo = self.COMBO_X
        mock_manifest.get_repo_sources.return_value = [default_source]
        mock_gwm.return_value = mock_manifest

        mock_lavmr.return_value = ([self.MANIFEST_REPO_PATH], [], [])

        mock_pin = MagicMock()
        mock_pin.general_config.current_combo = self.COMBO_X
        mock_pin.get_repo_sources.return_value = [default_source]
        mock_manifest_xml_cls.return_value = mock_pin

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        args = MagicMock()
        args.pinfile = self.PIN_FILE_XML
        args.verbose = False
        args.override = False
        args.source_manifest_repo = None
        config = {self.CFG_FILE: MagicMock(), self.USER_CFG_FILE: MagicMock()}

        CheckoutPinCommand().run_command(args, config)

        mock_checkout_repos.assert_called_once()
        mock_manifest.write_current_combo.assert_called_once()

    @patch('os.path.isfile')
    @patch('os.path.isabs')
    def test_get_pin_path_absolute_path_resolved(self, mock_isabs, mock_isfile):
        mock_isabs.return_value = True
        mock_isfile.return_value = True
        args = self._make_pin_args(self.ABS_PIN_PATH)
        manifest = MagicMock()

        result = _get_pin_path(args, self.WORKSPACE_PATH, self.MANIFEST_REPO_PATH, manifest)

        assert result == os.path.normpath(self.ABS_PIN_PATH)

    @patch('edkrepo.commands.checkout_pin_command._find_pin_in_manifest_repo')
    @patch('os.path.isfile', return_value=False)
    @patch('os.path.isabs', return_value=False)
    def test_get_pin_path_resolved_via_manifest_repo(self, mock_isabs, mock_isfile, mock_find_in_manifest):
        expected = os.path.normpath(os.path.join(self.MANIFEST_REPO_PATH, self.PIN_PATH_SUBDIR, self.PIN_FILE_XML))
        mock_find_in_manifest.return_value = expected
        args = self._make_pin_args(self.PIN_FILE_NO_EXT)
        manifest = MagicMock()
        manifest.general_config.pin_path = self.PIN_PATH_SUBDIR

        result = _get_pin_path(args, self.WORKSPACE_PATH, self.MANIFEST_REPO_PATH, manifest)

        mock_find_in_manifest.assert_called_once_with(self.PIN_FILE_XML, self.MANIFEST_REPO_PATH, self.PIN_PATH_SUBDIR)
        assert result == expected

    @patch('edkrepo.commands.checkout_pin_command._find_pin_in_workspace')
    @patch('os.path.isfile', return_value=False)
    @patch('os.path.isabs', return_value=False)
    def test_get_pin_path_resolved_via_workspace(self, mock_isabs, mock_isfile, mock_find_in_workspace):
        expected = os.path.normpath(os.path.join(self.WORKSPACE_PATH, self.PIN_FILE_XML))
        mock_find_in_workspace.return_value = expected
        args = self._make_pin_args(self.PIN_FILE_XML)
        manifest = MagicMock()

        result = _get_pin_path(args, self.WORKSPACE_PATH, None, manifest)

        mock_find_in_workspace.assert_called_once_with(self.WORKSPACE_PATH, self.PIN_FILE_XML)
        assert result == expected

    @patch('edkrepo.commands.checkout_pin_command._find_pin_in_workspace', return_value=None)
    @patch('os.path.isfile', return_value=False)
    @patch('os.path.isabs', return_value=False)
    def test_get_pin_path_not_found_raises_exception(self, mock_isabs, mock_isfile, mock_find_in_workspace):
        args = self._make_pin_args(self.PIN_FILE_MISSING)
        manifest = MagicMock()

        with pytest.raises(EdkrepoInvalidParametersException):
            _get_pin_path(args, self.WORKSPACE_PATH, None, manifest)

    @patch('os.path.isfile')
    def test_find_pin_in_manifest_repo_found_at_expected_path(self, mock_isfile):
        expected = os.path.normpath(os.path.join(self.MANIFEST_REPO_PATH, self.PIN_PATH_SUBDIR, self.PIN_FILE_XML))
        mock_isfile.side_effect = lambda p: p == expected

        result = _find_pin_in_manifest_repo(self.PIN_FILE_XML, self.MANIFEST_REPO_PATH, self.PIN_PATH_SUBDIR)

        assert result == expected

    @patch('os.path.isfile')
    def test_find_pin_in_manifest_repo_found_at_root(self, mock_isfile):
        root_path = os.path.normpath(os.path.join(self.MANIFEST_REPO_PATH, self.PIN_FILE_XML))
        mock_isfile.side_effect = lambda p: p == root_path

        result = _find_pin_in_manifest_repo(self.PIN_FILE_XML, self.MANIFEST_REPO_PATH, self.PIN_PATH_SUBDIR)

        assert result == root_path

    @patch('os.path.isfile', return_value=False)
    def test_find_pin_in_manifest_repo_not_found_returns_none(self, mock_isfile):
        result = _find_pin_in_manifest_repo(self.PIN_FILE_XML, self.MANIFEST_REPO_PATH, self.PIN_PATH_SUBDIR)

        assert result is None

    @patch('os.path.isfile')
    def test_find_pin_in_workspace_found_at_root(self, mock_isfile):
        root_path = os.path.normpath(os.path.join(self.WORKSPACE_PATH, self.PIN_FILE_XML))
        mock_isfile.side_effect = lambda p: p == root_path

        result = _find_pin_in_workspace(self.WORKSPACE_PATH, self.PIN_FILE_XML)

        assert result == root_path

    @patch('os.path.isfile')
    def test_find_pin_in_workspace_found_in_repo_subdir(self, mock_isfile):
        repo_path = os.path.normpath(os.path.join(self.WORKSPACE_PATH, self.REPO_SUBDIR, self.PIN_FILE_XML))
        mock_isfile.side_effect = lambda p: p == repo_path

        result = _find_pin_in_workspace(self.WORKSPACE_PATH, self.PIN_FILE_XML)

        assert result == repo_path

    @patch('os.path.isfile', return_value=False)
    def test_find_pin_in_workspace_not_found_returns_none(self, mock_isfile):
        result = _find_pin_in_workspace(self.WORKSPACE_PATH, self.PIN_FILE_XML)

        assert result is None

    @patch('edkrepo.commands.checkout_pin_command.combinations_in_manifest')
    def test_pin_matches_project_codename_mismatch_raises_exception(self, mock_combos):
        pin = MagicMock()
        manifest = MagicMock()
        pin.project_info.codename = self.PROJECT_A
        manifest.project_info.codename = self.PROJECT_B
        pin.remotes = []
        manifest.remotes = []

        with pytest.raises(EdkrepoProjectMismatchException):
            _pin_matches_project(pin, manifest, self.WORKSPACE_PATH)

    @patch('edkrepo.commands.checkout_pin_command.combinations_in_manifest')
    def test_pin_matches_project_remotes_not_subset_raises_exception(self, mock_combos):
        pin = MagicMock()
        manifest = MagicMock()
        pin.project_info.codename = self.PROJECT_A
        manifest.project_info.codename = self.PROJECT_A
        pin.remotes = [self._make_remote(self.REMOTE_NAME, self.EXTRA_REMOTE_URL)]
        manifest.remotes = []

        with pytest.raises(EdkrepoProjectMismatchException):
            _pin_matches_project(pin, manifest, self.WORKSPACE_PATH)

    @patch('edkrepo.commands.checkout_pin_command.ui_functions')
    @patch('edkrepo.commands.checkout_pin_command.combinations_in_manifest')
    def test_pin_matches_project_combo_not_in_manifest_prints_warning(
        self, mock_combos, mock_ui, mock_pin_repo, matched_pin_manifest, default_source
    ):
        pin, manifest = matched_pin_manifest
        mock_combos.return_value = [self.COMBO_Y]
        pin.get_repo_sources.return_value = [default_source]
        manifest.get_repo_sources.return_value = [default_source]

        _pin_matches_project(pin, manifest, self.WORKSPACE_PATH)

        mock_ui.print_warning_msg.assert_called_once()

    @patch('edkrepo.commands.checkout_pin_command.combinations_in_manifest')
    def test_pin_matches_project_root_remote_disjoint_raises_exception(
        self, mock_combos, matched_pin_manifest
    ):
        pin, manifest = matched_pin_manifest
        mock_combos.return_value = [self.COMBO_X]
        pin_source = self._make_source(self.REPO_ROOT_PIN, self.REMOTE_NAME)
        manifest_source = self._make_source(self.REPO_ROOT_MANIFEST, self.UPSTREAM_REMOTE)
        pin.get_repo_sources.return_value = [pin_source]
        manifest.get_repo_sources.return_value = [manifest_source]

        with pytest.raises(EdkrepoProjectMismatchException):
            _pin_matches_project(pin, manifest, self.WORKSPACE_PATH)

    @patch('edkrepo.commands.checkout_pin_command.combinations_in_manifest')
    def test_pin_matches_project_all_validations_pass(
        self, mock_combos, mock_pin_repo, matched_pin_manifest, default_source
    ):
        pin, manifest = matched_pin_manifest
        mock_combos.return_value = [self.COMBO_X]
        pin.get_repo_sources.return_value = [default_source]
        manifest.get_repo_sources.return_value = [default_source]

        _pin_matches_project(pin, manifest, self.WORKSPACE_PATH)

        mock_pin_repo.commit.assert_called_once_with(self.COMMIT_SHA)

    @patch('edkrepo.commands.checkout_pin_command.combinations_in_manifest')
    def test_pin_matches_project_value_error_falls_back_to_default_combo(
        self, mock_combos, mock_pin_repo, matched_pin_manifest, default_source
    ):
        pin, manifest = matched_pin_manifest
        mock_combos.return_value = [self.COMBO_X]
        pin.get_repo_sources.return_value = [default_source]
        manifest.get_repo_sources.side_effect = [ValueError(self.COMBO_NOT_FOUND_MSG), [default_source]]

        _pin_matches_project(pin, manifest, self.WORKSPACE_PATH)

        assert manifest.get_repo_sources.call_count == 2
        manifest.get_repo_sources.assert_called_with(manifest.general_config.default_combo)
