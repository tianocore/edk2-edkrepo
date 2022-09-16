#!/usr/bin/env python3
#
## @file
# ui_functions.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import string

import git
import colorama

from colorama import Fore
from colorama import Style
from colorama import init

from edkrepo.common.logger import get_logger
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
    colorama.init(strip=strip, convert=convert, autoreset=True)
    return strip, convert


def display_git_output(output_data, logger, verbose=False):
    """
    Displays output from GitPython git commands

    output_data - Output from the git.execute method
    verbose     - Enable verbose messages
    """
    if verbose and output_data[0]:
        print_info_msg(output_data[0], logger, extra = {'verbose': verbose})
    if output_data[1]:
        print_info_msg(output_data[1], logger)
    if verbose and output_data[2]:
        print_info_msg(output_data[2], logger, extra = {'verbose': verbose})

def print_info_msg(info_msg, logger=get_logger(), extra={'normal': True}, header=True):
    """
    Displays informational message with (default) or without header.
    """
    if header:
        info_msg_formatted = "Info: {}".format(info_msg)
    else:
        info_msg_formatted = "{}".format(info_msg)
    logger.info(info_msg_formatted, extra=extra)

def print_warning_msg(warning_msg, logger=get_logger(), extra={'normal': True}, header=True):
    """
    Displays warning message with (default) or without header.
    """
    if header:
        warning_msg_formatted = "{}{}Warning: {}{}{}".format(Style.BRIGHT, Fore.YELLOW, Style.RESET_ALL, Fore.YELLOW, warning_msg)
    else:
        warning_msg_formatted = "{}{}".format(Fore.YELLOW, warning_msg)
    logger.warning(warning_msg_formatted, extra=extra)

def print_error_msg(error_msg, logger=get_logger(), extra={'normal': True}, header=True):
    """
    Displays error message with (default) or without header.
    """
    if header:
        error_msg_formatted = "{}{}Error: {}{}{}".format(Style.BRIGHT, Fore.RED, Style.RESET_ALL, Fore.RED, error_msg)
    else:
        error_msg_formatted = "{}{}".format(Fore.RED, error_msg)
    logger.error(error_msg_formatted, extra=extra)

def print_safe(input_string, logger):
    print_info_msg(safe_str(input_string), logger)

def safe_str(input_string):
    safe_str = ''
    for char in input_string:
        if char not in string.printable:
            char = '?'
        safe_str = ''.join((safe_str, str(char)))
    return safe_str
