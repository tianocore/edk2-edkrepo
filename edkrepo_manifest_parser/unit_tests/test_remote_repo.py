#!/usr/bin/env python3
#
## @file
# test_remote_repo.py
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
    ATTRIB_NAME,
    REMOTE_NAME,
    REMOTE_URL,
    REQUIRED_ATTRIB_SPLIT_CHAR,
    ELEMENT_TAG_REMOTE_REPO,
    OWNER,
    REVIEW_TYPE,
    PR_STRATEGY,
    ATTRIB_OWNER,
    ATTRIB_REVIEW_TYPE,
    ATTRIB_PR_STRATEGY,
    FIELD_OWNER,
    FIELD_REVIEW_TYPE,
    FIELD_PR_STRATEGY,
)
from edkrepo_manifest_parser.edk_manifest import (
    _RemoteRepo,
    _parse_remote_repo_required_attribs,
    RemoteRepo,
    REQUIRED_ATTRIB_ERROR_MSG,
)

OPTIONAL_NONE_IDS = [FIELD_OWNER, FIELD_REVIEW_TYPE, FIELD_PR_STRATEGY]


class TestRemoteRepo:

    @staticmethod
    def _make_full_element():
        """Build a mock element with all required and optional RemoteRepo attributes."""
        return make_mock_element_with_text(
            attrib={
                ATTRIB_NAME: REMOTE_NAME,
                ATTRIB_OWNER: OWNER,
                ATTRIB_REVIEW_TYPE: REVIEW_TYPE,
                ATTRIB_PR_STRATEGY: PR_STRATEGY,
            },
            text=REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

    @pytest.fixture
    def full_remote_repo(self):
        """Return a _RemoteRepo instance with all optional attributes present."""
        return _RemoteRepo(self._make_full_element())

    def test_parse_required_attribs_returns_name_and_url_when_name_present(self):
        """When name is present, _parse_remote_repo_required_attribs must return (name, url)."""
        element = make_mock_element_with_text(
            attrib={ATTRIB_NAME: REMOTE_NAME},
            text=REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

        name, url = _parse_remote_repo_required_attribs(element)

        assert name == REMOTE_NAME
        assert url == REMOTE_URL

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent, _parse_remote_repo_required_attribs must raise KeyError with the required-attrib message."""
        element = make_mock_element_with_text(attrib={}, text=REMOTE_URL, tag=ELEMENT_TAG_REMOTE_REPO)

        with pytest.raises(KeyError) as exc_info:
            _parse_remote_repo_required_attribs(element)

        assert REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_name_and_url_from_required_attribs(self):
        """When name is present, __init__ must set self.name and self.url correctly."""
        element = make_mock_element_with_text(
            attrib={ATTRIB_NAME: REMOTE_NAME},
            text=REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

        repo = _RemoteRepo(element)

        assert repo.name == REMOTE_NAME
        assert repo.url == REMOTE_URL

    def test_init_sets_owner_when_present(self, full_remote_repo):
        """When the owner attribute is present, __init__ must set OWNER to its value."""
        assert full_remote_repo.owner == OWNER

    def test_init_sets_review_type_when_present(self, full_remote_repo):
        """When the reviewType attribute is present, __init__ must set REVIEW_TYPE to its value."""
        assert full_remote_repo.review_type == REVIEW_TYPE

    def test_init_sets_pr_strategy_when_present(self, full_remote_repo):
        """When the prStrategy attribute is present, __init__ must set PR_STRATEGY to its value."""
        assert full_remote_repo.pr_strategy == PR_STRATEGY

    @pytest.mark.parametrize('field_name', [
        FIELD_OWNER,
        FIELD_REVIEW_TYPE,
        FIELD_PR_STRATEGY,
    ], ids=OPTIONAL_NONE_IDS)
    def test_init_optional_attrib_defaults_to_none_when_absent(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        element = make_mock_element_with_text(
            attrib={ATTRIB_NAME: REMOTE_NAME}, text=REMOTE_URL, tag=ELEMENT_TAG_REMOTE_REPO,
        )
        repo = _RemoteRepo(element)
        assert getattr(repo, field_name) is None

    def test_tuple_returns_correct_remote_repo_namedtuple(self, full_remote_repo):
        """The tuple property must return a RemoteRepo namedtuple with all field values correct."""
        result = full_remote_repo.tuple

        assert result == RemoteRepo(
            name=REMOTE_NAME,
            url=REMOTE_URL,
            owner=OWNER,
            review_type=REVIEW_TYPE,
            pr_strategy=PR_STRATEGY,
        )
