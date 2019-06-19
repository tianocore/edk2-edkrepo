#!/usr/bin/env python3
#
## @file
# edkrepo_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

# Our modules
from edkrepo.common.argument_strings import VERBOSE_DESCRIPTION, VERBOSE_HELP, DRY_RUN_DESCRIPTION, DRY_RUN_HELP, COLOR_HELP
from edkrepo.common.argument_strings import OVERRIDE_HELP, SUBMODULE_SKIP_HELP


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
                   'description': VERBOSE_DESCRIPTION ,
                   'help-text': VERBOSE_HELP}


DryRunArgument = {'name': 'dry-run',
                  'positional': False,
                  'required': False,
                  'description': DRY_RUN_DESCRIPTION,
                  'help-text': DRY_RUN_HELP}

OverrideArgument = {'name': 'override',
                    'short-name': 'o',
                    'positional': False,
                    'required': False,
                    'help-text': OVERRIDE_HELP}

ColorArgument = {'name' : 'color',
                 'short-name': 'c',
                 'positional' : False,
                 'required' : False,
                 'help-text' : COLOR_HELP}

SubmoduleSkipArgument = {'name': 'skip-submodule',
                         'short-name' : 's',
                         'positional' : False,
                         'required' : False,
                         'help-text' : SUBMODULE_SKIP_HELP}
