#!/usr/bin/env python3
#
## @file
# cache_args.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the
cache command meta data.
'''
COMMAND_DESCRIPTION = ('Manages local caching support for project repos.  The goal of this feature '
                       'is to improve clone performance')
COMMAND_ENABLE_HELP = 'Enables caching support on the system.'
COMMAND_DISABLE_HELP = 'Disables caching support on the system.'
COMMAND_UPDATE_HELP = 'Update the repo cache for all cached projects.'
COMMAND_INFO_HELP = 'Display the current cache information.'
COMMAND_FORMAT_HELP = 'Change the format that the cache information is displayed in.'
COMMAND_PROJECT_HELP = 'Project or manifest/pin file to add to the cache.'
COMMAND_PATH_HELP = 'Path where cache will be created'
SELECTIVE_HELP = 'Only update the cache with the objects referenced by Project or the current workspace manifest'
