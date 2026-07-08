#!/usr/bin/env python3
#
## @file
# reference_repos_args.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
reference_repos command meta data.
'''

COMMAND_DESCRIPTION = 'Lists, adds, removes, or configures reference repositories in the edkrepo_user.cfg file.'
LIST_HELP = 'List all configured reference repositories and their current settings.'
ADD_HELP = 'Add a new reference repository entry.'
REMOVE_HELP = 'Remove an existing reference repository entry.'
ENABLE_HELP = 'Enable the use of reference repositories by default.'
DISABLE_HELP = 'Disable the use of reference repositories by default.'
ENABLE_DISSOCIATE_HELP = ('Enable dissociate mode by default. Configured reference repositories will be used only for '
                          'cloning, resulting in a fully independent clone.')
DISABLE_DISSOCIATE_HELP = ('Disable dissociate mode by default. Sets up a shared clone. WARNING: potentially dangerous. '
                           'See https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---shared')
ACTION_HELP = ('Which action to take: "list", "add", "remove", "enable", "disable", '
               '"enable-dissociate", "disable-dissociate"')
NAME_HELP = 'The name of the reference repository entry. Required with "add" and "remove".'
URL_HELP = 'The remote URL of the source repository this reference mirrors. Required with "add".'
PATH_HELP = 'The local filesystem path to the reference repository mirror. Required with "add".'
