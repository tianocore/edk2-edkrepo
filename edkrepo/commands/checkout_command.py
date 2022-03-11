#!/usr/bin/env python3
#
## @file
# checkout_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# Standard modules
import sys
import os

# Third-Party modules

# Our modules
from edkrepo.commands.edkrepo_command import EdkrepoCommand, OverrideArgument
import edkrepo.commands.arguments.checkout_args as arguments
import edkrepo.commands.humble.checkout_humble as humble
from edkrepo.common.common_cache_functions import get_repo_cache_obj
from edkrepo.common.common_repo_functions import checkout, combination_is_in_manifest
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
import edkrepo.common.ui_functions as ui_functions
from edkrepo.config.config_factory import get_workspace_manifest


class CheckoutCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'checkout'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'Combination',
                     'positional' : True,
                     'position' : 0,
                     'required': True,
                     'description' : arguments.COMBINATION_DESCRIPTION,
                     'help-text' : arguments.COMBINATION_HELP})
        args.append(OverrideArgument)
        return metadata

    def run_command(self, args, config):
        if combination_is_in_manifest(args.Combination, get_workspace_manifest()):
            checkout(args.Combination, args.verbose, args.override, get_repo_cache_obj(config))
        else:
            raise EdkrepoInvalidParametersException(humble.NO_COMBO.format(args.Combination))
