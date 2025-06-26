#!/usr/bin/env python3
#
## @file
# common_humble.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the list-repos command.
'''

from colorama import Fore
from colorama import Style


MANIFEST_REPO = '{}Manifest Directory:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
MANIFEST_REPO_PATH = '{}Manifest Directory Path:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
MANIFEST_REPO_URL = '{}Manifest Repository URL:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
MANIFEST_REPO_BRANCH = '{}Manifest Repository Branch:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)