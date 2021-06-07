#!/usr/bin/env python3
#
## @file
# ui_functions.py
#
# Copyright (c) 2017- 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import string

import git
import colorama

from edkrepo.common.pathfix import expanduser

def init_color_console(force_color_output):
    config = git.GitConfigParser(os.path.normpath(expanduser("~/.gitconfig")))
    config_color = config.get("color", "ui", fallback="auto")
    strip = not sys.stdout.isatty()
    convert = sys.stdout.isatty()
    if force_color_output or config_color == "always":
        strip = False
    elif config_color == "false":
        strip = True
        convert = False
    if os.name == 'posix':
        # Never convert on Linux.  Setting it to False seems to cause problems.
        convert=None
    colorama.init(strip=strip, convert=convert)
    return strip, convert


def display_git_output(output_data, verbose=False):
    """
    Displays output from GitPython git commands

    output_data - Output from the git.execute method
    verbose     - Enable verbose messages
    """
    if verbose and output_data[0]:
        print(output_data[0])
    if output_data[1]:
        print(output_data[1])
    if verbose and output_data[2]:
        print(output_data[2])

def print_safe(input_string):
    print(safe_str(input_string))

def safe_str(input_string):
    safe_str = ''
    for char in input_string:
        if char not in string.printable:
            char = '?'
        safe_str = ''.join((safe_str, str(char)))
    return safe_str
