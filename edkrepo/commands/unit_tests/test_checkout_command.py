#!/usr/bin/env python3
#
## @file
# test_checkout_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.checkout_command import CheckoutCommand, _checkout_combination
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException


class TestCheckoutCommand:
    """Unit tests for all methods and helper functions in edkrepo/commands/checkout_command.py."""

    COMBINATION_DEV = "DEV"
    COMBINATION_MISSING = "MISSING"
    GLOBAL_MANIFEST_PATH = "/global/manifest/path"
    MANIFEST_REPO = "repo1"

    CFG_FILE = "cfg_file"
    USER_CFG_FILE = "user_cfg_file"
    COMMAND_NAME = "checkout"
    META_NAME = "name"
    META_HELP_TEXT = "help-text"
    META_ARGUMENTS = "arguments"
    ARG_COMBINATION = "Combination"
    ARG_OVERRIDE = "override"

    # get_metadata

    def test_get_metadata_returns_expected_structure(self):
        cmd = CheckoutCommand()
        metadata = cmd.get_metadata()

        assert metadata[self.META_NAME] == self.COMMAND_NAME
        assert self.META_HELP_TEXT in metadata
        arg_names = [a[self.META_NAME] if isinstance(a, dict) and self.META_NAME in a else None
                     for a in metadata[self.META_ARGUMENTS]]
        assert self.ARG_COMBINATION in arg_names
        assert self.ARG_OVERRIDE in arg_names

    # run_command

    @patch('edkrepo.commands.checkout_command._checkout_combination')
    @patch('edkrepo.commands.checkout_command.get_workspace_manifest')
    @patch('edkrepo.commands.checkout_command.get_manifest_repo_path', return_value=GLOBAL_MANIFEST_PATH)
    def test_run_command_resolves_manifest_and_delegates(self, mock_get_manifest_repo_path, mock_get_workspace_manifest, mock_checkout_combination):
        mock_manifest = MagicMock()
        mock_manifest.general_config.source_manifest_repo = self.MANIFEST_REPO
        mock_get_workspace_manifest.return_value = mock_manifest
        args = MagicMock()
        args.Combination = self.COMBINATION_DEV
        args.verbose = True
        args.override = False
        config = {self.CFG_FILE: MagicMock(), self.USER_CFG_FILE: MagicMock()}

        CheckoutCommand().run_command(args, config)

        mock_checkout_combination.assert_called_once_with(
            self.COMBINATION_DEV, mock_manifest, self.GLOBAL_MANIFEST_PATH, True, False, config
        )

    # _checkout_combination

    @patch('edkrepo.commands.checkout_command.checkout')
    @patch('edkrepo.commands.checkout_command.get_repo_cache_obj')
    @patch('edkrepo.commands.checkout_command.combination_is_in_manifest', return_value=True)
    def test_valid_combination_triggers_checkout(self, mock_combination_is_in_manifest, mock_get_repo_cache_obj, mock_checkout):
        mock_manifest = MagicMock()
        mock_cache = MagicMock()
        mock_get_repo_cache_obj.return_value = mock_cache
        config = {self.CFG_FILE: MagicMock(), self.USER_CFG_FILE: MagicMock()}

        _checkout_combination(self.COMBINATION_DEV, mock_manifest, self.GLOBAL_MANIFEST_PATH, False, False, config)

        mock_checkout.assert_called_once_with(self.COMBINATION_DEV, self.GLOBAL_MANIFEST_PATH, False, False, mock_cache)

    @patch('edkrepo.commands.checkout_command.checkout')
    @patch('edkrepo.commands.checkout_command.combination_is_in_manifest', return_value=False)
    def test_invalid_combination_raises_exception(self, mock_combination_is_in_manifest, mock_checkout):
        mock_manifest = MagicMock()
        config = {self.CFG_FILE: MagicMock(), self.USER_CFG_FILE: MagicMock()}

        with pytest.raises(EdkrepoInvalidParametersException):
            _checkout_combination(self.COMBINATION_MISSING, mock_manifest, self.GLOBAL_MANIFEST_PATH, False, False, config)

        mock_checkout.assert_not_called()

