#!/usr/bin/env python3
#
## @file
# test_checkout_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.humble.checkout_humble import NO_COMBO
from edkrepo.commands.unit_test_bases import base_tests as bt
from edkrepo.common import edkrepo_exception


MODULE_CHECKOUT_COMMAND = 'edkrepo.commands.checkout_command'

FAKE_COMBINATION = 'CombinationA'
FAKE_GLOBAL_MANIFEST_PATH = '/fake/global/manifest'


class TestCheckoutCommand(bt.BaseCommandTest):

    command_module = MODULE_CHECKOUT_COMMAND

    @pytest.fixture
    def checkout_cmd(self):
        """Return a fresh CheckoutCommand instance for each test."""
        command_mod = importlib.import_module(MODULE_CHECKOUT_COMMAND)
        return command_mod.CheckoutCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with Combination, verbose, and override set."""
        args = MagicMock()
        args.Combination = FAKE_COMBINATION
        args.verbose = False
        args.override = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(MODULE_CHECKOUT_COMMAND)) as mock:
            manifest = MagicMock()
            manifest.general_config.source_manifest_repo = bt.FAKE_MANIFEST_REPO
            mock.return_value = manifest
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_manifest_repo_path(self):
        """Patch get_manifest_repo_path returning FAKE_GLOBAL_MANIFEST_PATH; always active."""
        with patch('{}.get_manifest_repo_path'.format(MODULE_CHECKOUT_COMMAND)) as mock:
            mock.return_value = FAKE_GLOBAL_MANIFEST_PATH
            yield mock

    @pytest.fixture
    def mock_combination_is_in_manifest(self):
        """Patch combination_is_in_manifest in checkout_command; yields the mock."""
        with patch('{}.combination_is_in_manifest'.format(MODULE_CHECKOUT_COMMAND)) as mock:
            yield mock

    @pytest.fixture
    def mock_checkout(self):
        """Patch checkout in checkout_command; yields the mock."""
        with patch('{}.checkout'.format(MODULE_CHECKOUT_COMMAND)) as mock:
            yield mock

    @staticmethod
    def _run_with_valid_combination(checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest):
        """Configure mock_combination_is_in_manifest for a valid combination and execute run_command."""
        mock_combination_is_in_manifest.return_value = True
        checkout_cmd.run_command(mock_args, mock_config)

    @staticmethod
    def _assert_invalid_combination_raises(checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest):
        """Configure mock_combination_is_in_manifest for an invalid combination and assert run_command raises."""
        mock_combination_is_in_manifest.return_value = False
        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            checkout_cmd.run_command(mock_args, mock_config)

    def test_run_command_valid_combination_calls_checkout(self, checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest, mock_checkout):
        """When the combination exists in the manifest, checkout must be called with the resolved args."""
        self._run_with_valid_combination(checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest)

        mock_checkout.assert_called_once_with(
            FAKE_COMBINATION,
            FAKE_GLOBAL_MANIFEST_PATH,
            mock_args.verbose,
            mock_args.override,
        )

    def test_run_command_valid_combination_uses_global_manifest_path_from_manifest_repo(self, checkout_cmd, mock_args, mock_config, mock_get_manifest_repo_path, mock_combination_is_in_manifest, mock_checkout):
        """get_manifest_repo_path must be called with the source_manifest_repo from the workspace manifest."""
        self._run_with_valid_combination(checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest)

        mock_get_manifest_repo_path.assert_called_once_with(bt.FAKE_MANIFEST_REPO, mock_config)

    def test_run_command_invalid_combination_raises_exception(self, checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest):
        """When the combination is not in the manifest, EdkrepoInvalidParametersException must be raised."""
        self._assert_invalid_combination_raises(checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest)

    def test_run_command_invalid_combination_exception_names_combination(self, checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest):
        """The exception message must contain the combination name that was not found."""
        mock_combination_is_in_manifest.return_value = False

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException) as exc_info:
            checkout_cmd.run_command(mock_args, mock_config)

        assert str(exc_info.value) == NO_COMBO.format(FAKE_COMBINATION)

    def test_run_command_invalid_combination_does_not_call_checkout(self, checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest, mock_checkout):
        """When the combination is not in the manifest, checkout must never be called."""
        self._assert_invalid_combination_raises(checkout_cmd, mock_args, mock_config, mock_combination_is_in_manifest)

        mock_checkout.assert_not_called()
