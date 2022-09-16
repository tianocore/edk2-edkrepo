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
import time
import shutil
import logging

from datetime import date
from colorama import init, Fore

from edkrepo.common.humble import REMOVE_LOG_FAILED
from edkrepo.common.edkrepo_exception import EdkrepoLogsRemoveException
from edkrepo.config.config_factory import GlobalUserConfig


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

def clear_logs():
    SECONDS_IN_A_DAY = 86400
    if os.path.exists(config.logs_path):
        for folder in os.listdir(config.logs_path):
            folder_path = os.path.join(config.logs_path, folder)
            if os.stat(folder_path).st_mtime < time.time() - config.logs_retention_period * SECONDS_IN_A_DAY:
                try:
                    shutil.rmtree(folder_path)
                except EdkrepoLogsRemoveException as e:
                    logger.info(REMOVE_LOG_FAILED.format(folder_path), extra={'normal': False})


def get_logger():
    return logger

config = GlobalUserConfig()
logFormatter = logging.Formatter("%(message)s\n")
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

folder_name = date.today().strftime("%Y/%m/%d_logs").split('/')
folder_name = '-'.join(folder_name)
path = os.path.join(config.logs_path, folder_name)

os.makedirs(path, exist_ok=True)
fileHandler = logging.FileHandler("{}/log.log".format(path))

formatter = fileFormatter("%(asctime)s.%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

consoleHandler = CustomHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)