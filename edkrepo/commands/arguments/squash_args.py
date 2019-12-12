#!/usr/bin/env python3
#
## @file
# squash_args.py
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
squash command meta data.
'''

COMMAND_DESCRIPTION = 'Convert multiple commits in to a single commit'
COMMIT_ISH_DESCRIPTION = 'A range of commits.'
COMMIT_ISH_HELP = 'The range of commits to be squashed, specified using the same syntax as git rev-list.'
NEW_BRANCH_DESCRIPTION = 'The name of the branch to be created'
NEW_BRANCH_HELP = 'The single commit that is the result of the squash operation will be placed in to a new branch with this name.'
ONELINE_HELP = 'Compact the commit messsages of the squashed commits down to one line'
