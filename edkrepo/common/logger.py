#!/usr/bin/env python3
#
## @file
# logger.py
#
# Copyright (c) 2020-2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import os
import re
import git
import sys
import errno
import string
import logging
from datetime import date

from colorama import init, Fore

from edkrepo.common.humble import LINE_BREAK, DISK_SPACE_ERROR
from edkrepo.common.pathfix import expanduser


# If you find yourself repeatedly sending reset sequences to turn off color changes at the end of
# every print, then init(autoreset=True) will automate that (from https://pypi.org/project/colorama/)
init(autoreset=True)

class CustomFormatter(logging.Formatter):
    def __init__(self):
        self.FORMATS = {
            logging.INFO: Fore.WHITE,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED
        }

    def format(self, record):
        '''
        Overriding the format method of logging.Formatter to check if the message is normal or verbose
        (if none of those, set it to normal by default), whether it requires safe processing or header
        and, colors the ouput message according to the message level (info, warning, error)
        '''
        format_ = "%(message)s\n"
        if not hasattr(record, 'normal') and not hasattr(record, 'verbose'):
            record.normal = True

        if hasattr(record, 'safe') and record.safe:
            safe_str = ''
            for char in record.msg:
                if char not in string.printable:
                    char = '?'
                safe_str = ''.join((safe_str, str(char)))
            record.msg = safe_str if safe_str != '' else record.msg

        if hasattr(record,'header') and record.header:
            format_ = "%(levelname)s: %(message)s\n"

        color = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter("{}{}".format(color, format_))
        return formatter.format(record)

class CustomHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()

    def write(self, stream, msg):
        try:
            stream.write(msg)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                logger.info(DISK_SPACE_ERROR)

    def emit(self, record):
        '''
        Overriding the emit method of the StreamHandler class to decide what to print in console
        based on the presence of 'verbose' or 'normal' attribute and their boolean values.
        '''
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(record, 'verbose') and record.verbose:
                self.write(stream, msg)
            if hasattr(record, 'normal') and record.normal:
                self.write(stream, msg)
        except:
            self.handleError(record)

class FileFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record):
        '''
        Overriding the format method of FileFormatter class to remove the color codes from messages
        and not format the blank lines and line breaks between commands in file
        '''
        if record.msg != "" and record.msg != LINE_BREAK:
            msg = logging.Formatter.format(self, record)
            colorCodeEscape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])') # regex for all 7-bit ANSI C1 escape sequences
            plainMsg = colorCodeEscape.sub('', msg)
            return plainMsg
        return record.msg


def get_logger():
    return logger

def get_formatted_git_output(output_data, verbose=False):
    """
    Displays output from GitPython git commands

    output_data - Output from the git.execute method
    verbose     - Enable verbose messages
    """
    out, verbose_out = "", []
    if verbose and output_data[0]:
        verbose_out.append(output_data[0])
    if output_data[1]:
        out += output_data[1]
    if verbose and output_data[2]:
        verbose_out.append(output_data[2])
    return out, verbose_out

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
    init(strip=strip, convert=convert, autoreset=True)
    return strip, convert

def initiate_file_logs(path):
    '''
    This method takes in the path to store log files, creates a file handler, sets a custom formatting for our
    log files and adds it to the logger object. Because of this, every message gets logged in log files.
    '''
    fileHandler = logging.FileHandler("{}/{}.log".format(path, file_name))
    formatter = FileFormatter("%(asctime)s.%(msecs)03d %(levelname)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)


file_name = date.today().strftime("%Y/%m/%d_logs").split('/')
file_name = '-'.join(file_name)

logger = logging.getLogger('log')
logger.setLevel(logging.INFO)

consoleHandler = CustomHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)
