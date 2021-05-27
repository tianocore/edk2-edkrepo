#!/usr/bin/env python3
#
## @file
# update_manifest_repo_command.py
#
# Copyright (c) 2020 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
combo command meta data.
'''

#Args for update_manifest_repo_command.py
UPDATE_MANIFEST_REPO_COMMAND_DESCRIPTION = 'Updates the global manifest repository (advanced users only)'
UPDATE_MANIFEST_REPO_HARD_DESCRIPTION = 'Performs a hard reset on the global manifest repository prior to syncing.'
UPDATE_MANIFEST_REPO_HARD_HELP = 'Without this flag the sync operations on the global manifest repository will not be completed if there are unstaged changes present.'
