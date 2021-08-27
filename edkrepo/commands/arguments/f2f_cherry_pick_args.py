#!/usr/bin/env python3
#
## @file
# f2f_cherry_pick_args.py
#
# Copyright (c) 2020 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
sync command meta data.
'''

#Args for the f2f_cherry_pick_command.py
F2F_CHERRY_PICK_COMMAND_DESCRIPTION = 'Cherry pick changes between different folders.'
F2F_CHERRY_PICK_COMMIT_ISH_DESCRIPTION = 'A commit or a range of commits.'
F2F_CHERRY_PICK_COMMIT_ISH_HELP = 'The commit or range of commits to be cherry picked, specified using the same syntax as git rev-parse/rev-list.'
F2F_CHERRY_PICK_TEMPLATE_HELP = 'The source and destination name seperated by a colon (:). Names are taken from templates pre-defined in the manifest file. Example: CNL:ICL might merge CannonLakeSiliconPkg->IceLakeSiliconPkg + CannonLakePlatSamplePkg->IceLakePlatSamplePkg. This can also be done in reverse (ICL:CNL).'
F2F_CHERRY_PICK_FOLDERS_HELP = 'A list of source and destination folders seperated by a colon (:). Only needed if a pre-defined template is not in the manifest file. Example: CannonLakeSiliconPkg:IceLakeSiliconPkg'
F2F_CHERRY_PICK_CONTINUE_HELP = 'Continue processing a Cherry Pick after resolving a merge conflict'
F2F_CHERRY_PICK_ABORT_HELP = 'Abort processing a Cherry Pick after encountering a merge conflict'
F2F_CHERRY_PICK_LIST_TEMPLATES_HELP = 'Print a list of templates defined in the manifest file, and the mappings they define.'
F2F_CHERRY_PICK_APPEND_COMMIT_HELP = 'Append a line that says "(cherry picked from commit ...​)" to the original commit message in order to indicate which commit this change was cherry-picked from.'
F2F_CHERRY_PICK_SQUASH_HELP = 'If given a range of commits, automatically squash them during the Cherry Pick'
