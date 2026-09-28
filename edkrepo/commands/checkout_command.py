#!/usr/bin/env python3
#
## @file
# checkout_command.py
#
# Copyright (c) 2017 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import edkrepo.commands.arguments.checkout_args as arguments
from edkrepo.commands.edkrepo_command import EdkrepoCommand, OverrideArgument
import edkrepo.commands.humble.checkout_humble as humble
from edkrepo.common.common_repo_functions import checkout, combination_is_in_manifest
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import get_manifest_repo_path
from edkrepo.config.config_factory import get_workspace_manifest


class CheckoutCommand(EdkrepoCommand):
    def __init__(self):
        """Initialize the checkout command."""
        super().__init__()

    def get_metadata(self):
        """Return the command metadata: name, help text, and argument definitions."""
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
        """Check out the requested combination from the workspace manifest."""
        manifest = get_workspace_manifest()
        manifest_repo = manifest.general_config.source_manifest_repo
        global_manifest_path = get_manifest_repo_path(manifest_repo, config)
        if combination_is_in_manifest(args.Combination, manifest):
            checkout(args.Combination, global_manifest_path, args.verbose, args.override)
        else:
            raise EdkrepoInvalidParametersException(humble.NO_COMBO.format(args.Combination))
