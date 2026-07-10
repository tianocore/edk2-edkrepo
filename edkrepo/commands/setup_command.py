#!/usr/bin/env python3
#
## @file
# setup_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
NOTE: "edkrepo setup" is handled in edkrepo_entry_point.main() before command
classes are enumerated. This class exists so "setup" appears in "edkrepo
--help", and as a defensive fallback for any invocation that does not go
through the standard edkrepo_entry_point.main().
'''

import sys

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.setup_args as arguments


class SetupCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'setup'
        metadata['help-text'] = arguments.SETUP_COMMAND_DESCRIPTION
        metadata['arguments'] = [
            {'name': 'prompt',
             'positional': False,
             'required': False,
             'help-text': arguments.SETUP_PROMPT_HELP},
            {'name': 'no-prompt',
             'positional': False,
             'required': False,
             'help-text': arguments.SETUP_NO_PROMPT_HELP},
        ]
        return metadata

    def run_command(self, args, config):
        from edkrepo.common import install_functions
        sys.exit(install_functions.handle_setup(sys.argv[2:]))
