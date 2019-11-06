#!/usr/bin/env python3
#
## @file
# argument_strings.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''Contains help and description strings for arguments in command meta data.'''

#Args for edk_command.py
VERBOSE_DESCRIPTION = 'Enable verbose output'
VERBOSE_HELP = 'Increases command verbosity'
DRY_RUN_DESCRIPTION = "Don't actually do anything"
DRY_RUN_HELP = "Don't actually do anything"
OVERRIDE_HELP = 'Ignore warnings'
SUBMODULE_SKIP_HELP = 'Skip the pull or sync of any submodules.'
COLOR_HELP = 'Force color output (useful with \'less -r\')'

#Args for clone_command.py
CLONE_COMMAND_DESCRIPTION = 'Downloads a project and creates a new workspace'
WORKSPACE_DESCRIPTION = 'The workspace in which to clone.'
WORKSPACE_HELP = 'The workspace in which to clone. This must refer to an empty directory. A value of "." indicates the current working directory \n'
PROJECT_OR_MANIFEST_DESCRIPTION = 'The project name as listed in the CiIndex.xml file or the name of the manifest file'
PROJECT_OR_MANIFEST_HELP = ('The project name as listed in the CiIndex.xml file or a path to a manifest file. If a relative path to a manifest file is provided ' +
                            'clone will attempt to find it by first searching relative to the current working directory and then searchting relative to the ' +
                            'global manifest repository \n')
COMBINATION_DESCRIPTION = 'The combination to checkout'
COMBINATION_HELP = 'The combination name to checkout if not specified the default combination is used.\n'
SPARSE_DESCRIPTION = 'Enables sparse checkout support.'
SPARSE_HELP = 'Enables a sparse checkout based on the contents of the DSC file(s) listed by the manifest.\n'
NO_SPARSE_DESCRIPTION = 'Disables sparse checkout support.'
NO_SPARSE_HELP = 'Disables sparse checkout if enabled by default in the manifest.\n'

#Args for sync_command.py
SYNC_COMMAND_DESCRIPTION = 'Updates the local copy of the current combination\'s target branches with the latest changes from the server. Does not update local branches.'
FETCH_DESCRIPTION = 'Downloads the changes from the remote server to the local workspace with out performing a merge'
FETCH_HELP = 'Performs a fetch only sync, no changes will be made to the local workspace'
UPDATE_LOCAL_MANIFEST_DESCRIPTION = 'Updates the global manifest repository and local manifest file prior to performing a sync'
UPDATE_LOCAL_MANIFEST_HELP = 'Updates the local manifest file found in the <workspace>/repo directory prior to performing sync operations.'
SYNC_OVERRIDE_HELP = 'Without this flag sync operations will not be completed if the updated manifest adds/removes repositories or if there are local commits on the target branch.'

