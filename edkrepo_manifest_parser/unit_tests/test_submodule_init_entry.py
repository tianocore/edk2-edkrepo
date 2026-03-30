#!/usr/bin/env python3
#
## @file
# test_submodule_init_entry.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_mock_element_with_text,
    REMOTE_NAME,
    REQUIRED_ATTRIB_SPLIT_CHAR,
)
from edkrepo_manifest_parser.edk_manifest import (
    _SubmoduleInitEntry,
    _parse_submodule_init_required_attribs,
    SubmoduleInitPath,
    REQUIRED_ATTRIB_ERROR_MSG,
)

ATTRIB_REMOTE               = 'remote'
ATTRIB_COMBO                = 'combo'
ATTRIB_RECURSIVE            = 'recursive'
ATTRIB_BOOL_TRUE            = 'true'
ATTRIB_BOOL_FALSE           = 'false'
ELEMENT_TAG_SUBMODULE_INIT  = 'SubmoduleInitEntry'
SUBMODULE_PATH_VALUE        = 'some/submodule/path'
SUBMODULE_COMBO             = 'combo_a'
FIELD_REMOTE_NAME           = 'remote_name'
FIELD_PATH                  = 'path'
PARAM_RECURSIVE_FLAG        = 'attrib_val, expected'
ID_RECURSIVE_TRUE           = 'recursive_true'
ID_RECURSIVE_FALSE          = 'recursive_false'


class TestSubmoduleInitEntry:

    @staticmethod
    def _make_required_element(**extra):
        """Build a mock element with the required remote attrib and SUBMODULE_PATH_VALUE text, plus any extra attribs."""
        attrib = {ATTRIB_REMOTE: REMOTE_NAME}
        attrib.update(extra)
        return make_mock_element_with_text(attrib, text=SUBMODULE_PATH_VALUE, tag=ELEMENT_TAG_SUBMODULE_INIT)

    @pytest.fixture
    def full_sie(self):
        """Return a _SubmoduleInitEntry built from an element with required fields only and no optional fields."""
        return _SubmoduleInitEntry(self._make_required_element())

    def test_parse_returns_all_fields_when_all_present(self):
        """When the required remote attribute is present, must return (remote_name, path) with the correct values."""
        element = self._make_required_element()

        remote_name, path = _parse_submodule_init_required_attribs(element)

        assert remote_name == REMOTE_NAME
        assert path == SUBMODULE_PATH_VALUE

    def test_parse_raises_when_remote_missing(self):
        """When the remote attribute is absent, must raise KeyError with the required-attrib message."""
        element = make_mock_element_with_text({}, text=SUBMODULE_PATH_VALUE, tag=ELEMENT_TAG_SUBMODULE_INIT)

        with pytest.raises(KeyError) as exc_info:
            _parse_submodule_init_required_attribs(element)

        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_all_required_fields(self, full_sie):
        """When all required attributes are present, __init__ must correctly set remote_name and path."""
        assert getattr(full_sie, FIELD_REMOTE_NAME) == REMOTE_NAME
        assert getattr(full_sie, FIELD_PATH) == SUBMODULE_PATH_VALUE

    def test_all_optional_fields_default_when_absent(self, full_sie):
        """When all optional attributes are absent, __init__ must set combo to None and recursive to False."""
        assert full_sie.combo is None
        assert full_sie.recursive is False

    def test_combo_when_present(self):
        """When the combo attribute is present, __init__ must set self.combo to its value."""
        element = self._make_required_element(**{ATTRIB_COMBO: SUBMODULE_COMBO})
        sie = _SubmoduleInitEntry(element)
        assert sie.combo == SUBMODULE_COMBO

    @pytest.mark.parametrize(PARAM_RECURSIVE_FLAG, [
        pytest.param(ATTRIB_BOOL_TRUE,  True,  id=ID_RECURSIVE_TRUE),
        pytest.param(ATTRIB_BOOL_FALSE, False, id=ID_RECURSIVE_FALSE),
    ])
    def test_init_sets_recursive_flag(self, attrib_val, expected):
        """When recursive is 'true' or 'false', __init__ must set self.recursive to the expected boolean."""
        element = self._make_required_element(**{ATTRIB_RECURSIVE: attrib_val})
        sie = _SubmoduleInitEntry(element)
        assert sie.recursive is expected

    def test_tuple_returns_correct_submodule_init_path_namedtuple(self, full_sie):
        """The tuple property must return a SubmoduleInitPath namedtuple with all field values correct."""
        assert full_sie.tuple == SubmoduleInitPath(
            remote_name=REMOTE_NAME,
            combo=None,
            recursive=False,
            path=SUBMODULE_PATH_VALUE,
        )

