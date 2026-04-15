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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

CHILD_PIN_PATH = 'PinPath'
CHILD_DEFAULT_COMBO = 'DefaultCombo'
CHILD_CURR_COMBO = 'CurrentClonedCombo'
CHILD_SOURCE_MANIFEST_REPO = 'SourceManifestRepository'
ATTRIB_MANIFEST_REPO = 'manifest_repo'
PIN_PATH = '/fake/pin.xml'
SOURCE_MANIFEST_REPO = 'edk2-manifest'
FIELD_PIN_PATH = 'pin_path'
FIELD_DEFAULT_COMBO = 'default_combo'
FIELD_CURR_COMBO = 'curr_combo'
FIELD_SOURCE_MANIFEST_REPO = 'source_manifest_repo'
ID_PIN_PATH_ABSENT = 'pin_path_absent'
ID_DEFAULT_COMBO_ABSENT = 'default_combo_absent'
ID_CURR_COMBO_ABSENT = 'curr_combo_absent'
ID_SOURCE_REPO_ABSENT = 'source_manifest_repo_absent'


class TestGeneralConfig:

    @staticmethod
    def _make_mock_element(find_map=None):
        """Build a mock XML element whose find() returns values from find_map, or None for absent keys."""
        return helpers.make_find_map_element(find_map)

    @staticmethod
    def _assert_field_present(find_map, field_name, expected):
        """Build a edk_manifest._GeneralConfig from an element containing find_map and assert field_name equals expected."""
        config = edk_manifest._GeneralConfig(TestGeneralConfig._make_mock_element(find_map))
        assert getattr(config, field_name) == expected

    @pytest.fixture
    def empty_config(self):
        """Return a edk_manifest._GeneralConfig built from an element with no children so all fields default to None."""
        return edk_manifest._GeneralConfig(self._make_mock_element({}))

    def test_init_sets_pin_path_when_present(self):
        """When the PinPath child element is present, __init__ must set self.pin_path to its text value."""
        self._assert_field_present(
            {CHILD_PIN_PATH: helpers.make_text_element(PIN_PATH)},
            FIELD_PIN_PATH,
            PIN_PATH,
        )

    def test_init_sets_default_combo_when_present(self):
        """When the DefaultCombo child element is present, __init__ must set self.default_combo to its combination attribute."""
        self._assert_field_present(
            {CHILD_DEFAULT_COMBO: helpers.make_attrib_element({helpers.ATTRIB_COMBINATION: helpers.BRANCH})},
            FIELD_DEFAULT_COMBO,
            helpers.BRANCH,
        )

    def test_init_sets_curr_combo_when_present(self):
        """When the CurrentClonedCombo child element is present, __init__ must set self.curr_combo to its combination attribute."""
        self._assert_field_present(
            {CHILD_CURR_COMBO: helpers.make_attrib_element({helpers.ATTRIB_COMBINATION: helpers.DEV})},
            FIELD_CURR_COMBO,
            helpers.DEV,
        )

    def test_init_sets_source_manifest_repo_when_present(self):
        """When the SourceManifestRepository child element is present, __init__ must set self.source_manifest_repo to its manifest_repo attribute."""
        self._assert_field_present(
            {CHILD_SOURCE_MANIFEST_REPO: helpers.make_attrib_element({ATTRIB_MANIFEST_REPO: SOURCE_MANIFEST_REPO})},
            FIELD_SOURCE_MANIFEST_REPO,
            SOURCE_MANIFEST_REPO,
        )

    @pytest.mark.parametrize(helpers.PARAM_FIELD_NAME, [
        pytest.param(FIELD_PIN_PATH, id=ID_PIN_PATH_ABSENT),
        pytest.param(FIELD_DEFAULT_COMBO, id=ID_DEFAULT_COMBO_ABSENT),
        pytest.param(FIELD_CURR_COMBO, id=ID_CURR_COMBO_ABSENT),
        pytest.param(FIELD_SOURCE_MANIFEST_REPO, id=ID_SOURCE_REPO_ABSENT),
    ])
    def test_init_field_defaults_to_none_when_absent(self, empty_config, field_name):
        """When any optional child element is absent, __init__ must set the corresponding field to None."""
        assert getattr(empty_config, field_name) is None

    def test_tuple_returns_correct_general_config_namedtuple(self):
        """The tuple property must return a edk_manifest.GeneralConfig namedtuple with the correct field values."""
        find_map = {
            CHILD_PIN_PATH: helpers.make_text_element(PIN_PATH),
            CHILD_DEFAULT_COMBO: helpers.make_attrib_element({helpers.ATTRIB_COMBINATION: helpers.BRANCH}),
            CHILD_CURR_COMBO: helpers.make_attrib_element({helpers.ATTRIB_COMBINATION: helpers.DEV}),
            CHILD_SOURCE_MANIFEST_REPO: helpers.make_attrib_element({ATTRIB_MANIFEST_REPO: SOURCE_MANIFEST_REPO}),
        }
        result = edk_manifest._GeneralConfig(self._make_mock_element(find_map)).tuple

        assert result == edk_manifest.GeneralConfig(
            default_combo=helpers.BRANCH,
            current_combo=helpers.DEV,
            pin_path=PIN_PATH,
            source_manifest_repo=SOURCE_MANIFEST_REPO,
        )
