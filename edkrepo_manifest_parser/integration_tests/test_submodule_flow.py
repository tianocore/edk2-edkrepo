#!/usr/bin/env python3
#
## @file
# test_submodule_flow.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo_manifest_parser.integration_test_bases import base_tests as bt


class TestSubmoduleFlow(bt.BaseTestSubmoduleFlow):

    manifest_module = 'edkrepo_manifest_parser.edk_manifest'
