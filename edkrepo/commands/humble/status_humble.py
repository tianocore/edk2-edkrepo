#!/usr/bin/env python3
#
## @file
# status_humble.py
#
# Copyright (c) 2020 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains informational and error messages outputted by
the status command.
'''

from colorama import Fore
from colorama import Style

#Messages for status_command.py
STATUS_CURRENT_COMBO = "{}Current combo: {}{{}}{}".format(Style.BRIGHT, Fore.GREEN, Style.RESET_ALL)
REPO_HEADER = "{}{}{{}}{}:".format(Style.BRIGHT, Fore.CYAN, Style.RESET_ALL)
REPO_HEADER_VERBOSE = "{}{}{{}}{} - [{}{}{{}}{}]:".format(Style.BRIGHT, Fore.CYAN, Style.RESET_ALL, Style.BRIGHT, Fore.RED, Style.RESET_ALL)