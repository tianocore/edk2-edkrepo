#!/usr/bin/env python3
#
## @file
# test_send_review_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo.commands.unit_test_bases import base_tests as bt


class TestSendReviewCommand(bt.BaseTestSendReviewCommand):

    command_module = 'edkrepo.commands.send_review_command'
