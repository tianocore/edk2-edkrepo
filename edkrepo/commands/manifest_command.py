#!/usr/bin/env python3
#
## @file
# manifest_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import copy
import os

from colorama import Fore

from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import ColorArgument
import edkrepo.commands.arguments.manifest_args as arguments
from edkrepo.common.edkrepo_exception import EdkrepoWorkspaceInvalidException
from edkrepo.common.common_repo_functions import pull_latest_manifest_repo, verify_manifest_data
from edkrepo.common.ui_functions import init_color_console
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo_manifest_parser.edk_manifest import CiIndexXml


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
        init_color_console(args.color)

        # Get path to global manifest file
        global_manifest_directory = config['cfg_file'].manifest_repo_abs_local_path
        if args.verbose:
            print("Manifest directory:")
            print(global_manifest_directory)
            print()
        index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')

        pull_latest_manifest_repo(args, config)
        print()

        ci_index_xml = CiIndexXml(index_path)

        try:
            current_project = get_workspace_manifest().project_info.codename
        except EdkrepoWorkspaceInvalidException:
            current_project = None

        # Attempt to make sure the manifest data is good
        try:
            verify_manifest_data(global_manifest_directory, config, verbose=args.verbose, verify_all=True, verify_archived=args.archived)
        except:
            print()

        print("Projects:")
        for project in ci_index_xml.project_list:
            if project == current_project:
                print("* {}{}{}".format(Fore.GREEN, project, Fore.RESET))
            else:
                print("  {}".format(project))
            if args.verbose:
                print("   -> {}".format(ci_index_xml.get_project_xml(project)))

        if args.archived:
            print()
            print("Archived Projects:")
            for project in ci_index_xml.archived_project_list:
                if project == current_project:
                    print("* {}{}{}".format(Fore.GREEN, project, Fore.RESET))
                else:
                    print("  {}".format(project))
                if args.verbose:
                    print("   -> {}".format(ci_index_xml.get_project_xml(project)))
