#!/usr/bin/env python3
#
## @file
# clone_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import shutil

from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import SubmoduleSkipArgument
import edkrepo.commands.arguments.clone_args as arguments
from edkrepo.common.common_repo_functions import pull_latest_manifest_repo, clone_repos, sparse_checkout, verify_manifest_data
from edkrepo.common.common_repo_functions import case_insensitive_single_match, update_editor_config
from edkrepo.common.common_repo_functions import write_included_config, write_conditional_include
from edkrepo.common.common_repo_functions import find_project_in_index
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoManifestInvalidException
from edkrepo.common.humble import CLONE_INVALID_WORKSPACE, CLONE_INVALID_PROJECT_ARG, CLONE_INVALID_COMBO_ARG
from edkrepo.common.humble import SPARSE_CHECKOUT, CLONE_INVALID_LOCAL_ROOTS
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml


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
        return metadata


    def run_command(self, args, config):
        pull_latest_manifest_repo(args, config)
        update_editor_config(config)
        name_or_manifest = args.ProjectNameOrManifestFile
        workspace_dir = args.Workspace
        # Check to see if requested workspace exists. If not create it. If so check for empty
        if workspace_dir == '.':
            # User has selected the directory they are running edkrepo from
            workspace_dir = os.getcwd()
        else:
            workspace_dir = os.path.abspath(workspace_dir)
        if os.path.isdir(workspace_dir) and os.listdir(workspace_dir):
            raise EdkrepoInvalidParametersException(CLONE_INVALID_WORKSPACE)
        if not os.path.isdir(workspace_dir):
            os.makedirs(workspace_dir)

        # Get path to global manifest file
        global_manifest_directory = config['cfg_file'].manifest_repo_abs_local_path

        # Verify the manifest directory at this point.
        verify_manifest_data(global_manifest_directory, config, verbose=args.verbose, verify_proj=name_or_manifest)

        # Now try to find the correct manifest file.
        index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
        ci_index_xml = CiIndexXml(index_path)

        global_manifest_path = find_project_in_index(name_or_manifest, ci_index_xml, global_manifest_directory, CLONE_INVALID_PROJECT_ARG)

        # Copy project manifest to local manifest dir and rename it Manifest.xml.
        local_manifest_dir = os.path.join(workspace_dir, "repo")
        os.makedirs(local_manifest_dir)
        local_manifest_path = os.path.join(local_manifest_dir, "Manifest.xml")
        shutil.copy(global_manifest_path, local_manifest_path)
        manifest = ManifestXml(local_manifest_path)

        # Process the combination name and make sure it can be found in the manifest
        combo_name = None
        if args.Combination is not None:
            try:
                combo_name = case_insensitive_single_match(args.Combination, [x.name for x in manifest.combinations])
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

        # Get the list of repos to clone and clone them
        manifest_config = manifest.general_config
        if combo_name:
            repo_sources_to_clone = manifest.get_repo_sources(combo_name)
        else:
            repo_sources_to_clone = manifest.get_repo_sources(manifest_config.default_combo)
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
        clone_repos(args, workspace_dir, repo_sources_to_clone, project_client_side_hooks, config, args.skip_submodule, manifest)

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
            print(SPARSE_CHECKOUT)
            sparse_checkout(workspace_dir, repo_sources_to_clone, manifest)
