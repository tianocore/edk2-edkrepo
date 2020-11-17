#!/usr/bin/env python3
#
## @file
# humble.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""
Contains strings used by the project_utils modules.
"""
# Status update messages
SUBMOD_DEINIT = 'Deinitializing submodules'
SUBMOD_DEINIT_FULL = 'Deinitializing all submodules'
SUBMOD_INIT_UPDATE = 'Initializing/Updating submodules'
SUBMOD_INIT_FULL = 'Initializing/Updating all submodules (recursive)'

# Verbose messages
SUBMOD_INIT_PATH = 'Submodule init: {}'
SUBMOD_DEINIT_PATH = 'Submodule deinit: {}'
SUBMOD_SYNC_PATH = 'Submodule sync: {}'
SUBMOD_UPDATE_PATH = 'Submodule update: {}'
SUBMOD_EXCEPTION = '- Exception: {}'

# Caching support strings
CACHE_ADD_REMOTE = '+ Adding remote {} ({})'
CACHE_FETCH_REMOTE = '+ Fetching data for {} ({})'
CACHE_CHECK_ROOT_DIR = '+ Creating cache root directory: {}'
CACHE_FAILED_TO_OPEN = '- Failed to open cache: {}'
CACHE_FAILED_TO_CLOSE = '- Failed to close cache: {}'
CACHE_REPO_EXISTS = '- Repo {} already exists.'
CACHE_ADDING_REPO = '+ Adding cache repo {}'
CACHE_REMOVE_REPO = '- Removing cache repo: {}'
CACHE_REMOTE_EXISTS = '- Remote {} already exists.'
