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

import edkrepo.commands.arguments.clone_args as arguments
import edkrepo.commands.edkrepo_command as edkrepo_command
import edkrepo.common.common_cache_functions as common_cache_functions
import edkrepo.common.common_repo_functions as common_repo_functions
import edkrepo.common.edkrepo_exception as edkrepo_exception
import edkrepo.common.humble as humble
import edkrepo.common.pathfix as pathfix
import edkrepo.common.ui_functions as ui_functions
import edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble as manifest_repos_maintenance_humble
import edkrepo.common.workspace_maintenance.manifest_repos_maintenance as manifest_repos_maintenance
import edkrepo.common.workspace_maintenance.workspace_maintenance as workspace_maintenance
import edkrepo.config.tool_config as tool_config
import edkrepo_manifest_parser.edk_manifest as edk_manifest
import project_utils.submodule as submodule_utils
from colorama import Fore
from edkrepo.commands.humble.reference_repos_humble import NO_DISSOCIATE_WARNING


class CloneCommand(edkrepo_command.EdkrepoCommand):
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
        args.append({'name': 'treeless',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.TREELESS_HELP})
        args.append({'name': 'blobless',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.BLOBLESS_HELP})
        args.append({'name': 'full',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.FULL_HELP})
        args.append(({'name': 'single-branch',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.SINGLE_BRANCH_HELP}))
        args.append(({'name': 'no-tags',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.NO_TAGS_HELP}))
        args.append({'name': 'reference-if-able',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.REFERENCE_IF_ABLE_HELP})
        args.append({'name': 'no-reference-if-able',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.NO_REFERENCE_IF_ABLE_HELP})
        args.append({'name': 'dissociate',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.DISSOCIATE_HELP})
        args.append({'name': 'no-dissociate',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.NO_DISSOCIATE_HELP})
        args.append(edkrepo_command.SubmoduleSkipArgument)
        args.append(edkrepo_command.SourceManifestRepoArgument)
        return metadata


    def run_command(self, args, config):
        manifest_repos_maintenance.pull_all_manifest_repos(config['cfg_file'], config['user_cfg_file'], False)

        workspace_dir = args.Workspace
        # Check to see if requested workspace exists. If not create it. If so check for empty
        if workspace_dir == '.':
            # User has selected the directory they are running edkrepo from
            workspace_dir = os.getcwd()
        else:
            workspace_dir = os.path.abspath(workspace_dir)
        if sys.platform == "win32":
            subst = pathfix.get_subst_drive_dict()
            drive = os.path.splitdrive(workspace_dir)[0][0].upper()
            if drive in subst:
                workspace_dir = os.path.join(subst[drive], os.path.splitdrive(workspace_dir)[1][1:])
                workspace_dir = os.path.normpath(workspace_dir)
        if os.path.isdir(workspace_dir) and os.listdir(workspace_dir):
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.CLONE_INVALID_WORKSPACE)
        if not os.path.isdir(workspace_dir):
            os.makedirs(workspace_dir)

        cfg, user_cfg, conflicts = manifest_repos_maintenance.list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
        try:
            manifest_repo, source_cfg, global_manifest_path = manifest_repos_maintenance.find_project_in_all_indices(args.ProjectNameOrManifestFile,
                                                                    config['cfg_file'],
                                                                    config['user_cfg_file'],
                                                                    manifest_repos_maintenance_humble.PROJ_NOT_IN_REPO.format(args.ProjectNameOrManifestFile),
                                                                    manifest_repos_maintenance_humble.SOURCE_MANIFEST_REPO_NOT_FOUND.format(args.ProjectNameOrManifestFile),
                                                                    args.source_manifest_repo)
        except edkrepo_exception.EdkrepoManifestNotFoundException:
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.CLONE_INVALID_PROJECT_ARG)

        manifest_repository_path = manifest_repos_maintenance.get_manifest_repo_path(manifest_repo, config)

        # If this manifest is in a defined manifest repository validate the manifest within the manifest repo
        if manifest_repo in cfg:
            common_repo_functions.verify_single_manifest(config['cfg_file'], manifest_repo, global_manifest_path)
            common_repo_functions.update_editor_config(config, config['cfg_file'].manifest_repo_abs_path(manifest_repo))
        elif manifest_repo in user_cfg:
            common_repo_functions.verify_single_manifest(config['user_cfg_file'], manifest_repo, global_manifest_path)
            common_repo_functions.update_editor_config(config, config['user_cfg_file'].manifest_repo_abs_path(manifest_repo))

        # Copy project manifest to local manifest dir and rename it Manifest.xml.
        local_manifest_dir = os.path.join(workspace_dir, "repo")
        os.makedirs(local_manifest_dir)
        local_manifest_path = os.path.join(local_manifest_dir, "Manifest.xml")
        # If JSON, write to XML. Else, simple copy
        file_ext = os.path.splitext(global_manifest_path)[1]
        if file_ext == '.json':
            json_manifest = edk_manifest.ManifestXml(global_manifest_path)
            json_manifest.write_tree(local_manifest_path)
        else:
            shutil.copy(global_manifest_path, local_manifest_path)
        manifest = edk_manifest.ManifestXml(local_manifest_path)

        # Update the source manifest repository tag in the local copy of the manifest XML
        try:
            if 'source_manifest_repo' in vars(args).keys():
                manifest_repos_maintenance.find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo)
            else:
                manifest_repos_maintenance.find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], None)
        except edkrepo_exception.EdkrepoManifestNotFoundException:
            pass

        # Process the combination name and make sure it can be found in the manifest
        if args.Combination is not None:
            try:
                combo_name = workspace_maintenance.case_insensitive_single_match(args.Combination, common_repo_functions.combinations_in_manifest(manifest))
            except:
                #remove the repo directory and Manifest.xml from the workspace so the next time the user trys to clone
                #they will have an empty workspace and then raise an exception
                shutil.rmtree(local_manifest_dir)
                raise edkrepo_exception.EdkrepoInvalidParametersException(humble.CLONE_INVALID_COMBO_ARG)
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
                raise edkrepo_exception.EdkrepoManifestInvalidException(humble.CLONE_INVALID_LOCAL_ROOTS)
        project_client_side_hooks = manifest.repo_hooks
        # Set up submodule alt url config settings prior to cloning any repos
        submodule_included_configs = common_repo_functions.write_included_config(manifest.remotes, manifest.submodule_alternate_remotes, local_manifest_dir)
        common_repo_functions.write_conditional_include(workspace_dir, repo_sources_to_clone, submodule_included_configs)

        # Determine if caching is going to be used and then clone
        cache_obj = common_cache_functions.get_repo_cache_obj(config)
        if cache_obj is not None:
            common_cache_functions.add_missing_cache_repos(cache_obj, manifest, args.verbose)

        # Resolve reference repository settings
        use_reference = config['user_cfg_file'].reference_repos_enabled_by_default
        use_dissociate = config['user_cfg_file'].reference_repos_dissociate_by_default
        if args.reference_if_able:
            use_reference = True
        if args.no_reference_if_able:
            use_reference = False
        if args.dissociate:
            use_dissociate = True
        if args.no_dissociate:
            use_dissociate = False
        if use_reference and not use_dissociate:
            ui_functions.print_info_msg('{}{}{}'.format(Fore.YELLOW, NO_DISSOCIATE_WARNING, Fore.RESET), header=False)
        reference_path_map = {}
        if use_reference:
            for ref_name in config['user_cfg_file'].reference_repos_enabled_for:
                ref_url = config['user_cfg_file'].get_reference_repo_url(ref_name)
                ref_path = config['user_cfg_file'].get_reference_repo_path(ref_name)
                if ref_url and ref_path:
                    reference_path_map[ref_url.lower()] = ref_path

        clone_times = common_repo_functions.clone_repos(args, workspace_dir, repo_sources_to_clone, project_client_side_hooks, config, manifest, manifest_repository_path, cache_obj, reference_path_map=reference_path_map, dissociate=use_dissociate)

        # Init submodules
        if not args.skip_submodule:
            cache_path = None
            if cache_obj is not None:
                cache_path = cache_obj.get_cache_path(tool_config.SUBMODULE_CACHE_REPO_NAME)
            submodule_utils.maintain_submodules(workspace_dir, manifest, combo_name, args.verbose, cache_path)

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
            ui_functions.print_info_msg(humble.SPARSE_CHECKOUT)
            common_repo_functions.sparse_checkout(workspace_dir, repo_sources_to_clone, manifest)


        # Print performance timing if requested
        if args.performance:
            print()
            for repo_root, duration in clone_times:
                ui_functions.print_info_msg(humble.CLONE_TIME.format(repo_root, duration), header=False)
