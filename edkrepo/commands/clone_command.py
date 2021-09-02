#!/usr/bin/env python3
#
## @file
# clone_command.py
#
# Copyright (c) 2017- 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import shutil
import sys

from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import SubmoduleSkipArgument, SourceManifestRepoArgument
import edkrepo.commands.arguments.clone_args as arguments
from edkrepo.common.common_cache_functions import get_repo_cache_obj
from edkrepo.common.common_cache_functions import add_missing_cache_repos
from edkrepo.common.common_repo_functions import clone_repos, sparse_checkout, verify_single_manifest
from edkrepo.common.common_repo_functions import update_editor_config, combinations_in_manifest
from edkrepo.common.common_repo_functions import write_included_config, write_conditional_include
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoManifestInvalidException
from edkrepo.common.edkrepo_exception import EdkrepoManifestNotFoundException
from edkrepo.common.humble import CLONE_INVALID_WORKSPACE, CLONE_INVALID_PROJECT_ARG, CLONE_INVALID_COMBO_ARG
from edkrepo.common.humble import SPARSE_CHECKOUT, CLONE_INVALID_LOCAL_ROOTS
from edkrepo.common.pathfix import get_subst_drive_dict
from edkrepo.common.workspace_maintenance.workspace_maintenance import case_insensitive_single_match
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_all_manifest_repos, find_project_in_all_indices
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble import PROJ_NOT_IN_REPO, SOURCE_MANIFEST_REPO_NOT_FOUND
import edkrepo.common.ui_functions as ui_functions
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml
from project_utils.submodule import maintain_submodules
from edkrepo.config.tool_config import SUBMODULE_CACHE_REPO_NAME


class CloneCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'clone'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'Workspace',
                     'positional': True,
                     'position': 0,
                     'required': True,
                     'help-text': arguments.WORKSPACE_HELP})
        args.append({'name': 'ProjectNameOrManifestFile',
                     'positional': True,
                     'position': 1,
                     'required': True,
                     'help-text': arguments.PROJECT_MANIFEST_HELP})
        args.append({'name': 'Combination',
                     'positional': True,
                     'position': 2,
                     'required': False,
                     'help-text': arguments.COMBINATION_HELP})
        args.append({'name': 'sparse',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.SPARSE_HELP})
        args.append({'name': 'nosparse',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.NO_SPARSE_HELP})
        args.append(SubmoduleSkipArgument)
        args.append(SourceManifestRepoArgument)
        return metadata


    def run_command(self, args, config):
        pull_all_manifest_repos(config['cfg_file'], config['user_cfg_file'], False)

        name_or_manifest = args.ProjectNameOrManifestFile
        workspace_dir = args.Workspace
        # Check to see if requested workspace exists. If not create it. If so check for empty
        if workspace_dir == '.':
            # User has selected the directory they are running edkrepo from
            workspace_dir = os.getcwd()
        else:
            workspace_dir = os.path.abspath(workspace_dir)
        if sys.platform == "win32":
            subst = get_subst_drive_dict()
            drive = os.path.splitdrive(workspace_dir)[0][0].upper()
            if drive in subst:
                workspace_dir = os.path.join(subst[drive], os.path.splitdrive(workspace_dir)[1][1:])
                workspace_dir = os.path.normpath(workspace_dir)
        if os.path.isdir(workspace_dir) and os.listdir(workspace_dir):
            raise EdkrepoInvalidParametersException(CLONE_INVALID_WORKSPACE)
        if not os.path.isdir(workspace_dir):
            os.makedirs(workspace_dir)

        cfg, user_cfg, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
        try:
            manifest_repo, source_cfg, global_manifest_path = find_project_in_all_indices(args.ProjectNameOrManifestFile,
                                                                    config['cfg_file'],
                                                                    config['user_cfg_file'],
                                                                    PROJ_NOT_IN_REPO.format(args.ProjectNameOrManifestFile),
                                                                    SOURCE_MANIFEST_REPO_NOT_FOUND.format(args.ProjectNameOrManifestFile),
                                                                    args.source_manifest_repo)
        except EdkrepoManifestNotFoundException:
            raise EdkrepoInvalidParametersException(CLONE_INVALID_PROJECT_ARG)

        # If this manifest is in a defined manifest repository validate the manifest within the manifest repo
        if manifest_repo in cfg:
            verify_single_manifest(config['cfg_file'], manifest_repo, global_manifest_path)
            update_editor_config(config, config['cfg_file'].manifest_repo_abs_path(manifest_repo))
        elif manifest_repo in user_cfg:
            verify_single_manifest(config['user_cfg_file'], manifest_repo, global_manifest_path)
            update_editor_config(config, config['user_cfg_file'].manifest_repo_abs_path(manifest_repo))

        # Copy project manifest to local manifest dir and rename it Manifest.xml.
        local_manifest_dir = os.path.join(workspace_dir, "repo")
        os.makedirs(local_manifest_dir)
        local_manifest_path = os.path.join(local_manifest_dir, "Manifest.xml")
        shutil.copy(global_manifest_path, local_manifest_path)
        manifest = ManifestXml(local_manifest_path)

        # Update the source manifest repository tag in the local copy of the manifest XML
        try:
            if 'source_manifest_repo' in vars(args).keys():
                find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo)
            else:
                find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], None)
        except EdkrepoManifestNotFoundException:
            pass

        # Process the combination name and make sure it can be found in the manifest
        if args.Combination is not None:
            try:
                combo_name = case_insensitive_single_match(args.Combination, combinations_in_manifest(manifest))
            except:
                #remove the repo directory and Manifest.xml from the workspace so the next time the user trys to clone
                #they will have an empty workspace and then raise an exception
                shutil.rmtree(local_manifest_dir)
                raise EdkrepoInvalidParametersException(CLONE_INVALID_COMBO_ARG)
            manifest.write_current_combo(combo_name)
        elif manifest.is_pin_file():
            # Since pin files are subset of manifest files they do not have a "default combo" it is set to None. In this
            # case use the current_combo instead.
            combo_name = manifest.general_config.current_combo
        else:
            # If a combo was not specified or a pin file used the default combo should be cloned.  Also ensure that the
            # current combo is updated to match.
            combo_name = manifest.general_config.default_combo
            manifest.write_current_combo(combo_name)

        # Get the list of repos to clone and clone them
        repo_sources_to_clone = manifest.get_repo_sources(combo_name)

        #check that the repo sources do not contain duplicated local roots
        local_roots = [r.root for r in repo_sources_to_clone]
        for root in local_roots:
            if local_roots.count(root) > 1:
                #remove the repo dir and manifest.xml so the next time the user trys to clone they will have an empty
                #workspace
                shutil.rmtree(local_manifest_dir)
                raise EdkrepoManifestInvalidException(CLONE_INVALID_LOCAL_ROOTS)
        project_client_side_hooks = manifest.repo_hooks
        # Set up submodule alt url config settings prior to cloning any repos
        submodule_included_configs = write_included_config(manifest.remotes, manifest.submodule_alternate_remotes, local_manifest_dir)
        write_conditional_include(workspace_dir, repo_sources_to_clone, submodule_included_configs)

        # Determine if caching is going to be used and then clone
        cache_obj = get_repo_cache_obj(config)
        if cache_obj is not None:
            add_missing_cache_repos(cache_obj, manifest, args.verbose)
        clone_repos(args, workspace_dir, repo_sources_to_clone, project_client_side_hooks, config, manifest, cache_obj)

        # Init submodules
        if not args.skip_submodule:
            cache_path = None
            if cache_obj is not None:
                cache_path = cache_obj.get_cache_path(SUBMODULE_CACHE_REPO_NAME)
            maintain_submodules(workspace_dir, manifest, combo_name, args.verbose, cache_path)

        # Perform a sparse checkout if requested.
        use_sparse = args.sparse
        sparse_settings = manifest.sparse_settings
        if sparse_settings is None:
            # No SparseCheckout information in manifest so skip sparse checkout
            use_sparse = False
        elif sparse_settings.sparse_by_default:
            # Sparse settings enabled by default for the project
            use_sparse = True
        if args.nosparse:
            # Command line disables sparse checkout
            use_sparse = False
        if use_sparse:
            ui_functions.print_info_msg(SPARSE_CHECKOUT)
            sparse_checkout(workspace_dir, repo_sources_to_clone, manifest)
