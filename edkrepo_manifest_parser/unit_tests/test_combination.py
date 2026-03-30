#!/usr/bin/env python3
#
## @file
# test_combination.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element,
    ATTRIB_NAME,
    ATTRIB_BOOL_TRUE,
    ATTRIB_BOOL_FALSE,
    REQUIRED_ATTRIB_SPLIT_CHAR,
    ELEMENT_TAG_COMBINATION,
    COMBO_NAME,
    COMBO_DESCRIPTION,
    ATTRIB_DESCRIPTION,
    ATTRIB_ARCHIVED,
    ATTRIB_VENV_ENABLE,
    ARCHIVED_TRUE_UPPER,
    COMBINATION_BOOL_FLAG_FIELDS,
    COMBINATION_REQUIRED_FIELD_FIELDS,
    ID_ARCHIVED_TRUE_LOWER,
    ID_ARCHIVED_FALSE_LOWER,
    ID_ARCHIVED_MISSING,
    ID_ARCHIVED_TRUE_UPPER,
    ID_VENV_TRUE,
    ID_VENV_FALSE,
    ID_VENV_MISSING,
)
from edkrepo_manifest_parser.edk_manifest import (
    _Combination,
    _parse_combination_required_attribs,
    Combination,
    REQUIRED_ATTRIB_ERROR_MSG,
)

BOOL_FLAG_IDS = [
    ID_ARCHIVED_TRUE_LOWER, ID_ARCHIVED_FALSE_LOWER, ID_ARCHIVED_MISSING, ID_ARCHIVED_TRUE_UPPER,
    ID_VENV_TRUE, ID_VENV_FALSE, ID_VENV_MISSING,
]
REQUIRED_FIELD_IDS = [ATTRIB_NAME, ATTRIB_DESCRIPTION]


class TestCombination:

    @staticmethod
    def _make_required_element():
        """Build a mock element with only the required name attribute."""
        return make_mock_element({ATTRIB_NAME: COMBO_NAME}, tag=ELEMENT_TAG_COMBINATION)

    def test_parse_required_attribs_returns_name_when_present(self):
        """When name is present, _parse_combination_required_attribs must return the name string."""
        element = self._make_required_element()

        name = _parse_combination_required_attribs(element)

        assert name == COMBO_NAME

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent, _parse_combination_required_attribs must raise KeyError with the required-attrib message."""
        element = make_mock_element({}, tag=ELEMENT_TAG_COMBINATION)

        with pytest.raises(KeyError) as exc_info:
            _parse_combination_required_attribs(element)

        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    @pytest.mark.parametrize(COMBINATION_REQUIRED_FIELD_FIELDS, [
        (ATTRIB_NAME,        COMBO_NAME),
        (ATTRIB_DESCRIPTION, None),
    ], ids=REQUIRED_FIELD_IDS)
    def test_init_required_combo_field(self, field_name, expected):
        """Each required-combo field must have the expected value after __init__."""
        combo = _Combination(self._make_required_element())
        assert getattr(combo, field_name) == expected

    def test_init_sets_description_when_present(self):
        """When the description attribute is present, __init__ must set self.description to its value."""
        element = make_mock_element({
            ATTRIB_NAME: COMBO_NAME,
            ATTRIB_DESCRIPTION: COMBO_DESCRIPTION,
        }, tag=ELEMENT_TAG_COMBINATION)

        combo = _Combination(element)

        assert combo.description == COMBO_DESCRIPTION

    @pytest.mark.parametrize(COMBINATION_BOOL_FLAG_FIELDS, [
        (ATTRIB_ARCHIVED,    ATTRIB_BOOL_TRUE,     ATTRIB_ARCHIVED,    True),
        (ATTRIB_ARCHIVED,    ATTRIB_BOOL_FALSE,    ATTRIB_ARCHIVED,    False),
        (ATTRIB_ARCHIVED,    None,                 ATTRIB_ARCHIVED,    False),
        (ATTRIB_ARCHIVED,    ARCHIVED_TRUE_UPPER,  ATTRIB_ARCHIVED,    True),
        (ATTRIB_VENV_ENABLE, ATTRIB_BOOL_TRUE,     ATTRIB_VENV_ENABLE, True),
        (ATTRIB_VENV_ENABLE, ATTRIB_BOOL_FALSE,    ATTRIB_VENV_ENABLE, False),
        (ATTRIB_VENV_ENABLE, None,                 ATTRIB_VENV_ENABLE, False),
    ], ids=BOOL_FLAG_IDS)
    def test_init_bool_flag(self, attrib_name, attrib_value, field_name, expected):
        """Each combination of attrib_name/attrib_value must produce the expected boolean on the named field."""
        attrib = {ATTRIB_NAME: COMBO_NAME}
        if attrib_value is not None:
            attrib[attrib_name] = attrib_value
        element = make_mock_element(attrib, tag=ELEMENT_TAG_COMBINATION)
        combo = _Combination(element)
        assert getattr(combo, field_name) is expected

    def test_tuple_returns_correct_combination_namedtuple(self):
        """The tuple property must return a Combination namedtuple with name, description, and venv_enable."""
        element = make_mock_element({
            ATTRIB_NAME: COMBO_NAME,
            ATTRIB_DESCRIPTION: COMBO_DESCRIPTION,
            ATTRIB_VENV_ENABLE: ATTRIB_BOOL_TRUE,
        }, tag=ELEMENT_TAG_COMBINATION)
        combo = _Combination(element)

        result = combo.tuple

        assert result == Combination(
            name=COMBO_NAME,
            description=COMBO_DESCRIPTION,
            venv_enable=True,
        )
