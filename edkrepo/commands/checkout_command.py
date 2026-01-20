#!/usr/bin/env python3
#
## @file
# checkout_command.py
#
# Copyright (c) 2017- 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

# Our modules
from edkrepo.commands.edkrepo_command import EdkrepoCommand, OverrideArgument
import edkrepo.commands.arguments.checkout_args as arguments
import edkrepo.commands.humble.checkout_humble as humble
from edkrepo.common.common_cache_functions import get_repo_cache_obj
from edkrepo.common.common_repo_functions import checkout, combination_is_in_manifest
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import get_manifest_repo_path


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
                     'required': False,
                     'description' : arguments.COMBINATION_DESCRIPTION,
                     'help-text' : arguments.COMBINATION_HELP})
        args.append(OverrideArgument)
        return metadata

    def run_command(self, args, config):
        manifest = get_workspace_manifest()
        manifest_repo = manifest.general_config.source_manifest_repo
        global_manifest_path = get_manifest_repo_path(manifest_repo, config)
        if combination_is_in_manifest(args.Combination, manifest):
            checkout(args.Combination, global_manifest_path, args.verbose, args.override, get_repo_cache_obj(config))
        else:
            raise EdkrepoInvalidParametersException(humble.NO_COMBO.format(args.Combination))
