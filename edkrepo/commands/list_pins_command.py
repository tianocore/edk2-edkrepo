#!/usr/bin/env python3
#
## @file
# list_pins_command.py
#
# Copyright (c) 2018 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import subprocess
import sys
import io

from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand, SourceManifestRepoArgument
from edkrepo.common.humble import VERIFY_PROJ_NOT_IN_INDEX
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_workspace_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_project_in_all_indices
from edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble import PROJ_NOT_IN_REPO, SOURCE_MANIFEST_REPO_NOT_FOUND
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo.common.edkrepo_exception import EdkrepoWorkspaceInvalidException, EdkrepoInvalidParametersException
from edkrepo.common.edkrepo_exception import EdkrepoManifestNotFoundException
import edkrepo.commands.arguments.list_pins_args as arguments
import edkrepo.commands.humble.list_pins_humble as humble
from edkrepo.common.common_repo_functions import find_less
from edkrepo.common.logger import get_logger
from edkrepo_manifest_parser.edk_manifest import ManifestXml, CiIndexXml

class ListPinsCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'list-pins'
        metadata['help-text'] = arguments.LIST_PINS_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'description',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.LIST_PINS_DESCRIPTION_ARG_DESC})
        args.append({'name' : 'project',
                     'positional' : False,
                     'required' : False,
                     'nargs' : 1,
                     'action' : 'store',
                     'help-text' : arguments.LIST_PINS_PROJECT_DESCRIPTION})
        args.append(SourceManifestRepoArgument)
        return metadata

    def run_command(self, args, config):
        logger = get_logger()
        less_path, use_less = find_less()
        if use_less:
            output_string = ''
            separator = '\n'
        cfg, user_cfg, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
        try:
            manifest = get_workspace_manifest()
            pull_workspace_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo, False)
            src_manifest_repo = find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo)
            if src_manifest_repo in cfg:
                manifest_directory = config['cfg_file'].manifest_repo_abs_path(src_manifest_repo)
            elif src_manifest_repo in user_cfg:
                manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(src_manifest_repo)
            else:
                raise EdkrepoManifestNotFoundException(SOURCE_MANIFEST_REPO_NOT_FOUND.format(manifest.project_info.codename))
        except EdkrepoWorkspaceInvalidException:
            if not args.project:
                raise EdkrepoInvalidParametersException(humble.NOT_IN_WKSPCE)
            else:
                #arg parse provides a list so only use the first item since we are limiting users to one project
                manifest_repo, src_cfg, manifest_path = find_project_in_all_indices(args.project[0],
                                                                                 config['cfg_file'],
                                                                                 config['user_cfg_file'],
                                                                                 PROJ_NOT_IN_REPO.format(args.project[0]),
                                                                                 SOURCE_MANIFEST_REPO_NOT_FOUND.format(args.project[0]))
                if manifest_repo in cfg:
                    manifest_directory = config['cfg_file'].manifest_repo_abs_path(manifest_repo)
                elif manifest_repo in user_cfg:
                    manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(manifest_repo)
                manifest = ManifestXml(manifest_path)
        if manifest.general_config.pin_path is None:
            logger.info(humble.NO_PIN_FOLDER)
            return
        pin_folder = os.path.normpath(os.path.join(manifest_directory, manifest.general_config.pin_path))
        if args.verbose:
            if not use_less:
                logger.info(humble.PIN_FOLDER.format(pin_folder))
            else:
                output_string = (humble.PIN_FOLDER.format(pin_folder))
        for dirpath, _, filenames in os.walk(pin_folder):
            for file in filenames:
                pin_file = os.path.join(dirpath, file)
                # Capture error output from manifest parser stdout to properly interleave with other pin data
                stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    pin = ManifestXml(pin_file)
                except TypeError:
                    continue
                parse_output = sys.stdout.getvalue()
                sys.stdout = stdout
                if pin.project_info.codename == manifest.project_info.codename:
                    if not use_less:
                        logger.info('Pin File: {}'.format(file))
                        if not args.description:
                            logger.info('Parsing Errors: {}\n'.format(parse_output.strip()), extra={'verbose':args.verbose})
                        if args.description:
                            logger.info('Parsing Errors: {}'.format(parse_output.strip()), extra={'verbose':args.verbose})
                            logger.info('Description: {}\n'.format(pin.project_info.description))
                    elif use_less:
                        output_string = separator.join((output_string, 'Pin File: {}'.format(file)))
                        if args.verbose and not args.description:
                            output_string = separator.join((output_string, 'Parsing Errors: {}\n'.format(parse_output.strip())))
                        elif args.verbose and args.description:
                            output_string = separator.join((output_string, 'Parsing Errors: {}'.format(parse_output.strip())))
                        if args.description:
                            output_string = separator.join((output_string, 'Description: {}\n'.format(pin.project_info.description)))
        if less_path:
            less_output = subprocess.Popen([str(less_path), '-F', '-R', '-S', '-X', '-K'], stdin=subprocess.PIPE, stdout=sys.stdout, universal_newlines=True)
            less_output.communicate(input=output_string)