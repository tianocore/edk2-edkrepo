#!/usr/bin/env python3
#
## @file
# maintenance_command.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.arguments import maintenance_args as arguments
from edkrepo.commands.humble import maintenance_humble as humble
from edkrepo.common.workspace_maintenance.git_config_maintenance import clean_git_globalconfig, set_long_path_support
from edkrepo.common.edkrepo_exception import EdkrepoWorkspaceInvalidException
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest
from edkrepo_manifest_parser.edk_manifest import ManifestXml
import edkrepo.common.ui_functions as ui_functions


class MaintenanceCommande(EdkrepoCommand):

    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'maintenance'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'no-gc',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.NO_GC})
        return metadata

    def run_command(self, args, config):

        # Configure git long path support
        ui_functions.print_info_msg(humble.LONGPATH_CONFIG, header = False)
        set_long_path_support()
        print()

        # Remove unneeded instead of entries from git global config
        ui_functions.print_info_msg(humble.CLEAN_INSTEAD_OFS, header = False)
        clean_git_globalconfig()
        print()

        # If in a valid workspace run the following for each repo:
        # git reflog --expire, git gc, git remote prune origin
        if not args.no_gc:
            try:
                workspace_path = get_workspace_path()
            except EdkrepoWorkspaceInvalidException:
                workspace_path = None
                ui_functions.print_error_msg(humble.NO_WOKKSPACE, header = False)
                print()

            if workspace_path:
                manifest = get_workspace_manifest()
                repos_to_maintain = manifest.get_repo_sources(manifest.general_config.current_combo)
                for repo_to_maintain in repos_to_maintain:
                    local_repo_path = os.path.join(workspace_path, repo_to_maintain.root)
                    repo = Repo(local_repo_path)
                    ui_functions.print_info_msg(humble.REPO_MAINTENANCE.format(repo_to_maintain.root), header = False)
                    ui_functions.print_info_msg(humble.REFLOG_EXPIRE, header = False)
                    repo.git.reflog('expire', '--expire=now', '--all')
                    ui_functions.print_info_msg(humble.GC_AGGRESSIVE, header = False)
                    repo.git.gc('--aggressive', '--prune=now')
                    ui_functions.print_info_msg(humble.REMOTE_PRUNE, header = False)
                    repo.git.remote('prune', 'origin')
                    print()
