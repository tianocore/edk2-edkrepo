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
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

ATTRIB_DESTINATION = 'destination'
ATTRIB_DEST_FILE = 'destination_file'
ELEMENT_TAG_CLIENT_GIT_HOOK = 'ClientGitHook'
HOOK_SOURCE = '/scripts/pre-commit.sh'
DEST_PATH = '.git/hooks'
DEST_FILE = 'pre-commit'
FIELD_REMOTE_URL = 'remote_url'
FIELD_DEST_FILE = 'dest_file'
ID_SOURCE_ABSENT = 'source_absent'
ID_DESTINATION_ABSENT = 'destination_absent'
ID_REMOTE_URL_FOUND = 'remote_url_found'
ID_DEST_FILE_PRESENT = 'dest_file_present'


class TestRepoHook:

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry using the class-level constants."""
        return helpers.make_mock_remotes()

    @pytest.fixture
    def full_hook(self, default_remotes):
        """Return a edk_manifest._RepoHook built from a full-attribute element and the default remotes."""
        element = helpers.make_mock_element({
            helpers.ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
            ATTRIB_DEST_FILE: DEST_FILE,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)
        return edk_manifest._RepoHook(element, default_remotes)

    def test_parse_required_attribs_returns_source_and_dest_when_both_present(self):
        """When source and destination are present, must return (source, dest_path) without raising."""
        element = helpers.make_mock_element({
            helpers.ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        source, dest_path = edk_manifest._parse_repo_hook_required_attribs(element)

        assert source == HOOK_SOURCE
        assert dest_path == DEST_PATH

    @pytest.mark.parametrize(helpers.PARAM_MISSING_ATTRIB, [
        pytest.param(helpers.ATTRIB_SOURCE, id=ID_SOURCE_ABSENT),
        pytest.param(ATTRIB_DESTINATION, id=ID_DESTINATION_ABSENT),
    ])
    def test_parse_required_attribs_raises_key_error_when_missing(self, missing_attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        full = {
            helpers.ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }
        del full[missing_attrib]
        element = helpers.make_mock_element(full, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)
        with pytest.raises(KeyError) as exc_info:
            edk_manifest._parse_repo_hook_required_attribs(element)
        assert edk_manifest.REQUIRED_ATTRIB_ERROR_MSG.split(helpers.REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_source_and_dest_path(self, full_hook):
        """When all required attributes are present, __init__ must set self.source and self.dest_path correctly."""
        assert full_hook.source == HOOK_SOURCE
        assert full_hook.dest_path == DEST_PATH

    @pytest.mark.parametrize(helpers.PARAM_FIELD_AND_EXPECTED, [
        pytest.param(FIELD_REMOTE_URL, helpers.REMOTE_URL, id=ID_REMOTE_URL_FOUND),
        pytest.param(FIELD_DEST_FILE, DEST_FILE, id=ID_DEST_FILE_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, full_hook, field_name, expected_value):
        """When the optional attribute is present and resolved, __init__ must set the corresponding field to its value."""
        assert getattr(full_hook, field_name) == expected_value

    def test_init_sets_remote_url_to_none_when_remote_absent(self):
        """When the remote attribute is absent from the element, __init__ must set self.remote_url to None."""
        element = helpers.make_mock_element({
            helpers.ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        hook = edk_manifest._RepoHook(element, {})

        assert hook.remote_url is None

    def test_init_sets_dest_file_to_none_when_absent(self, default_remotes):
        """When the destination_file attribute is absent, __init__ must set self.dest_file to None."""
        element = helpers.make_mock_element({
            helpers.ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
            helpers.ATTRIB_REMOTE: helpers.REMOTE_NAME,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        hook = edk_manifest._RepoHook(element, default_remotes)

        assert hook.dest_file is None

    def test_tuple_returns_correct_repo_hook_namedtuple(self, full_hook):
        """The tuple property must return a edk_manifest.RepoHook namedtuple with the correct field values."""
        assert full_hook.tuple == edk_manifest.RepoHook(
            source=HOOK_SOURCE,
            dest_path=DEST_PATH,
            dest_file=DEST_FILE,
            remote_url=helpers.REMOTE_URL,
        )
