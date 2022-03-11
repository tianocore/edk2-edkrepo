#!/usr/bin/env python3
#
## @file
# manifest_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import copy
import os

from colorama import Fore

from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import ColorArgument
import edkrepo.commands.arguments.manifest_args as arguments
from edkrepo.common.edkrepo_exception import EdkrepoWorkspaceInvalidException, EdkrepoManifestNotFoundException
from edkrepo.common.common_repo_functions import validate_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_all_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_project_in_single_index
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml
import edkrepo.common.ui_functions as ui_functions


class ManifestCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'manifest'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'archived',
                     'short-name': 'a',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.ARCHIVED_HELP})
        args.append(ColorArgument)
        return metadata

    def run_command(self, args, config):
        print()
        cfg_file = config['cfg_file']
        user_cfg = config['user_cfg_file']
        cfg_man_repos, user_cfg_man_repos, conflicts = list_available_manifest_repos(cfg_file, user_cfg)
        man_repos = {}

        pull_all_manifest_repos(cfg_file, user_cfg, False)

        # Get paths to the global manifest dirs and their index files
        for repo in cfg_man_repos:
            global_manifest_directory = cfg_file.manifest_repo_abs_path(repo)
            index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
            man_repos[repo] = (global_manifest_directory, index_path)
        for repo in user_cfg_man_repos:
            global_manifest_directory = user_cfg.manifest_repo_abs_path(repo)
            index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
            man_repos[repo] = (global_manifest_directory, index_path)

        try:
            wkspc_manifest = get_workspace_manifest()
            current_project = wkspc_manifest.project_info.codename
            src_man_repo = find_source_manifest_repo(wkspc_manifest, cfg_file, user_cfg, None)
        except EdkrepoWorkspaceInvalidException:
            current_project = None
            src_man_repo = None
        except EdkrepoManifestNotFoundException:
            src_man_repo = None


        for repo in man_repos.keys():
            print()
            ui_functions.print_info_msg("Manifest directory:", header = False)
            ui_functions.print_info_msg(repo, header = False)
            if args.verbose:
                ui_functions.print_info_msg('Manifest directory path:', header = False)
                ui_functions.print_info_msg(man_repos[repo][0], header = False)
            print()

            ci_index_xml = CiIndexXml(man_repos[repo][1])

            # Attempt to make sure the manifest data is good
            try:
                validate_manifest_repo(man_repos[repo][0], args.verbose, args.archived)
            except:
                print()

            ui_functions.print_info_msg("Projects:", header = False)
            for project in sorted(ci_index_xml.project_list):
                if (project == current_project and src_man_repo == repo) or (not src_man_repo and project == current_project):
                    ui_functions.print_info_msg(project, header = False)
                else:
                    ui_functions.print_warning_msg(project, header = False)
                if args.verbose:
                    ui_functions.print_info_msg("   -> {}".format(ci_index_xml.get_project_xml(project)), header = False)
                    proj_manifest = ManifestXml(find_project_in_single_index(project, ci_index_xml, man_repos[repo][0])[1])
                    ui_functions.print_info_msg("   -> DevLead: {}".format(' '.join(x for x in proj_manifest.project_info.dev_leads)), header = False)

            if args.archived:
                print()
                ui_functions.print_info_msg("Archived Projects:", header = False)
                for project in sorted(ci_index_xml.archived_project_list):
                    if project == current_project:
                        ui_functions.print_info_msg(project, header = False)
                    else:
                        ui_functions.print_warning_msg(project, header = False)
                    if args.verbose:
                        ui_functions.print_info_msg("   -> {}".format(ci_index_xml.get_project_xml(project)), header = False)
                        proj_manifest = ManifestXml(find_project_in_single_index(project, ci_index_xml, man_repos[repo][0])[1])
                        ui_functions.print_info_msg("   -> DevLead: {}".format(' '.join(x for x in proj_manifest.project_info.dev_leads)), header = False)
