#!/usr/bin/env python3
#
## @file
# status_command.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from git import Repo
from colorama import Fore
from colorama import Style

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.status_args as arguments
import edkrepo.commands.humble.status_humble as humble
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest
import edkrepo.common.ui_functions as ui_functions

class StatusCommand(EdkrepoCommand):

    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'status'
        metadata['help-text'] = arguments.STATUS_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        return metadata
    def run_command(self, args, config):
        workspace_path = get_workspace_path()
        initial_manifest = get_workspace_manifest()
        ui_functions.display_current_project(initial_manifest, verbose=args.verbose)
        current_combo = initial_manifest.general_config.current_combo
        current_sources = initial_manifest.get_repo_sources(current_combo)
        ui_functions.print_info_msg(humble.STATUS_CURRENT_COMBO.format(initial_manifest.current_combo), header=False)
        print()
        for current_repo in current_sources:
            local_repo_path = os.path.join(workspace_path, current_repo.root)
            repo = Repo(local_repo_path)
            if not args.verbose:
                ui_functions.print_info_msg(humble.REPO_HEADER.format(current_repo.root), header=False)
            else:
                ui_functions.print_info_msg(humble.REPO_HEADER_VERBOSE.format(current_repo.root, current_repo.remote_url), header=False)
            ui_functions.print_info_msg(repo.git.execute(['git', '-c', 'color.ui=always','status']), header=False)
            print()