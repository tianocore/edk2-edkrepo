#!/usr/bin/env python3
#
## @file
# test_project_info.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo_manifest_parser.edk_manifest import ProjectInfo
from edkrepo_manifest_parser.edk_manifest import _parse_project_info_required_fields
from edkrepo_manifest_parser.edk_manifest import _ProjectInfo
from edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers import (
    make_text_element,
)

ELEMENT_TAG_PROJECT_INFO = 'ProjectInfo'
CHILD_CODE_NAME          = 'CodeName'
CHILD_DESCRIPT           = 'Description'
CHILD_ORG                = 'Org'
CHILD_SHORT_NAME         = 'ShortName'
CHILD_LEAD_REVIEWERS     = 'LeadReviewers'
TEST_PROJECT_NAME        = 'TestProject'
DESCRIPT                 = 'A test project.'
LEAD                     = 'lead@example.com'
ORG                      = 'Intel'
SHORT_NAME               = 'TP'
REVIEWER                 = 'reviewer@example.com'
PARAM_REQUIRED_ABSENT    = 'missing_child'
ID_CODE_NAME_ABSENT      = 'code_name_absent'
ID_DESCRIPT_ABSENT       = 'descript_absent'
ATTR_ORG                 = 'org'
ATTR_SHORT_NAME          = 'short_name'
PARAM_OPTIONAL_PRESENT   = 'child_key, value, attr'
PARAM_OPTIONAL_ABSENT    = 'attr'
ID_ORG_PRESENT           = 'org_present'
ID_SHORT_NAME_PRESENT    = 'short_name_present'
ID_ORG_ABSENT            = 'org_absent'
ID_SHORT_NAME_ABSENT     = 'short_name_absent'


