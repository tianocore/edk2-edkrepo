#!/usr/bin/env python3
#
## @file
# update_manifest_repo_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import DryRunArgument
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_all_manifest_repos
import edkrepo.commands.arguments.update_manifest_repo as arguments
import edkrepo.common.ui_functions as ui_functions


class UpdateManifestRepoCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'update-manifest-repo'
        metadata['help-text'] = arguments.UPDATE_MANIFEST_REPO_COMMAND_DESCRIPTION
        metadata['alias'] = 'umr'
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'hard',
                     'positional' : False,
                     'required' : False,
                     'description' : arguments.UPDATE_MANIFEST_REPO_HARD_DESCRIPTION,
                     'help-text' : arguments.UPDATE_MANIFEST_REPO_HARD_HELP})
        return metadata

    def run_command(self, args, config):
        ui_functions.init_color_console(args.color)

        pull_all_manifest_repos(config['cfg_file'], config['user_cfg_file'], reset_hard=args.hard)
