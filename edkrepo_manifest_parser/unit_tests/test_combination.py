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
    REQUIRED_ATTRIB_SPLIT_CHAR,
)
from edkrepo_manifest_parser.edk_manifest import (
    _Combination,
    _parse_combination_required_attribs,
    Combination,
    REQUIRED_ATTRIB_ERROR_MSG,
)

ATTRIB_NAME                     = 'name'
ATTRIB_DESCRIPTION               = 'description'
ATTRIB_ARCHIVED                  = 'archived'
ATTRIB_VENV_ENABLE               = 'venv_enable'
ATTRIB_BOOL_TRUE                 = 'true'
ATTRIB_BOOL_FALSE                = 'false'
ARCHIVED_TRUE_UPPER              = 'TRUE'
ELEMENT_TAG_COMBINATION          = 'Combination'
COMBO_NAME                       = 'TestCombo'
COMBO_DESCRIPTION                = 'A test combination'
FIELD_NAME                       = 'name'
FIELD_DESCRIPTION                = 'description'
PARAM_MINIMAL_FIELD              = 'field_name, expected'
PARAM_BOOL_FLAG                  = 'attrib_name, attrib_value, field_name, expected'
ID_NAME_SET                      = 'name_set'
ID_DESCRIPTION_ABSENT            = 'description_absent'
ID_ARCHIVED_TRUE_LOWER           = 'archived_true_lower'
ID_ARCHIVED_FALSE_LOWER          = 'archived_false_lower'
ID_ARCHIVED_MISSING              = 'archived_missing'
ID_ARCHIVED_TRUE_UPPER           = 'archived_true_upper'
ID_VENV_TRUE                     = 'venv_true'
ID_VENV_FALSE                    = 'venv_false'
ID_VENV_MISSING                  = 'venv_missing'


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

    @pytest.mark.parametrize(PARAM_MINIMAL_FIELD, [
        pytest.param(FIELD_NAME,        COMBO_NAME, id=ID_NAME_SET),
        pytest.param(FIELD_DESCRIPTION, None,       id=ID_DESCRIPTION_ABSENT),
    ])
    def test_init_sets_field_on_minimal_element(self, field_name, expected):
        """On an element with only the required name attribute, each field must equal the expected value after __init__."""
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

    @pytest.mark.parametrize(PARAM_BOOL_FLAG, [
        pytest.param(ATTRIB_ARCHIVED,    ATTRIB_BOOL_TRUE,    ATTRIB_ARCHIVED,    True,  id=ID_ARCHIVED_TRUE_LOWER),
        pytest.param(ATTRIB_ARCHIVED,    ATTRIB_BOOL_FALSE,   ATTRIB_ARCHIVED,    False, id=ID_ARCHIVED_FALSE_LOWER),
        pytest.param(ATTRIB_ARCHIVED,    None,                ATTRIB_ARCHIVED,    False, id=ID_ARCHIVED_MISSING),
        pytest.param(ATTRIB_ARCHIVED,    ARCHIVED_TRUE_UPPER, ATTRIB_ARCHIVED,    True,  id=ID_ARCHIVED_TRUE_UPPER),
        pytest.param(ATTRIB_VENV_ENABLE, ATTRIB_BOOL_TRUE,    ATTRIB_VENV_ENABLE, True,  id=ID_VENV_TRUE),
        pytest.param(ATTRIB_VENV_ENABLE, ATTRIB_BOOL_FALSE,   ATTRIB_VENV_ENABLE, False, id=ID_VENV_FALSE),
        pytest.param(ATTRIB_VENV_ENABLE, None,                ATTRIB_VENV_ENABLE, False, id=ID_VENV_MISSING),
    ])
    def test_init_sets_bool_flag(self, attrib_name, attrib_value, field_name, expected):
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
