#!/usr/bin/env python3
#
## @file
# checkout_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# Standard modules
import sys
import os

# Third-Party modules

# Our modules
from edkrepo.commands.edkrepo_command import EdkrepoCommand, OverrideArgument
from edkrepo.common.argument_strings import CHECKOUT_COMMAND_DESCRIPTION
from edkrepo.common.argument_strings import CHECKOUT_COMBINATION_DESCRIPTION
from edkrepo.common.argument_strings import CHECKOUT_COMBINATION_HELP
from edkrepo.common.common_repo_functions import checkout


class CheckoutCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'checkout'
        metadata['help-text'] = CHECKOUT_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'Combination',
                     'positional' : True,
                     'position' : 0,
                     'required': True,
                     'description' : CHECKOUT_COMBINATION_DESCRIPTION,
                     'help-text' : CHECKOUT_COMBINATION_HELP})
        args.append(OverrideArgument)
        return metadata

    def run_command(self, args, config):
        checkout(args.Combination, args.verbose, args.override)
