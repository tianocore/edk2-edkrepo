#!/usr/bin/env python3
#
## @file
# uninstall_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
NOTE: "edkrepo uninstall" is handled in edkrepo_entry_point.main() before
command classes are enumerated. This class exists so "uninstall" appears in
"edkrepo --help", and as a defensive fallback for any invocation that does not
go through the standard edkrepo_entry_point.main().
'''

import sys

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.uninstall_args as arguments


class UninstallCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'uninstall'
        metadata['help-text'] = arguments.UNINSTALL_COMMAND_DESCRIPTION
        args = []
        if sys.platform != 'win32':
            # --yes has no effect on Windows, see install_functions.py for why.
            args.append({'name': 'yes',
                         'short-name': 'y',
                         'positional': False,
                         'required': False,
                         'help-text': arguments.UNINSTALL_YES_HELP})
        args.append({'name': 'system',
                     'short-name': 's',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.UNINSTALL_SYSTEM_HELP})
        metadata['arguments'] = args
        return metadata

    def run_command(self, args, config):
        from edkrepo.common import install_functions
        sys.exit(install_functions.handle_uninstall(sys.argv[2:]))
