#!/usr/bin/env python3
#
## @file
# combo_humble.py
#
# Copyright (c) 2023, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the list-repos command.
'''

from colorama import Fore
from colorama import Style

CURRENT_COMBO = "{}{}* {{}}{}".format(Fore.GREEN, Style.BRIGHT, Fore.RESET)
ARCHIVED_COMBO = "{}{}- {{}}{}".format(Fore.YELLOW, Style.BRIGHT, Style.RESET_ALL)
COMBO = "  {}{{}}{}".format(Style.BRIGHT, Style.RESET_ALL)
COMBO_DESCRIPTION = "    {}Description: {{}}{}".format(Style.BRIGHT, Style.RESET_ALL)
NO_DESCRIPTION = "{}no description included in combo definition{}".format(Fore.RED, Style.RESET_ALL)
PIN_DESCRIPTION = "{}Currently checked out to a Pin file. The current references are listed below.{}".format(Fore.RED, Style.RESET_ALL)
REPO_DETAILS = "    {}{}{{}}{} : {}{}{{}}{}".format(Style.BRIGHT, Fore.CYAN, Style.RESET_ALL, Style.BRIGHT, Fore.BLUE, Style.RESET_ALL)