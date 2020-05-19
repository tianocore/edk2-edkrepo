#!/usr/bin/env python3
#
## @file
# submodule.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""
Strings for command line arguments.
"""

SUBMOD_MANIFEST_HELP = 'The current manifest file.'
SUBMOD_COMBO_HELP = 'The current branch combination in use. If a combo is not specified, the current ' \
                    'combo will be used.'
SUBMOD_NEW_MANIFEST_HELP = 'The new manifest file.  Used to test manifest upgrade paths.'
SUBMOD_NEW_COMBO_HELP = 'The new branch combination to use.  Used to test switching combos.'
SUBMOD_DEINIT_HELP = 'Performs submodule deinitialization before initializing submodules.'
SUBMOD_INIT_FULL_HELP = 'Initialize all submodules (recursive).'
SUBMOD_DEINIT_FULL_HELP = 'Deinitialize all submodules.'
SUBMOD_WORKSPACE_HELP = 'The project workspace root.  If not specified the current working directory will ' \
                        'be used.'
SUBMOD_VERBOSE_HELP = 'Enables verbose messaging.'
