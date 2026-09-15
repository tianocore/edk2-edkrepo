#!/usr/bin/env python3
#
## @file
# edkrepo_command.py
#
# Copyright (c) 2017 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import edkrepo.commands.arguments.edkrepo_cmd_args as arguments


class EdkrepoCommand(object):
    def __init__(self):
        """Initialize the base edkrepo command."""
        pass
    def get_metadata(self):
        """Return the command metadata; subclasses must override this method."""
        raise NotImplementedError()
    def run_command(self, args, config):
        """Execute the command; subclasses must override this method."""
        raise NotImplementedError()


VerboseArgument = {'name': 'verbose',
                   'short-name': 'v',
                   'positional': False,
                   'required': False,
                   'help-text': arguments.VERBOSE_HELP}


DryRunArgument = {'name': 'dry-run',
                  'positional': False,
                  'required': False,
                  'help-text': arguments.DRY_RUN_HELP}

OverrideArgument = {'name': 'override',
                    'short-name': 'o',
                    'positional': False,
                    'required': False,
                    'help-text': arguments.OVERRIDE_HELP}

ColorArgument = {'name' : 'color',
                 'short-name': 'c',
                 'positional' : False,
                 'required' : False,
                 'help-text' : arguments.COLOR_HELP}

SubmoduleSkipArgument = {'name': 'skip-submodule',
                         'short-name' : 's',
                         'positional' : False,
                         'required' : False,
                         'help-text' : arguments.SUBMODULE_SKIP_HELP}

SourceManifestRepoArgument = {'name' : 'source-manifest-repo',
                         'positional': False,
                         'required' : False,
                         'action' : 'store',
                         'help-text' : arguments.SOURCE_MANIFEST_REPO_HELP}

PerformanceArgument = {'name': 'performance',
                       'positional': False,
                       'required': False,
                       'help-text': arguments.PERFORMANCE_HELP}

FormatArgument = {'name': 'format',
                  'positional': False,
                  'required': False,
                  'action': 'store',
                  'nargs': 1,
                  'help-text': arguments.FORMAT_HELP}
