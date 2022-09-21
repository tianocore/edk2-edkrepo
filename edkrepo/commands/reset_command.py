#! python3
#
# This file contains 'Framework Code' and is licensed as such
# under the terms of your license agreement with Intel or your
# vendor. This file may not be modified, except as allowed by
# additional terms of your license agreement.
#
## @file
# reset_command.py
#
# Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.
# This software and associated documentation (if any) is furnished
# under a license and may only be used or copied in accordance
# with the terms of the license. Except as permitted by such
# license, no part of this software or documentation may be
# reproduced, stored in a retrieval system, or transmitted in any
# form or by any means without the express written consent of
# Intel Corporation.
#

import os

from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.reset_args as arguments
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest
import edkrepo.common.ui_functions as ui_functions
class ResetCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
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
        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()
        manifest_config = manifest.general_config
        repo_sources_to_reset = manifest.get_repo_sources(manifest_config.current_combo)
        for repo_to_reset in repo_sources_to_reset:
            local_repo_path = os.path.join(workspace_path, repo_to_reset.root)
            repo = Repo(local_repo_path)
            ui_functions.print_info_msg("{}Resetting {}".format("Hard " if args.hard else "", repo_to_reset.root), extra={"verbose": args.verbose})
            repo.head.reset(working_tree=args.hard)
