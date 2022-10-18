#!/usr/bin/env python3
#
## @file
# sparse_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.sparse_args as arguments
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest
from edkrepo.common.common_repo_functions import sparse_checkout_enabled, sparse_checkout, reset_sparse_checkout
from edkrepo.common.common_repo_functions import check_dirty_repos
from edkrepo.common.edkrepo_exception import EdkrepoSparseException
from edkrepo.common.humble import SPARSE_ENABLE_DISABLE, SPARSE_NO_CHANGE, SPARSE_ENABLE, SPARSE_DISABLE
from edkrepo.common.humble import SPARSE_STATUS, SPARSE_CHECKOUT_STATUS
from edkrepo.common.humble import SPARSE_BY_DEFAULT_STATUS, SPARSE_ENABLED_REPOS
from edkrepo.common.logger import get_logger


class SparseCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'sparse'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'enable',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.ENABLE_HELP})
        args.append({'name': 'disable',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.DISABLE_HELP})
        return metadata

    def run_command(self, args, config):
        # Collect workspace/repo data
        logger = get_logger()
        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()
        current_combo = manifest.general_config.current_combo
        repo_list = manifest.get_repo_sources(current_combo)
        sparse_settings = manifest.sparse_settings
        sparse_enabled = sparse_checkout_enabled(workspace_path, repo_list)

        # Determine if settings are being chaged or just status display
        if args.enable or args.disable:
            # Handle sparse checkout changes
            if args.enable and args.disable:
                raise EdkrepoSparseException(SPARSE_ENABLE_DISABLE)
            elif (args.enable and sparse_enabled) or (args.disable and not sparse_enabled):
                raise EdkrepoSparseException(SPARSE_NO_CHANGE)

            check_dirty_repos(manifest, workspace_path)

            if args.enable and not sparse_enabled:
                logger.info(SPARSE_ENABLE)
                sparse_checkout(workspace_path, repo_list, manifest)
            elif args.disable and sparse_enabled:
                logger.info(SPARSE_DISABLE)
                reset_sparse_checkout(workspace_path, repo_list, True)
        else:
            # Display the current status of the project
            logger.info(SPARSE_STATUS)
            logger.info(SPARSE_CHECKOUT_STATUS.format(sparse_enabled))
            if sparse_settings is not None:
                logger.info(SPARSE_BY_DEFAULT_STATUS.format(sparse_settings.sparse_by_default))
            logger.info(SPARSE_ENABLED_REPOS.format(current_combo))
            for repo in [x for x in repo_list if x.sparse]:
                logger.info('- {}: {}'.format(repo.root, repo.remote_url))