#!/usr/bin/env python3
#
## @file
# create_pin_command.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains the help and description strings for arguments in the create pin
command meta data.
'''

COMMAND_DESCRIPTION = 'Creates a PIN file based on the current workspace state'
NAME_HELP = ('The name of the PIN file. Extension must be .xml. File paths are '
             'supported only if the --push option is not used.')
DESCRIPTION_HELP = 'A short summary of the PIN file contents. Must be contained in ""'
PUSH_HELP = ('Automatically commit and push the PIN file to the global manifest '
             'repository at the location specified by the Pin-Path field in '
             'the project manifest file.')

