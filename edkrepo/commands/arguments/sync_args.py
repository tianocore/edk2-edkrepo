#!/usr/bin/env python3
#
## @file
# sync_args.py
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
sync command meta data.
'''

COMMAND_DESCRIPTION = 'Updates the local copy of the current combination\'s target branches by pulling the latest changes from the server. Does not update local branches.'
FETCH_HELP = 'Performs a fetch only sync, no changes will be made to the local workspace.'
UPDATE_LOCAL_MANIFEST_HELP = 'Updates the local copy of the project manifest file prior to performing sync operations.'
OVERRIDE_HELP = 'Ignore warnings and proceed with sync operations.'
TAG_HELP = 'Enables tags to be pulled'
