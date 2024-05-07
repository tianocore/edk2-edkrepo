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
import edkrepo.commands.humble.combo_humble as humble
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
        ui_functions.display_current_project(manifest, verbose=args.verbose)
        all_combos = manifest.combinations
        combo_archive = []
        combo_list = [c.name for c in manifest.combinations]
        if args.archived:
            combo_archive = [c.name for c in manifest.archived_combinations]
            combo_list.extend(combo_archive)
            all_combos.extend(manifest.archived_combinations)
        if manifest.general_config.current_combo not in combo_list:
            combo_list.append(manifest.general_config.current_combo)
            all_combos.extend(c for c in manifest.archived_combinations if c.name == manifest.general_config.current_combo)
        for combo in sorted(combo_list):
            if args.verbose:
                description = [c.description for c in all_combos if c.name == combo]
                description = description[0]
                if description is None:
                    description = humble.NO_DESCRIPTION
            if combo == manifest.general_config.current_combo:
                ui_functions.print_info_msg(humble.CURRENT_COMBO.format(combo), header=False)
            elif combo in combo_archive:
                ui_functions.print_info_msg(humble.ARCHIVED_COMBO.format(combo), header=False)
            else:
                ui_functions.print_info_msg(humble.COMBO.format(combo), header=False)
            if args.verbose:
                ui_functions.print_info_msg(humble.COMBO_DESCRIPTION.format(description), header=False)
                sources = manifest.get_repo_sources(combo)
                length = len(max([source.root for source in sources], key=len))
                for source in sources:
                    if source.commit:
                        ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.commit), header=False)
                    elif source.tag and not source.commit:
                        ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.tag), header=False)
                    elif source.branch and not (source.commit or source.tag) :
                        ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.branch), header=False)
                    elif source.patch_set:
                        ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.patch_set), header=False)

