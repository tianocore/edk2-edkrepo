#!/usr/bin/env python3
#
## @file
# test_project.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo_manifest_parser.unit_test_bases import base_tests as bt


class TestProject(bt.BaseTestProject):

    manifest_module = 'edkrepo_manifest_parser.edk_manifest'

    @staticmethod
    def _make_full_element(archived=None):
        """Build a mock element with name, xmlPath and an optional archived value."""
        attrib = {
            bt.ATTRIB_NAME: bt.TEST_PROJECT_NAME,
            bt.ATTRIB_XML_PATH: bt.PROJECT_XML_PATH,
        }
        if archived is not None:
            attrib[bt.ATTRIB_ARCHIVED] = archived
        return bt.make_mock_element(attrib, tag=bt.ELEMENT_TAG_PROJECT)
