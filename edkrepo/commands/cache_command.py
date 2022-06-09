#!/usr/bin/env python3
#
## @file
# cache_command.py
#
# Copyright (c) 2020-2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

import edkrepo.commands.arguments.cache_args as arguments
from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import SourceManifestRepoArgument
from edkrepo.commands.humble.cache_humble import CACHE_ENABLED, CACHE_FETCH, CACHE_INFO
from edkrepo.commands.humble.cache_humble import CACHE_INFO_LINE, PROJECT_NOT_FOUND, NO_INSTANCE
from edkrepo.commands.humble.cache_humble import UNABLE_TO_LOAD_MANIFEST, UNABLE_TO_PARSE_MANIFEST
from edkrepo.common.common_cache_functions import add_missing_cache_repos
from edkrepo.common.common_cache_functions import get_repo_cache_obj
from edkrepo.common.edkrepo_exception import EdkrepoCacheException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_project_in_all_indices
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_all_manifest_repos
import edkrepo.common.ui_functions as ui_functions
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo_manifest_parser.edk_manifest import ManifestXml


class CacheCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'cache'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'enable',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.COMMAND_ENABLE_HELP})
        args.append({'name': 'disable',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.COMMAND_DISABLE_HELP})
        args.append({'name': 'update',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.COMMAND_UPDATE_HELP})
        args.append({'name': 'info',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.COMMAND_INFO_HELP})
        args.append({'name': 'path',
                     'positional': False,
                     'required': False,
                     'action': 'store',
                     'help-text': arguments.COMMAND_PATH_HELP})
        args.append({'name': 'project',
                     'positional': True,
                     'required': False,
                     'help-text': arguments.COMMAND_PROJECT_HELP})
        args.append(SourceManifestRepoArgument)
        return metadata

    def run_command(self, args, config):

        if not args.info:
        # Process enable disable requests
            if args.disable:
                config['user_cfg_file'].set_caching_state(False)
            elif args.enable:
                config['user_cfg_file'].set_caching_state(True)

            # Write the cache location to the user_cfg
            if not args.path:
                config['user_cfg_file'].set_cache_path(cache_path=None, default=True)
            elif args.path:
                config['user_cfg_file'].set_cache_path(cache_path=os.path.normpath(os.path.normcase(args.path)), default=False)

        # Get the current state now that we have processed enable/disable
        cache_state = config['user_cfg_file'].caching_state

        ui_functions.print_info_msg(CACHE_ENABLED.format(cache_state))
        if not cache_state:
            return
        # State is enabled so make sure cache directory exists
        cache_obj = get_repo_cache_obj(config)

        pull_all_manifest_repos(config['cfg_file'], config['user_cfg_file'])

        # Check to see if a manifest was provided and add any missing remotes
        manifest = None
        if args.project is not None:
            manifest = _get_manifest(args.project, config, args.source_manifest_repo)
        else:
            try:
                manifest = get_workspace_manifest()
            except Exception:
                pass

        # If manifest is provided attempt to add any remotes that do not exist
        if manifest is not None:
            add_missing_cache_repos(cache_obj, manifest, True)

        # Display all the cache information
        if args.info:
            ui_functions.print_info_msg(CACHE_INFO)
            info = cache_obj.get_cache_info(args.verbose)
            for item in info:
                ui_functions.print_info_msg(CACHE_INFO_LINE.format(item.path, item.remote, item.url))

        # Do an update if requested
        if args.update:
            ui_functions.print_info_msg(CACHE_FETCH)
            cache_obj.update_cache(verbose=True)

        # Close the cache repos
        cache_obj.close(args.verbose)


def _get_manifest(project, config, source_manifest_repo=None):
    try:
        manifest_repo, source_cfg, manifest_path = find_project_in_all_indices(
            project,
            config['cfg_file'],
            config['user_cfg_file'],
            PROJECT_NOT_FOUND.format(project),
            NO_INSTANCE.format(project),
            source_manifest_repo)
    except Exception:
        raise EdkrepoCacheException(UNABLE_TO_LOAD_MANIFEST)
    try:
        manifest = ManifestXml(manifest_path)
    except Exception:
        raise EdkrepoCacheException(UNABLE_TO_PARSE_MANIFEST)
    return manifest