class TestProjectInfo:

    @staticmethod
    def _make_mock_element(find_map=None, dev_leads=None):
        """Build a mock XML element using find_map for find() calls and dev_leads for findall('DevLead')."""
        elem = MagicMock()
        elem.tag = ELEMENT_TAG_PROJECT_INFO
        fm = find_map if find_map is not None else {}
        elem.find.side_effect = lambda tag: fm.get(tag)
        elem.findall.return_value = dev_leads if dev_leads is not None else []
        return elem

    @staticmethod
    def _make_required_element():
        """Build a mock element with only the required CodeName and Description children."""
        find_map = {
            CHILD_CODE_NAME: make_text_element(TEST_PROJECT_NAME),
            CHILD_DESCRIPT: make_text_element(DESCRIPT),
        }
        return TestProjectInfo._make_mock_element(find_map=find_map)

    @pytest.fixture
    def required_info(self):
        """Build and return a _ProjectInfo instance with only the required CodeName and Description children."""
        return _ProjectInfo(self._make_required_element())

    def test_parse_required_fields_returns_codename_and_descript_when_both_present(self):
        """When CodeName and Description children are present, must return (codename, descript)."""
        element = self._make_required_element()

        codename, descript = _parse_project_info_required_fields(element)

        assert codename == TEST_PROJECT_NAME
        assert descript == DESCRIPT

    @pytest.mark.parametrize(PARAM_REQUIRED_ABSENT, [
        pytest.param(CHILD_CODE_NAME, id=ID_CODE_NAME_ABSENT),
        pytest.param(CHILD_DESCRIPT,  id=ID_DESCRIPT_ABSENT),
    ])
    def test_parse_required_fields_raises_when_required_child_absent(self, missing_child):
        """When a required child element is absent, must raise AttributeError."""
        find_map = {
            CHILD_CODE_NAME: make_text_element(TEST_PROJECT_NAME),
            CHILD_DESCRIPT:  make_text_element(DESCRIPT),
        }
        del find_map[missing_child]
        element = self._make_mock_element(find_map=find_map)

        with pytest.raises(AttributeError):
            _parse_project_info_required_fields(element)

    def test_init_sets_codename_and_descript(self, required_info):
        """When required children are present, __init__ must set codename and descript correctly."""
        assert required_info.codename == TEST_PROJECT_NAME
        assert required_info.descript == DESCRIPT

    def test_init_builds_lead_list_from_dev_lead_children(self):
        """When DevLead child elements are present, __init__ must populate lead_list with their text values."""
        lead_mock = make_text_element(LEAD)
        element = self._make_mock_element(
            find_map={
                CHILD_CODE_NAME: make_text_element(TEST_PROJECT_NAME),
                CHILD_DESCRIPT: make_text_element(DESCRIPT),
            },
            dev_leads=[lead_mock],
        )

        info = _ProjectInfo(element)

        assert info.lead_list == [LEAD]

    def test_init_sets_lead_list_to_empty_when_no_dev_lead_children(self, required_info):
        """When no DevLead children exist, __init__ must set lead_list to an empty list."""
        assert required_info.lead_list == []

    @pytest.mark.parametrize(PARAM_OPTIONAL_PRESENT, [
        pytest.param(CHILD_ORG,        ORG,        ATTR_ORG,        id=ID_ORG_PRESENT),
        pytest.param(CHILD_SHORT_NAME, SHORT_NAME, ATTR_SHORT_NAME, id=ID_SHORT_NAME_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, child_key, value, attr):
        """When an optional child element is present, __init__ must set the field to its text value."""
        element = self._make_mock_element(find_map={
            CHILD_CODE_NAME: make_text_element(TEST_PROJECT_NAME),
            CHILD_DESCRIPT: make_text_element(DESCRIPT),
            child_key: make_text_element(value),
        })

        info = _ProjectInfo(element)

        assert getattr(info, attr) == value

    @pytest.mark.parametrize(PARAM_OPTIONAL_ABSENT, [
        pytest.param(ATTR_ORG,        id=ID_ORG_ABSENT),
        pytest.param(ATTR_SHORT_NAME, id=ID_SHORT_NAME_ABSENT),
    ])
    def test_init_sets_optional_field_to_none_when_absent(self, required_info, attr):
        """When an optional child element is absent, __init__ must set the field to None."""
        assert getattr(required_info, attr) is None

    def test_init_sets_reviewer_list_from_lead_reviewers(self):
        """When LeadReviewers with Reviewer children is present, __init__ must populate reviewer_list."""
        reviewer_mock = make_text_element(REVIEWER)
        lead_reviewers_mock = MagicMock()
        lead_reviewers_mock.iter.return_value = [reviewer_mock]
        element = self._make_mock_element(find_map={
            CHILD_CODE_NAME: make_text_element(TEST_PROJECT_NAME),
            CHILD_DESCRIPT: make_text_element(DESCRIPT),
            CHILD_LEAD_REVIEWERS: lead_reviewers_mock,
        })

        info = _ProjectInfo(element)

        assert info.reviewer_list == [REVIEWER]

    def test_init_sets_reviewer_list_to_none_when_lead_reviewers_absent(self, required_info):
        """When no LeadReviewers child element exists, __init__ must set reviewer_list to None."""
        assert required_info.reviewer_list is None

    def test_tuple_returns_correct_project_info_namedtuple(self):
        """The tuple property must return a ProjectInfo namedtuple with the correct field values."""
        lead_mock = make_text_element(LEAD)
        reviewer_mock = make_text_element(REVIEWER)
        lead_reviewers_mock = MagicMock()
        lead_reviewers_mock.iter.return_value = [reviewer_mock]
        find_map = {
            CHILD_CODE_NAME: make_text_element(TEST_PROJECT_NAME),
            CHILD_DESCRIPT: make_text_element(DESCRIPT),
            CHILD_ORG: make_text_element(ORG),
            CHILD_SHORT_NAME: make_text_element(SHORT_NAME),
            CHILD_LEAD_REVIEWERS: lead_reviewers_mock,
        }
        result = _ProjectInfo(self._make_mock_element(find_map=find_map, dev_leads=[lead_mock])).tuple

        assert result == ProjectInfo(
            codename=TEST_PROJECT_NAME,
            description=DESCRIPT,
            dev_leads=[LEAD],
            reviewers=[REVIEWER],
            org=ORG,
            short_name=SHORT_NAME,
        )

