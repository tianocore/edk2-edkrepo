#!/usr/bin/env python3
#
## @file
# test_sparse_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo.commands.unit_test_bases import base_tests as bt


class TestSparseCommand(bt.BaseTestSparseCommand):

    command_module = 'edkrepo.commands.sparse_command'
