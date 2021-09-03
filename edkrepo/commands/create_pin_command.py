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
from edkrepo.common.humble import COMMIT_MESSAGE, PIN_PATH_NOT_PRESENT, PIN_FILE_ALREADY_EXISTS, PATH_AND_FILEPATH_USED
from edkrepo.common.humble import MISSING_REPO
from edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble import SOURCE_MANIFEST_REPO_NOT_FOUND
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_workspace_manifest_repo
from edkrepo.config.config_factory import get_workspace_manifest, get_workspace_path
from edkrepo_manifest_parser.edk_manifest import ManifestXml


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
        args.append({'name': 'push',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.PUSH_HELP})
        args.append(SourceManifestRepoArgument)
        return metadata

    def run_command(self, args, config):
        # Check if --push and file path provided
        if args.push and os.path.dirname(args.PinFileName):
            raise EdkrepoInvalidParametersException(PATH_AND_FILEPATH_USED)

        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()

        if args.push:
            src_manifest_repo = find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo)
            pull_workspace_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo, False)
            cfg, user_cfg, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
            manifest_repo_path = None
            if src_manifest_repo in cfg:
                manifest_repo_path = config['cfg_file'].manifest_repo_abs_path(src_manifest_repo)
            elif src_manifest_repo in user_cfg:
                manifest_repo_path = config['user_cfg_file'].manifest_repo_abs_path(src_manifest_repo)
            if manifest_repo_path is None:
                raise EdkrepoManifestNotFoundException(SOURCE_MANIFEST_REPO_NOT_FOUND.format(manifest.project_info.codename))
        # If the push flag is enabled use general_config.pin_path to determine global manifest relative location to save
        # pin file to.
        if args.push and manifest.general_config.pin_path is not None:
            pin_dir = os.path.join(manifest_repo_path, os.path.normpath(manifest.general_config.pin_path))
            pin_file_name = os.path.join(pin_dir, args.PinFileName)
        elif args.push and manifest.general_config.pin_path is None:
            raise EdkrepoManifestInvalidException(PIN_PATH_NOT_PRESENT)
        # If not using the push flag ignore the local manifest's pin file field and set the pinname/path == to the file
        # name provided. If a relative paths is provided save the file relative to the current working directory.
        elif not args.push and os.path.isabs(os.path.normpath(args.PinFileName)):
            pin_file_name = os.path.normpath(args.PinFileName)
        elif not args.push:
            pin_file_name = os.path.abspath(os.path.normpath(args.PinFileName))
        # If the directory that the pin file is saved in does not exist create it and ensure pin file name uniqueness.
        if os.path.isfile(pin_file_name):
            raise EdkrepoInvalidParametersException(PIN_FILE_ALREADY_EXISTS)
        if not os.path.exists(os.path.dirname(pin_file_name)):
            os.mkdir(os.path.dirname(pin_file_name))

        repo_sources = manifest.get_repo_sources(manifest.general_config.current_combo)

        # get the repo sources and commit ids for the pin
        print(GENERATING_PIN_DATA.format(manifest.project_info.codename, manifest.general_config.current_combo))
        updated_repo_sources = []
        for repo_source in repo_sources:
            local_repo_path = os.path.join(workspace_path, repo_source.root)
            if not os.path.exists(local_repo_path):
                raise EdkrepoWorkspaceCorruptException(MISSING_REPO.format(repo_source.root))
            repo = Repo(local_repo_path)
            commit_id = repo.head.commit.hexsha
            if args.verbose:
                print(GENERATING_REPO_DATA.format(repo_source.root))
                print(BRANCH.format(repo_source.branch))
                print(COMMIT.format(commit_id))
            updated_repo_source = repo_source._replace(commit=commit_id)
            updated_repo_sources.append(updated_repo_source)

        # create the pin
        print(WRITING_PIN_FILE.format(pin_file_name))
        manifest.generate_pin_xml(args.Description, manifest.general_config.current_combo, updated_repo_sources,
                                  filename=pin_file_name)

        # commit and push the pin file
        if args.push:
            manifest_repo = Repo(manifest_repo_path)
            # Create a local branch with the same name as the pin file arg and check it out before attempting the push
            # to master
            master_branch = manifest_repo.active_branch
            local_branch = manifest_repo.create_head(args.PinFileName)
            manifest_repo.heads[local_branch.name].checkout()
            manifest_repo.git.add(pin_file_name)
            manifest_repo.git.commit(m=COMMIT_MESSAGE.format(manifest.project_info.codename, args.Description))
            # Try to push if the push fails re update the manifest repo and rebase from master
            try:
                manifest_repo.git.push('origin', 'HEAD:master')
            except:
                manifest_repo.heads[master_branch.name].checkout()
                origin = manifest_repo.remotes.origin
                origin.pull()
                manifest_repo.heads[local_branch.name].checkout()
                manifest_repo.git.rebase('master')
                manifest_repo.git.push('origin', 'HEAD:master')
            finally:
                manifest_repo.heads[master_branch.name].checkout()
                manifest_repo.delete_head(local_branch, '-D')
