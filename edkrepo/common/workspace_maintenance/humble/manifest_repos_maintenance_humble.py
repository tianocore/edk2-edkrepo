#!/usr/bin/env python3
#
## @file
# manifest_repos_maintenance_humble.py
#
# Copyright (c) 2017- 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains user facing strings for manifest_repos_mgmt.py '''

from colorama import Fore
from colorama import Style

CLONE_SINGLE_MAN_REPO = 'Cloning global manifest repository to: {} from: {}'
SYNC_SINGLE_MAN_REPO = 'Syncing the global manifest repository: {}'
SINGLE_MAN_REPO_DIRTY = ('Uncommited changes present in the global manifest '
                         'repository: {} Resolve these changes and attempt your'
                         ' operation again.')
SINGLE_MAN_REPO_NOT_CFG_BRANCH = ('The current active branch, {}, is not the '
                                  'specified branch for global manifst repository: {}')
SINGLE_MAN_REPO_CHECKOUT_CFG_BRANCH = 'Checking out the specified branch: {} prior to syncing'
SINGLE_MAN_REPO_MOVED = '{}{}WARNING:{}{} The global manifest repository has moved. Backing up previous global manifest repository to: {{}}{}\n'.format(Style.BRIGHT, Fore.RED, Style.RESET_ALL, Fore.RED, Style.RESET_ALL)
