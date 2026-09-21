#!/usr/bin/env python3
#
## @file
# reset_command.py
#
# Copyright (c) 2017 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from git import Repo

import edkrepo.commands.arguments.reset_args as arguments
from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.common.ui_functions as ui_functions
from edkrepo.config.config_factory import get_workspace_manifest, get_workspace_path


class ResetCommand(EdkrepoCommand):
    def __init__(self):
        """Initialize the reset command."""
        super().__init__()

    def get_metadata(self):
        """Return the command metadata: name, help text, and argument definitions."""
        metadata = {}
        metadata['name'] = 'reset'
        metadata['help-text'] = arguments.RESET_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'hard',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.HARD_HELP})
        return metadata

    def run_command(self, args, config):
        """Reset every repo source in the current combo, optionally performing a hard reset."""
        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()
        manifest_config = manifest.general_config
        repo_sources_to_reset = manifest.get_repo_sources(manifest_config.current_combo)
        for repo_to_reset in repo_sources_to_reset:
            local_repo_path = os.path.join(workspace_path, repo_to_reset.root)
            repo = Repo(local_repo_path)
            if args.verbose:
                ui_functions.print_info_msg("{}Resetting {}".format("Hard " if args.hard else "", repo_to_reset.root))
            repo.head.reset(working_tree=args.hard)
