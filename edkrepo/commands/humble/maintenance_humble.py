#!/usr/bin/env python3
#
## @file
# maintenance_humble.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

LONGPATH_CONFIG = 'Configuring git longpaths support'
CLEAN_INSTEAD_OFS = 'Removing unused "InsteadOf" entries from the git global config'
NO_WOKKSPACE = 'Not currently in a valid workspace. No workspace level maintenance tasks will be completed.'
REPO_MAINTENANCE = 'Currently conducting maintenance operations for the {} repository'
GC_AGGRESSIVE = '   Running: git gc --aggressive --prune=now (this may take a significant amount of time)'
REFLOG_EXPIRE = '   Running: git reflog expire --expire=now --all'
REMOTE_PRUNE = '   Running: git remote prune origin'