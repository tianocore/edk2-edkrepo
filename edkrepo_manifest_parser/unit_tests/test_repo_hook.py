#!/usr/bin/env python3
#
## @file
# test_repo_hook.py
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
    make_mock_remotes,
    ATTRIB_REMOTE,
    REMOTE_NAME,
    REMOTE_URL,
    REQUIRED_ATTRIB_SPLIT_CHAR,
    ELEMENT_TAG_CLIENT_GIT_HOOK,
    HOOK_SOURCE,
    DEST_PATH,
    DEST_FILE,
    ATTRIB_SOURCE,
    ATTRIB_DESTINATION,
    ATTRIB_DEST_FILE,
    MISSING_ATTRIB_FIELDS,
)
from edkrepo_manifest_parser.edk_manifest import (
    _RepoHook,
    _parse_repo_hook_required_attribs,
    RepoHook,
    REQUIRED_ATTRIB_ERROR_MSG,
)

MISSING_ATTRIB_IDS = [ATTRIB_SOURCE, ATTRIB_DESTINATION]


class TestRepoHook:

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry using the class-level constants."""
        return make_mock_remotes()

    @pytest.fixture
    def full_hook(self, default_remotes):
        """Return a _RepoHook built from a full-attribute element and the default remotes."""
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_DEST_FILE: DEST_FILE,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)
        return _RepoHook(element, default_remotes)

    def test_parse_required_attribs_returns_source_and_dest_when_both_present(self):
        """When source and destination are present, must return (source, dest_path) without raising."""
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        source, dest_path = _parse_repo_hook_required_attribs(element)

        assert source == HOOK_SOURCE
        assert dest_path == DEST_PATH

    @pytest.mark.parametrize(MISSING_ATTRIB_FIELDS, [
        ATTRIB_SOURCE,
        ATTRIB_DESTINATION,
    ], ids=MISSING_ATTRIB_IDS)
    def test_parse_required_attribs_raises_key_error_when_missing(self, missing_attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        full = {
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }
        del full[missing_attrib]
        element = make_mock_element(full, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)
        with pytest.raises(KeyError) as exc_info:
            _parse_repo_hook_required_attribs(element)
        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_source_and_dest_path(self, full_hook):
        """When all required attributes are present, __init__ must set HOOK_SOURCE and DEST_PATH correctly."""
        assert full_hook.source == HOOK_SOURCE
        assert full_hook.dest_path == DEST_PATH

    def test_init_sets_remote_url_when_remote_found(self, full_hook):
        """When the remote attribute matches a key in remotes, __init__ must set self.remote_url to that remote's URL."""
        assert full_hook.remote_url == REMOTE_URL

    def test_init_sets_remote_url_to_none_when_remote_not_found(self):
        """When the remote attribute is absent or its key is not in remotes, __init__ must set self.remote_url to None."""
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        hook = _RepoHook(element, {})

        assert hook.remote_url is None

    def test_init_sets_dest_file_when_present(self, full_hook):
        """When the destination_file attribute is present, __init__ must set DEST_FILE to its value."""
        assert full_hook.dest_file == DEST_FILE

    def test_init_sets_dest_file_to_none_when_absent(self, default_remotes):
        """When the destination_file attribute is absent, __init__ must set DEST_FILE to None."""
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
            ATTRIB_REMOTE: REMOTE_NAME,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        hook = _RepoHook(element, default_remotes)

        assert hook.dest_file is None

    def test_tuple_returns_correct_repo_hook_namedtuple(self, full_hook):
        """The tuple property must return a RepoHook namedtuple with the correct field values."""
        assert full_hook.tuple == RepoHook(
            source=HOOK_SOURCE,
            dest_path=DEST_PATH,
            dest_file=DEST_FILE,
            remote_url=REMOTE_URL,
        )
