#!/usr/bin/env python3
#
## @file
# reference_repos_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import edkrepo.commands.edkrepo_command as edkrepo_command
import edkrepo.commands.arguments.reference_repos_args as arguments
import edkrepo.commands.humble.reference_repos_humble as humble
import edkrepo.common.edkrepo_exception as edkrepo_exception
import edkrepo.common.ui_functions as ui_functions


class ReferenceRepos(edkrepo_command.EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'reference-repos'
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
        args.append({'choice': 'enable',
                     'parent': 'action',
                     'help-text': arguments.ENABLE_HELP})
        args.append({'choice': 'disable',
                     'parent': 'action',
                     'help-text': arguments.DISABLE_HELP})
        args.append({'choice': 'enable-dissociate',
                     'parent': 'action',
                     'help-text': arguments.ENABLE_DISSOCIATE_HELP})
        args.append({'choice': 'disable-dissociate',
                     'parent': 'action',
                     'help-text': arguments.DISABLE_DISSOCIATE_HELP})
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
                     'help-text': arguments.NAME_HELP})
        args.append({'name': 'url',
                     'positional': True,
                     'required': False,
                     'position': 2,
                     'help-text': arguments.URL_HELP})
        args.append({'name': 'path',
                     'positional': True,
                     'required': False,
                     'position': 3,
                     'help-text': arguments.PATH_HELP})
        return metadata

    def run_command(self, args, config):
        user_cfg = config['user_cfg_file']

        if args.action == 'list':
            self._list_reference_repos(user_cfg)

        elif args.action in ('add', 'remove') and not args.name:
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.NAME_REQUIRED)

        elif args.action == 'add' and (not args.url or not args.path):
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.ADD_REQUIRED)

        elif args.action == 'add':
            if args.name in user_cfg.reference_repos_enabled_for:
                raise edkrepo_exception.EdkrepoInvalidParametersException(humble.ALREADY_EXISTS.format(args.name))
            user_cfg.add_reference_repo(args.name, args.url, args.path)
            ui_functions.print_info_msg(humble.REPO_ADDED.format(args.name), header=False)

        elif args.action == 'remove':
            if args.name not in user_cfg.reference_repos_enabled_for:
                raise edkrepo_exception.EdkrepoInvalidParametersException(humble.REMOVE_NOT_EXIST.format(args.name))
            user_cfg.remove_reference_repo(args.name)
            ui_functions.print_info_msg(humble.REPO_REMOVED.format(args.name), header=False)

        elif args.action == 'enable':
            user_cfg.set_reference_repos_enable_by_default(True)
            ui_functions.print_info_msg(humble.REFERENCE_REPOS_ENABLED, header=False)

        elif args.action == 'disable':
            user_cfg.set_reference_repos_enable_by_default(False)
            ui_functions.print_info_msg(humble.REFERENCE_REPOS_DISABLED, header=False)

        elif args.action == 'enable-dissociate':
            user_cfg.set_reference_repos_dissociate_by_default(True)
            ui_functions.print_info_msg(humble.DISSOCIATE_ENABLED, header=False)

        elif args.action == 'disable-dissociate':
            user_cfg.set_reference_repos_dissociate_by_default(False)
            ui_functions.print_info_msg(humble.DISSOCIATE_DISABLED, header=False)

    def _list_reference_repos(self, user_cfg):
        ui_functions.print_info_msg(humble.LIST_HEADER, header=False)
        ui_functions.print_info_msg(humble.ENABLE_BY_DEFAULT.format(user_cfg.reference_repos_enabled_by_default), header=False)
        ui_functions.print_info_msg(humble.DISSOCIATE_BY_DEFAULT.format(user_cfg.reference_repos_dissociate_by_default), header=False)
        enabled_for = user_cfg.reference_repos_enabled_for
        ui_functions.print_info_msg(humble.ENABLED_FOR.format(', '.join(enabled_for) if enabled_for else '(none)'), header=False)
        if enabled_for:
            for name in enabled_for:
                url = user_cfg.get_reference_repo_url(name)
                path = user_cfg.get_reference_repo_path(name)
                ui_functions.print_info_msg(
                    humble.REPO_ENTRY.format(name, url or '(not set)', path or '(not set)'),
                    header=False)
        else:
            ui_functions.print_info_msg(humble.NO_REPOS_CONFIGURED, header=False)
