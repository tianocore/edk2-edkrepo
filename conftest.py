#!/usr/bin/env python3
#
## @file
# conftest.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import logging
import os
import sys

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Add EDKREPO_ROOT to sys.path if environment variable is set and path exists."""
    edkrepo_root = os.environ.get('EDKREPO_ROOT')

    if edkrepo_root:
        abs_path = os.path.abspath(edkrepo_root)
        if os.path.exists(abs_path):
            if abs_path not in sys.path:
                sys.path.insert(0, abs_path)
                logger.debug("Using EDKREPO_ROOT: {}".format(abs_path))
        else:
            logger.warning("EDKREPO_ROOT is set but path does not exist: {}".format(abs_path))
    else:
        logger.debug("EDKREPO_ROOT not set, relying on pytest's inherent path manipulation")
