#!/usr/bin/env python3
#
## @file
# list_repos_humble.py
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the list-repos command.
'''

from colorama import Fore
from colorama import Style

BRANCHES = 'Branches:'
BRANCH_FORMAT_STRING = '  {}{}{{}}{}'.format(Fore.BLUE, Style.BRIGHT, Style.RESET_ALL)
COMBO_FORMAT_STRING = '    {{}}  {}{}({{}}){}'.format(Fore.CYAN, Style.BRIGHT, Style.RESET_ALL)
DEFAULT_COMBO_FORMAT_STRING = '    {{}} {}{}*({{}})*{}'.format(Fore.GREEN, Style.BRIGHT, Style.RESET_ALL)
MANIFEST_DIRECTORY = 'Manifest directory:'
PROJECT_NAME_FORMAT_STRING = '{}{}{{}}{}:'.format(Fore.YELLOW, Style.BRIGHT, Style.RESET_ALL)
REPOSITORIES = 'Repositories:'
REPO_NAME_AND_URL = '{}{}{{}}{} - [ {}{}{{}}{} ]'.format(Fore.MAGENTA, Style.BRIGHT, Style.RESET_ALL, Fore.RED, Style.BRIGHT, Style.RESET_ALL)
REPO_NAME_NOT_FOUND = 'repo_name not found'
REPO_NOT_FOUND_IN_MANIFEST = 'Repo(s) {} not found in any manifest file'
FORMAT_TYPE_INVALID = 'format must be text or json'
