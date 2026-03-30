#!/usr/bin/env python3
#
## @file
# test_submodule_alternate_remote.py
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
    make_mock_remotes,
    REMOTE_NAME,
    REQUIRED_ATTRIB_SPLIT_CHAR,
)
from edkrepo_manifest_parser.edk_manifest import (
    _SubmoduleAlternateRemote,
    _parse_submodule_alternate_remote_attribs,
    SubmoduleAlternateRemote,
    REQUIRED_ATTRIB_ERROR_MSG,
    NO_REMOTE_EXISTS_WITH_NAME,
)

ATTRIB_REMOTE               = 'remote'
ATTRIB_ORIGINAL_URL         = 'originalUrl'
ELEMENT_TAG_SUBMODULE_ALT   = 'SubmoduleAlternateRemote'
ORIGINAL_URL                = 'https://original.example.com/repo.git'
ALT_URL                     = 'https://alt.example.com/repo.git'
FIELD_REMOTE_NAME           = 'remote_name'
FIELD_ORIGINAL_URL          = 'originalUrl'
FIELD_ALT_URL               = 'altUrl'
NO_REMOTE_SPLIT_CHAR        = '{'
PARAM_PARSE_RAISES          = 'attrib'
ID_REMOTE_MISSING           = 'remote_missing'
ID_ORIGINAL_URL_MISSING     = 'original_url_missing'


class TestSubmoduleAlternateRemote:

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry using REMOTE_NAME."""
        return make_mock_remotes(REMOTE_NAME)

    @pytest.fixture
    def full_element(self):
        """Return a mock element with all required attributes set for a SubmoduleAlternateRemote."""
        return make_mock_element_with_text(
            {ATTRIB_REMOTE: REMOTE_NAME, ATTRIB_ORIGINAL_URL: ORIGINAL_URL},
            text=ALT_URL,
            tag=ELEMENT_TAG_SUBMODULE_ALT,
        )

    @pytest.fixture
    def full_sar(self, full_element, default_remotes):
        """Return a _SubmoduleAlternateRemote built from an element with all required attributes set."""
        return _SubmoduleAlternateRemote(full_element, default_remotes)

    def test_parse_returns_all_fields_when_all_present(self, full_element, default_remotes):
        """When all required attributes are present and the remote is in remotes, must return (remote_name, original_url, alt_url)."""
        remote_name, original_url, alt_url = _parse_submodule_alternate_remote_attribs(full_element, default_remotes)

        assert remote_name == REMOTE_NAME
        assert original_url == ORIGINAL_URL
        assert alt_url == ALT_URL

    @pytest.mark.parametrize(PARAM_PARSE_RAISES, [
        pytest.param({ATTRIB_ORIGINAL_URL: ORIGINAL_URL}, id=ID_REMOTE_MISSING),
        pytest.param({ATTRIB_REMOTE: REMOTE_NAME}, id=ID_ORIGINAL_URL_MISSING),
    ])
    def test_parse_raises_when_required_attrib_missing(self, default_remotes, attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        element = make_mock_element_with_text(attrib, tag=ELEMENT_TAG_SUBMODULE_ALT)
        with pytest.raises(KeyError) as exc_info:
            _parse_submodule_alternate_remote_attribs(element, default_remotes)
        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_parse_raises_when_remote_not_in_remotes(self, full_element):
        """When the remote attribute value is not a key in the remotes dict, must raise KeyError with the no-remote message."""
        with pytest.raises(KeyError) as exc_info:
            _parse_submodule_alternate_remote_attribs(full_element, {})

        assert NO_REMOTE_EXISTS_WITH_NAME.split(NO_REMOTE_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_all_fields(self, full_sar):
        """When all required attributes are valid, __init__ must correctly set remote_name, originalUrl, and altUrl."""
        assert getattr(full_sar, FIELD_REMOTE_NAME) == REMOTE_NAME
        assert getattr(full_sar, FIELD_ORIGINAL_URL) == ORIGINAL_URL
        assert getattr(full_sar, FIELD_ALT_URL) == ALT_URL

    def test_tuple_returns_correct_submodule_alternate_remote_namedtuple(self, full_sar):
        """The tuple property must return a SubmoduleAlternateRemote namedtuple with all field values correct."""
        assert full_sar.tuple == SubmoduleAlternateRemote(
            remote_name=REMOTE_NAME,
            original_url=ORIGINAL_URL,
            alternate_url=ALT_URL,
        )

