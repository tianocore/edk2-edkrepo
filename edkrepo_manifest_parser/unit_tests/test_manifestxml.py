#!/usr/bin/env python3
#
## @file
# test_manifestxml.py
#
# Copyright (c) 2025 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo_manifest_parser.unit_test_bases import base_tests as bt


class TestManifestXml(bt.BaseTestManifestXml):

    manifest_module = 'edkrepo_manifest_parser.edk_manifest'

    def test_get_remotes_dict_returns_name_to_url_mapping(self, manifest_instance):
        """Must return a dict mapping each remote name to its URL."""
        mock_remote = self._make_mock_remote(name=bt.REMOTE_NAME, url=bt.REMOTE_URL)
        manifest_instance._remotes = {bt.REMOTE_NAME: mock_remote}
        result = manifest_instance.get_remotes_dict()
        assert result == {bt.REMOTE_NAME: bt.REMOTE_URL}
