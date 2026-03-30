#!/usr/bin/env python3
#
## @file
# test_general_config.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_text_element,
    make_attrib_element,
    CHILD_PIN_PATH,
    CHILD_DEFAULT_COMBO,
    CHILD_CURR_COMBO,
    CHILD_SOURCE_MANIFEST_REPO,
    PIN_PATH,
    DEFAULT_COMBO,
    CURR_COMBO,
    SOURCE_MANIFEST_REPO,
    ATTRIB_COMBINATION,
    ATTRIB_MANIFEST_REPO,
    FIELD_PIN_PATH,
    FIELD_DEFAULT_COMBO,
    FIELD_CURR_COMBO,
    FIELD_SOURCE_MANIFEST_REPO,
)
from edkrepo_manifest_parser.edk_manifest import _GeneralConfig, GeneralConfig


class TestGeneralConfig:

    @staticmethod
    def _make_mock_element(find_map=None):
        """Build a mock XML element whose find() returns values from find_map, or None for absent keys."""
        elem = MagicMock()
        fm = find_map if find_map is not None else {}
        elem.find.side_effect = lambda tag: fm.get(tag)
        return elem

    @staticmethod
    def _assert_field_present(find_map, field_name, expected):
        """Build a _GeneralConfig from an element containing find_map and assert field_name equals expected."""
        config = _GeneralConfig(TestGeneralConfig._make_mock_element(find_map))
        assert getattr(config, field_name) == expected

    @pytest.fixture
    def empty_config(self):
        """Return a _GeneralConfig built from an element with no children so all fields default to None."""
        return _GeneralConfig(self._make_mock_element({}))

    def test_init_sets_pin_path_when_present(self):
        """When the PinPath child element is present, __init__ must set self.pin_path to its text value."""
        self._assert_field_present(
            {CHILD_PIN_PATH: make_text_element(PIN_PATH)},
            FIELD_PIN_PATH,
            PIN_PATH,
        )

    def test_init_sets_pin_path_to_none_when_absent(self, empty_config):
        """When the PinPath child element is absent, __init__ must set self.pin_path to None."""
        assert getattr(empty_config, FIELD_PIN_PATH) is None

    def test_init_sets_default_combo_when_present(self):
        """When the DefaultCombo child element is present, __init__ must set self.default_combo to its combination attribute."""
        self._assert_field_present(
            {CHILD_DEFAULT_COMBO: make_attrib_element({ATTRIB_COMBINATION: DEFAULT_COMBO})},
            FIELD_DEFAULT_COMBO,
            DEFAULT_COMBO,
        )

    def test_init_sets_default_combo_to_none_when_absent(self, empty_config):
        """When the DefaultCombo child element is absent, __init__ must set self.default_combo to None."""
        assert getattr(empty_config, FIELD_DEFAULT_COMBO) is None

    def test_init_sets_curr_combo_when_present(self):
        """When the CurrentClonedCombo child element is present, __init__ must set self.curr_combo to its combination attribute."""
        self._assert_field_present(
            {CHILD_CURR_COMBO: make_attrib_element({ATTRIB_COMBINATION: CURR_COMBO})},
            FIELD_CURR_COMBO,
            CURR_COMBO,
        )

    def test_init_sets_curr_combo_to_none_when_absent(self, empty_config):
        """When the CurrentClonedCombo child element is absent, __init__ must set self.curr_combo to None."""
        assert getattr(empty_config, FIELD_CURR_COMBO) is None

    def test_init_sets_source_manifest_repo_when_present(self):
        """When the SourceManifestRepository child element is present, __init__ must set self.source_manifest_repo to its manifest_repo attribute."""
        self._assert_field_present(
            {CHILD_SOURCE_MANIFEST_REPO: make_attrib_element({ATTRIB_MANIFEST_REPO: SOURCE_MANIFEST_REPO})},
            FIELD_SOURCE_MANIFEST_REPO,
            SOURCE_MANIFEST_REPO,
        )

    def test_init_sets_source_manifest_repo_to_none_when_absent(self, empty_config):
        """When the SourceManifestRepository child element is absent, __init__ must set self.source_manifest_repo to None."""
        assert getattr(empty_config, FIELD_SOURCE_MANIFEST_REPO) is None

    def test_tuple_returns_correct_general_config_namedtuple(self):
        """The tuple property must return a GeneralConfig namedtuple with the correct field values."""
        find_map = {
            CHILD_PIN_PATH: make_text_element(PIN_PATH),
            CHILD_DEFAULT_COMBO: make_attrib_element({ATTRIB_COMBINATION: DEFAULT_COMBO}),
            CHILD_CURR_COMBO: make_attrib_element({ATTRIB_COMBINATION: CURR_COMBO}),
            CHILD_SOURCE_MANIFEST_REPO: make_attrib_element({ATTRIB_MANIFEST_REPO: SOURCE_MANIFEST_REPO}),
        }
        result = _GeneralConfig(self._make_mock_element(find_map)).tuple

        assert result == GeneralConfig(
            default_combo=DEFAULT_COMBO,
            current_combo=CURR_COMBO,
            pin_path=PIN_PATH,
            source_manifest_repo=SOURCE_MANIFEST_REPO,
        )
