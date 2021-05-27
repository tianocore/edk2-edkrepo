#!/usr/bin/env python3
#
## @file
# clean_args.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
sync command meta data.
'''

#Args for clean_command.py
CLEAN_COMMAND_DESCRIPTION = 'Deletes untracked files from all repositories in the workspace'
FORCE_HELP = 'Without this flag untracked files are listed but not deleted'
QUIET_HELP = 'Don\'t list files as they are deleted'
DIRS_HELP = 'Remove directories in addition to files'