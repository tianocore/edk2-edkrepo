#!/usr/bin/env python3
#
## @file
# ui_functions.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import string

import git

import colorama

def init_color_console(force_color_output):
    config = git.GitConfigParser(os.path.normpath(os.path.expanduser("~/.gitconfig")))
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
