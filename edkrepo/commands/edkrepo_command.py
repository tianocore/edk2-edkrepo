#!/usr/bin/env python3
#
## @file
# edkrepo_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import edkrepo.commands.arguments.edkrepo_cmd_args as arguments


class EdkrepoCommand(object):
    def __init__(self):
        pass
    def get_metadata(self):
        raise NotImplementedError()
    def run_command(self, args, config):
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
