#!/usr/bin/env python3
#
## @file
# logger.py
#
# Copyright (c) 2018 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import re
import sys
import json
import logging
import subprocess
import pkg_resources

from colorama import init, Fore

from edkrepo.common.edkrepo_version import EdkrepoVersion
from edkrepo.common.humble import PYTHON_VERSION, LFS_VERSION
from edkrepo.common.humble import EDKREPO_VERSION, GIT_VERSION, ENVIRONMENT_VARIABLES, GIT_CONFIG



init(autoreset=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        if color:
            record.asctime = color + record.asctime
            record.msg = color + record
        return logging.Formatter.format(self, record)


class CustomHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(record, 'verbose') and record.verbose:
                stream.write(msg)
            if hasattr(record, 'normal') and record.normal:
                stream.write(msg)
        except:
            self.handleError(record)

class fileFormatter(logging.Formatter):
    def format(self, record):
        if record.msg != "":
            msg = logging.Formatter.format(self, record)
            colorCodeEscape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            plainMsg = colorCodeEscape.sub('', msg)
            return plainMsg
        return ""


def get_logger():
    return logger


logFormatter = logging.Formatter("%(message)s\n")
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)


fileHandler = logging.FileHandler("log.log")

formatter = fileFormatter("%(asctime)s.%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

git_version_output = subprocess.getoutput('git --version')
lfs_version_output = subprocess.getoutput('git-lfs version')
python_version_output = str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro)
edkrepo_version = EdkrepoVersion(pkg_resources.get_distribution('edkrepo').version)
environment_info = json.dumps(dict(os.environ), indent=2)
git_config_values = subprocess.getoutput('git config --list --show-scope --show-origin')

logger.info(GIT_VERSION.format(git_version_output), extra = {'normal': False})
logger.info(LFS_VERSION.format(lfs_version_output), extra = {'normal': False})
logger.info(PYTHON_VERSION.format(python_version_output), extra = {'normal': False})
logger.info(EDKREPO_VERSION.format(edkrepo_version.version_string()), extra = {'normal': False})
logger.info(ENVIRONMENT_VARIABLES.format(environment_info), extra={'normal': False})
logger.info(GIT_CONFIG.format(git_config_values), extra={'normal': False})

consoleHandler = CustomHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
