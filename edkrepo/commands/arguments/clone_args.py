#!/usr/bin/env python3
#
## @file
# clone_args.py
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
clone command meta data.
'''

COMMAND_DESCRIPTION = 'Downloads a project and creates a new workspace.'
WORKSPACE_HELP = ('The destination for the newly created workspace, this must be an empty directory.\n'
                  'A value of "." indicates the current working directory.')
PROJECT_MANIFEST_HELP = ('Either a project name as listed by "edkrepo manifest" or the path to a project manifest file.\n'
                         'If a relative path is provided clone will first search relative to the current working directory'
                         ' and then search relative to the global manifest repository.')
COMBINATION_HELP = 'The name of the combination to checkout. If not specified the projects default combination is used.'
SPARSE_HELP = 'Enables sparse checkout if supported by the project manifest file.'
NO_SPARSE_HELP = 'Disables sparse checkout if the project manifest file enables it by default.'