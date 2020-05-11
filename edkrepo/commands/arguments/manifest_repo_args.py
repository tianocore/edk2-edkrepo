#!/usr/bin/env python3
#
## @file
# manifest_repo_args.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
manifest_repo command meta data.
'''

COMMAND_DESCRIPTION = 'Lists, adds or removes a manifest repository.'
LIST_HELP = 'List all available manifest repositories.'
ADD_HELP = 'Add a manifest repository.'
REMOVE_HELP = 'Remove a manifest repository.'
NAME_HELP = 'The name of a manifest repository to add/remove. Required with Add or Remove flags.'
URL_HELP = 'The URL of a manifest repository to add. Required with Add flag.'
LOCAL_PATH_HELP = 'The local path that a manifest is stored at in the edkrepo global data directory. Required with Add flag.'
BRANCH_HELP = 'The branch of a manifest repository to use. Required with Add flag.'
ACTION_HELP = 'Which action "list", "add", "remove" to take'
