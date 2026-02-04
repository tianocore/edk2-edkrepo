#!/usr/bin/env python3
#
## @file
# combo_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import os
from colorama import Fore
from colorama import Style
from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.combo_args as arguments
import edkrepo.commands.humble.combo_humble as humble
import edkrepo.commands.humble.common_humble as common_humble
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo, get_manifest_repo_path, get_manifest_repo_info_from_config
import edkrepo.common.ui_functions as ui_functions
from edkrepo.config.config_factory import get_workspace_manifest, get_workspace_path, get_checked_out_pin_file
from edkrepo.common.edkrepo_exception import EdkrepoManifestInvalidException, EdkrepoPinFileNotFoundException


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

        if args.verbose:
            man_repo = find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'])
            print()
            print(common_humble.MANIFEST_REPO.format(man_repo))
            print(common_humble.MANIFEST_REPO_PATH.format(get_manifest_repo_path(man_repo, config)))
            url, branch, _ = get_manifest_repo_info_from_config(man_repo, config)
            print(common_humble.MANIFEST_REPO_URL.format(url))
            print(common_humble.MANIFEST_REPO_BRANCH.format(branch))
            print()

        for combo in sorted(combo_list):

            if args.verbose:
                if 'pin:' in combo.lower():
                    description = humble.PIN_DESCRIPTION
                else:
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
                
                sources = []
                sources = self._identify_combo_sources(combo, manifest, config)
                    
                length = len(max([source.root for source in sources], key=len))
                if 'pin' in combo.lower():
                    for source in sources:
                        ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.commit), header=False)
                else:
                    for source in sources:
                        if source.commit:
                            ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.commit), header=False)
                        elif source.tag and not source.commit:
                            ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.tag), header=False)
                        elif source.branch and not (source.commit or source.tag) :
                            ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.branch), header=False)
                        elif source.patch_set:
                            ui_functions.print_info_msg(humble.REPO_DETAILS.format(source.root.ljust(length), source.patch_set), header=False)

    def _identify_combo_sources(self, combo, manifest, config):
        """
        Identify and return the source objects for a given combo.
        """
        sources = []
        if 'pin' in combo.lower():
            pin_filename = combo.split(':', 1)[1].strip()
            try:
                pin_manifest = get_checked_out_pin_file(pin_filename, manifest, config, get_workspace_path())
                if pin_manifest and pin_manifest.combinations:
                    sources = pin_manifest.get_repo_sources(pin_manifest.combinations[0].name)
                else:
                    sources = manifest.get_repo_sources(combo)
            except (EdkrepoPinFileNotFoundException, EdkrepoManifestInvalidException) as e:
                ui_functions.print_warning_msg(f"Failed to load pin file '{pin_filename}': {e}", header=False)
                sources = manifest.get_repo_sources(combo)
        else:
            sources = manifest.get_repo_sources(combo)
        return sources

