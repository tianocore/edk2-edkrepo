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
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers
import edkrepo_manifest_parser.edk_manifest as edk_manifest

ATTRIB_OWNER = 'owner'
ATTRIB_REVIEW_TYPE = 'reviewType'
ATTRIB_PR_STRATEGY = 'prStrategy'
ELEMENT_TAG_REMOTE_REPO = 'edk_manifest.RemoteRepo'
OWNER = 'Jane Doe'
REVIEW_TYPE = 'gerrit'
PR_STRATEGY = 'squash'
FIELD_REVIEW_TYPE = 'review_type'
FIELD_PR_STRATEGY = 'pr_strategy'
ID_OWNER_ABSENT = 'owner_absent'
ID_REVIEW_TYPE_ABSENT = 'review_type_absent'
ID_PR_STRATEGY_ABSENT = 'pr_strategy_absent'
ID_OWNER_PRESENT = 'owner_present'
ID_REVIEW_TYPE_PRESENT = 'review_type_present'
ID_PR_STRATEGY_PRESENT = 'pr_strategy_present'


class TestRemoteRepo:

    @pytest.fixture
    def full_remote_repo(self):
        """Return a edk_manifest._RemoteRepo built from a fully-populated element with all optional attributes set."""
        return edk_manifest._RemoteRepo(helpers.make_mock_element_with_text(
            attrib={
                helpers.ATTRIB_NAME: helpers.REMOTE_NAME,
                ATTRIB_OWNER: OWNER,
                ATTRIB_REVIEW_TYPE: REVIEW_TYPE,
                ATTRIB_PR_STRATEGY: PR_STRATEGY,
            },
            text=helpers.REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        ))

    def test_parse_required_attribs_returns_name_and_url_when_name_present(self):
        """When name is present, edk_manifest._parse_remote_repo_required_attribs must return (name, url)."""
        element = helpers.make_mock_element_with_text(
            attrib={helpers.ATTRIB_NAME: helpers.REMOTE_NAME},
            text=helpers.REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

        name, url = edk_manifest._parse_remote_repo_required_attribs(element)

        assert name == helpers.REMOTE_NAME
        assert url == helpers.REMOTE_URL

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent, edk_manifest._parse_remote_repo_required_attribs must raise KeyError with the required-attrib message."""
        element = helpers.make_mock_element_with_text(attrib={}, text=helpers.REMOTE_URL, tag=ELEMENT_TAG_REMOTE_REPO)

        with pytest.raises(KeyError) as exc_info:
            edk_manifest._parse_remote_repo_required_attribs(element)

        assert edk_manifest.REQUIRED_ATTRIB_ERROR_MSG.split(helpers.REQUIRED_ATTRIB_SPLIT_CHAR)[0] in exc_info.value.args[0]

    def test_init_sets_name_and_url_from_required_attribs(self):
        """When name is present, __init__ must set self.name and self.url correctly."""
        element = helpers.make_mock_element_with_text(
            attrib={helpers.ATTRIB_NAME: helpers.REMOTE_NAME},
            text=helpers.REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

        repo = edk_manifest._RemoteRepo(element)

        assert repo.name == helpers.REMOTE_NAME
        assert repo.url == helpers.REMOTE_URL

    @pytest.mark.parametrize(helpers.PARAM_FIELD_AND_EXPECTED, [
        pytest.param(ATTRIB_OWNER, OWNER, id=ID_OWNER_PRESENT),
        pytest.param(FIELD_REVIEW_TYPE, REVIEW_TYPE, id=ID_REVIEW_TYPE_PRESENT),
        pytest.param(FIELD_PR_STRATEGY, PR_STRATEGY, id=ID_PR_STRATEGY_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, full_remote_repo, field_name, expected_value):
        """When any optional attribute is present, __init__ must set the corresponding field to its value."""
        assert getattr(full_remote_repo, field_name) == expected_value

    @pytest.mark.parametrize(helpers.PARAM_FIELD_NAME, [
        pytest.param(ATTRIB_OWNER, id=ID_OWNER_ABSENT),
        pytest.param(FIELD_REVIEW_TYPE, id=ID_REVIEW_TYPE_ABSENT),
        pytest.param(FIELD_PR_STRATEGY, id=ID_PR_STRATEGY_ABSENT),
    ])
    def test_init_optional_attrib_defaults_to_none_when_absent(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        element = helpers.make_mock_element_with_text(
            attrib={helpers.ATTRIB_NAME: helpers.REMOTE_NAME}, text=helpers.REMOTE_URL, tag=ELEMENT_TAG_REMOTE_REPO,
        )
        repo = edk_manifest._RemoteRepo(element)
        assert getattr(repo, field_name) is None

    def test_tuple_returns_correct_remote_repo_namedtuple(self, full_remote_repo):
        """The tuple property must return a edk_manifest.RemoteRepo namedtuple with all field values correct."""
        result = full_remote_repo.tuple

        assert result == edk_manifest.RemoteRepo(
            name=helpers.REMOTE_NAME,
            url=helpers.REMOTE_URL,
            owner=OWNER,
            review_type=REVIEW_TYPE,
            pr_strategy=PR_STRATEGY,
        )
