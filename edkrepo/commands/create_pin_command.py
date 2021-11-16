#!/usr/bin/env python3
#
## @file
# create_pin_command.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
from collections import namedtuple

from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand, SourceManifestRepoArgument
import edkrepo.commands.arguments.create_pin_args as arguments
from edkrepo.common.edkrepo_exception import EdkrepoManifestInvalidException, EdkrepoInvalidParametersException
from edkrepo.common.edkrepo_exception import EdkrepoWorkspaceCorruptException, EdkrepoManifestNotFoundException
from edkrepo.common.humble import WRITING_PIN_FILE, GENERATING_PIN_DATA, GENERATING_REPO_DATA, BRANCH, COMMIT
from edkrepo.common.humble import COMMIT_MESSAGE, PIN_PATH_NOT_PRESENT, PIN_FILE_ALREADY_EXISTS
from edkrepo.common.humble import MISSING_REPO
from edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble import SOURCE_MANIFEST_REPO_NOT_FOUND
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_workspace_manifest_repo
from edkrepo.config.config_factory import get_workspace_manifest, get_workspace_path
from edkrepo_manifest_parser.edk_manifest import ManifestXml
import edkrepo.common.ui_functions as ui_functions



class CreatePinCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'create-pin'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        metadata['alias'] = 'crp'
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'PinFileName',
                     'positional' : True,
                     'position' : 0,
                     'required' : True,
                     'help-text' : arguments.NAME_HELP})
        args.append({'name' : 'Description',
                     'positional' : True,
                     'position' : 1,
                     'required' : True,
                     'help-text' : arguments.DESCRIPTION_HELP})
        args.append(SourceManifestRepoArgument)
        return metadata

    def run_command(self, args, config):

        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()

        # Set the pinname/path == to the file name provided.
        # If a relative paths is provided save the file relative to the current working directory.
        if os.path.isabs(os.path.normpath(args.PinFileName)):
            pin_file_name = os.path.normpath(args.PinFileName)
        else:
            pin_file_name = os.path.abspath(os.path.normpath(args.PinFileName))
        # If the directory that the pin file is saved in does not exist create it and ensure pin file name uniqueness.
        if os.path.isfile(pin_file_name):
            raise EdkrepoInvalidParametersException(PIN_FILE_ALREADY_EXISTS)
        if not os.path.exists(os.path.dirname(pin_file_name)):
            os.mkdir(os.path.dirname(pin_file_name))

        repo_sources = manifest.get_repo_sources(manifest.general_config.current_combo)

        # get the repo sources and commit ids for the pin
        ui_functions.print_info_msg(GENERATING_PIN_DATA.format(manifest.project_info.codename, manifest.general_config.current_combo), header = False)
        updated_repo_sources = []
        for repo_source in repo_sources:
            local_repo_path = os.path.join(workspace_path, repo_source.root)
            if not os.path.exists(local_repo_path):
                raise EdkrepoWorkspaceCorruptException(MISSING_REPO.format(repo_source.root))
            repo = Repo(local_repo_path)
            commit_id = repo.head.commit.hexsha
            if args.verbose:
                ui_functions.print_info_msg(GENERATING_REPO_DATA.format(repo_source.root), header = False)
                ui_functions.print_info_msg(BRANCH.format(repo_source.branch), header = False)
                ui_functions.print_info_msg(COMMIT.format(commit_id), header = False)
            updated_repo_source = repo_source._replace(commit=commit_id)
            updated_repo_sources.append(updated_repo_source)

        # create the pin
        ui_functions.print_info_msg(WRITING_PIN_FILE.format(pin_file_name), header = False)
        manifest.generate_pin_xml(args.Description, manifest.general_config.current_combo, updated_repo_sources,
                                  filename=pin_file_name)

