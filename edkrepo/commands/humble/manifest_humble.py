#!/usr/bin/env python3
#
## @file
# manifest_humble.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the list-repos command.
'''

from colorama import Fore
from colorama import Style

CURRENT_PROJECT = '{}{}  * {{}}{}'.format(Fore.GREEN, Style.BRIGHT, Fore.RESET)
CURRENT_PROJECT_ARCHIVED = '{}{}  *ARCHIVED: {{}}{}'.format(Fore.GREEN, Style.BRIGHT, Fore.RESET)
MANIFEST_REPO = '{}Manifest Directory:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
MANIFEST_REPO_PATH = '{}Manifest Directory Path:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
MANIFEST_REPO_URL = '{}Manifest Repository URL:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
MANIFEST_REPO_BRANCH = '{}Manifest Repository Branch:{} {{}}'.format(Style.BRIGHT, Style.RESET_ALL)
PROJECTS = '{}Projects:{}'.format(Style.BRIGHT, Style.RESET_ALL)
ARCHIVED_PROJECT = '{}  Archived: {{}}{}'.format(Fore.YELLOW, Fore.RESET)
SINGLE_PROJECT = '  {}'
MANIFEST_FILE_PATH = '    - Manifest File Path: {}'
DEV_LEAD = '    - DevLead(s): {}'
COMBOS = '    - Combos: {}'
DUPLICATE_PROJECTS_DETECTED = '  {}WARNING: Multiple entries for Project {{}} found listed in this manifest repository{}'.format(Fore.RED, Fore.RESET)
BAD_MANIFEST = '    {}ERROR: Unable to parse manifest file{}'.format(Fore.RED, Fore.RESET)