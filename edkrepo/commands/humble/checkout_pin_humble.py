#!/usr/bin/env python3
#
## @file
# checkout_pin_humble.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

CHP_EXIT = 'Exiting without checkout out PIN data.'
NOT_FOUND = 'The selected PIN file was not found.'
MANIFEST_MISMATCH = ('The selected PIN file does not refer to the same project '
                     'as the local manifest file. {}'.format(CHP_EXIT))
COMMIT_NOT_FOUND = 'The commit referenced by the PIN file does not exist. {}'.format(CHP_EXIT) 
PIN_COMBO = 'Pin: {}'
COMBO_NOT_FOUND = ('Warning: The combo listed in PIN file: {} is no longer '
                   'listed in the project manifest file.')
