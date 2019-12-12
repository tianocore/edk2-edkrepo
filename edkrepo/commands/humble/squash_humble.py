#!/usr/bin/env python3
#
## @file
# squash_humble.py
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the squash command.
'''

#from colorama import Fore @todo
#from colorama import Style

BRANCH_EXISTS = 'A branch with the name {} already exists, a non-existant branch must be provided'
MULTIPLE_COMMITS_REQUIRED = 'A range of commits is required, only a single commit was given'
COMMIT_MESSAGE = 'Squash of the following commits:\n\n'
