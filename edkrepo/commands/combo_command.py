#!/usr/bin/env python3
#
## @file
# combo_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
from colorama import Fore
from colorama import Style

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.combo_args as arguments
import edkrepo.common.ui_functions as ui_functions
from edkrepo.config.config_factory import get_workspace_manifest


class ComboCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'combo'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'archived',
                     'short-name': 'a',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.ARCHIVED_HELP})
        return metadata

    def run_command(self, args, config):
        manifest = get_workspace_manifest()
        combo_archive = []
        combo_list = [c.name for c in manifest.combinations]
        if args.archived:
            combo_archive = [c.name for c in manifest.archived_combinations]
            combo_list.extend(combo_archive)
        if manifest.general_config.current_combo not in combo_list:
            combo_list.append(manifest.general_config.current_combo)
        for combo in sorted(combo_list):
            if combo == manifest.general_config.current_combo:
                print("* {}{}{}".format(Fore.GREEN, combo, Fore.RESET))
            elif combo in combo_archive:
                print("  {}{}{}{}".format(Fore.YELLOW, Style.BRIGHT, combo, Style.RESET_ALL))
            else:
                ui_functions.print_info_msg("  {}".format(combo), header=False)
            if args.verbose:
                sources = manifest.get_repo_sources(combo)
                length = len(max([source.root for source in sources], key=len))
                for source in sources:
                    if source.branch:
                        ui_functions.print_info_msg("    {} : {}".format(source.root.ljust(length), source.branch), header=False)
                    elif source.patch_set:
                        ui_functions.print_info_msg("    {} : {}".format(source.root.ljust(length), source.patch_set), header=False)
