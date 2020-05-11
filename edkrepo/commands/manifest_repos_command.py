#!/usr/bin/env python3
#
## @file
# manifest_repos_command.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import configparser

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.manifest_repo_args as arguments
import edkrepo.commands.humble.manifest_repos_humble as humble
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos




class ManifestRepos(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'manifest-repos'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'choice': 'list',
                     'parent': 'action',
                     'help-text': arguments.LIST_HELP})
        args.append({'choice': 'add',
                     'parent': 'action',
                     'help-text': arguments.ADD_HELP})
        args.append({'choice': 'remove',
                     'parent': 'action',
                     'help-text': arguments.REMOVE_HELP})
        args.append({'name': 'action',
                     'positional': True,
                     'position': 0,
                     'required': True,
                     'choices': True,
                     'help-text': arguments.ACTION_HELP})
        args.append({'name': 'name',
                     'positional': True,
                     'required': False,
                     'position': 1,
                     'nargs' : 1,
                     'help-text': arguments.NAME_HELP})
        args.append({'name': 'branch',
                     'positional': True,
                     'required': False,
                     'position': 3,
                     'nargs' : 1,
                     'help-text': arguments.BRANCH_HELP})
        args.append({'name': 'url',
                     'positional': True,
                     'required': False,
                     'position': 2,
                     'nargs' : 1,
                     'help-text': arguments.URL_HELP})
        args.append({'name': 'path',
                     'positional': True,
                     'required': False,
                     'position': 4,
                     'nargs' : 1,
                     'help-text': arguments.LOCAL_PATH_HELP})
        return metadata

    def run_command(self, args, config):
        cfg_repos, user_cfg_repos, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])

        if args.action == 'list':
            for repo in cfg_repos:
                print(humble.CFG_LIST_ENTRY.format(repo))
            for repo in user_cfg_repos:
                print(humble.USER_CFG_LIST_ENTRY.format(repo))

        elif (args.action == ('add' or 'remove')) and not args.name:
            raise EdkrepoInvalidParametersException(humble.NAME_REQUIRED)
        elif args.action == 'add' and not (args.branch or args.url or args.local_path):
            raise EdkrepoInvalidParametersException(humble.ADD_REQUIRED)
        elif args.action == 'remove' and args.name and args.name in cfg_repos:
            raise EdkrepoInvalidParametersException(humble.CANNOT_REMOVE_CFG)
        elif args.action =='remove' and args.name not in config['user_cfg_file'].manifest_repo_list:
            raise EdkrepoInvalidParametersException(humble.REMOVE_NOT_EXIST)
        elif args.action == 'add' and (args.name in cfg_repos or args.name in user_cfg_repos):
            raise EdkrepoInvalidParametersException(humble.ALREADY_EXISTS.format(args.name))

        user_cfg_file_path = config['user_cfg_file'].cfg_filename

        if args.action == 'add' or 'remove':
            user_cfg_file = configparser.ConfigParser(allow_no_value=True)
            user_cfg_file.read(user_cfg_file_path)
            if args.action == 'add':
                user_cfg_file.set('manifest-repos', args.name, None)
                user_cfg_file.add_section(args.name)
                user_cfg_file.set(args.name, 'URL', args.url)
                user_cfg_file.set(args.name, 'Branch', args.branch)
                user_cfg_file.set(args.name, 'LocalPath', args.path)
            if args.action == 'remove':
                user_cfg_file.remove_option('manifest-repos', args.name)
                user_cfg_file.remove_section(args.name)
            with open(user_cfg_file_path, 'w') as cfg_stream:
                user_cfg_file.write(cfg_stream)
