#!/usr/bin/env python3
#
## @file
# progress_handler.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from git import RemoteProgress
from edkrepo.common.logger import get_logger
logger = get_logger()
class GitProgressHandler(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.__max_line_len = 0

    def update(self, *args):
        self.__max_line_len = max(self.__max_line_len, len(self._cur_line))
        logger.info(self._cur_line.ljust(self.__max_line_len), end="\r")
