#!/usr/bin/env python3
#
## @file
# combo_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
from colorama import Fore

# Our modules
from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import ColorArgument
from edkrepo.common.argument_strings import COMBO_COMMAND_DESCRIPTION
from edkrepo.common.ui_functions import init_color_console
from edkrepo.config.config_factory import get_workspace_manifest


class ComboCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'combo'
        metadata['help-text'] = COMBO_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append(ColorArgument)
        return metadata

    def run_command(self, args, config):
        init_color_console(args.color)

        manifest = get_workspace_manifest()
        for combo in [c.name for c in manifest.combinations]:
            if combo == manifest.general_config.current_combo:
                print("* {}{}{}".format(Fore.GREEN, combo, Fore.RESET))
            else:
                print("  {}".format(combo))
            if args.verbose:
                sources = manifest.get_repo_sources(combo)
                length = len(max([source.root for source in sources], key=len))
                for source in sources:
                    print("    {} : {}".format(source.root.ljust(length), source.branch))
