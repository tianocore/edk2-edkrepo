#!/usr/bin/env python3
#
## @file
# test_sparse_data.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo_manifest_parser.unit_test_bases import base_tests as bt


class TestSparseData(bt.BaseTestSparseData):

    manifest_module = 'edkrepo_manifest_parser.edk_manifest'
