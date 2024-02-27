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
TREELESS_HELP = ('Creates a partial "treeless" clone; all reachable commits will be downloaded with additional blobs and trees being '
                 'downloaded on demand by future Git operations as needed.\n'
                 'Treeless clones result in significantly faster initial clone times and minimize the amount of content downloaded.\n'
                 'Workspaces created with this option are best used for one time workspaces that will be discarded.')
BLOBLESS_HELP = ('Creates a partial "blobless" clone; all reachable commits and trees will be downloaded with additional blobs being '
                 'downloaded on demand by future Git operations as needed.\n'
                 'Blobless clones result in significantly faster initial clone times and minimize the amount of content downloaded.\n'
                 'Workspaces created with this option are best used for persistent development environments')