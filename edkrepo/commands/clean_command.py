#!/usr/bin/env python3
#
## @file
# clean_command.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from git import Repo


from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.clean_args as arguments
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest

class CleanCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'clean'
        metadata['help-text'] = arguments.CLEAN_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'force',
                     'short-name': 'f',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.FORCE_HELP})
        args.append({'name' : 'quiet',
                     'short-name': 'q',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.QUIET_HELP})
        args.append({'name' : 'dirs',
                     'short-name': 'd',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.DIRS_HELP})
        return metadata

    def run_command(self, args, config):
        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()
        manifest_config = manifest.general_config
        repo_sources_to_clean = manifest.get_repo_sources(manifest_config.current_combo)
        for repo_to_clean in repo_sources_to_clean:
            local_repo_path = os.path.join(workspace_path, repo_to_clean.root)
            repo = Repo(local_repo_path)
            result = repo.git.clean(f=args.force,
                                    d=args.dirs,
                                    n=(not args.force),
                                    q=(args.quiet and args.force))
            if result:
                print(result)
