#!/usr/bin/env python3
#
## @file
# sync_command.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import itertools
import os
import shutil
import sys
import time
import re

import git
from git import Repo
from git.exc import GitCommandError

# Our modules
from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import DryRunArgument, SubmoduleSkipArgument, SourceManifestRepoArgument
import edkrepo.commands.arguments.sync_args as arguments
from edkrepo.common.progress_handler import GitProgressHandler
from edkrepo.common.edkrepo_exception import EdkrepoUncommitedChangesException, EdkrepoManifestNotFoundException
from edkrepo.common.edkrepo_exception import EdkrepoManifestChangedException
from edkrepo.common.humble import SYNC_UNCOMMITED_CHANGES, SYNC_MANIFEST_NOT_FOUND, SYNC_URL_CHANGE, SYNC_COMBO_CHANGE
from edkrepo.common.humble import SYNC_SOURCE_MOVE_WARNING, SYNC_REMOVE_WARNING, SYNC_REMOVE_LIST_END_FORMATTING
from edkrepo.common.humble import SYNC_MANIFEST_DIFF_WARNING, SYNC_MANIFEST_UPDATE
from edkrepo.common.humble import SPARSE_RESET, SPARSE_CHECKOUT, SYNC_REPO_CHANGE, SYNCING, FETCHING, UPDATING_MANIFEST
from edkrepo.common.humble import NO_SYNC_DETACHED_HEAD, SYNC_COMMITS_ON_TARGET, SYNC_ERROR
from edkrepo.common.humble import MIRROR_BEHIND_PRIMARY_REPO, SYNC_NEEDS_REBASE, INCLUDED_FILE_NAME
from edkrepo.common.humble import SYNC_BRANCH_CHANGE_ON_LOCAL, SYNC_INCOMPATIBLE_COMBO
from edkrepo.common.humble import SYNC_REBASE_CALC_FAIL, SYNC_MOVE_FAILED
from edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble import SOURCE_MANIFEST_REPO_NOT_FOUND
from edkrepo.common.pathfix import get_actual_path, expanduser
from edkrepo.common.common_cache_functions import get_repo_cache_obj
from edkrepo.common.common_repo_functions import clone_repos, sparse_checkout_enabled
from edkrepo.common.common_repo_functions import reset_sparse_checkout, sparse_checkout, verify_single_manifest
from edkrepo.common.common_repo_functions import checkout_repos, check_dirty_repos
from edkrepo.common.common_repo_functions import update_editor_config
from edkrepo.common.common_repo_functions import update_repo_commit_template, get_latest_sha
from edkrepo.common.common_repo_functions import has_primary_repo_remote, fetch_from_primary_repo, in_sync_with_primary
from edkrepo.common.common_repo_functions import update_hooks, combinations_in_manifest
from edkrepo.common.common_repo_functions import write_included_config, remove_included_config
from edkrepo.common.workspace_maintenance.git_config_maintenance import clean_git_globalconfig
from edkrepo.common.workspace_maintenance.workspace_maintenance import generate_name_for_obsolete_backup
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_workspace_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.ui_functions import init_color_console
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest, get_edkrepo_global_data_directory
from edkrepo.config.config_factory import get_workspace_manifest_file
from edkrepo.config.tool_config import SUBMODULE_CACHE_REPO_NAME
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml
from project_utils.submodule import deinit_submodules, maintain_submodules


class SyncCommand(EdkrepoCommand):

    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'sync'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'fetch',
                     'positional' : False,
                     'required' : False,
                     'help-text': arguments.FETCH_HELP})
        args.append({'name' : 'update-local-manifest',
                     'short-name': 'u',
                     'required' : False,
                     'help-text' : arguments.UPDATE_LOCAL_MANIFEST_HELP})
        args.append({'name' : 'override',
                     'short-name': 'o',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.OVERRIDE_HELP})
        args.append(SubmoduleSkipArgument)
        args.append(SourceManifestRepoArgument)
        return metadata

    def run_command(self, args, config):
        workspace_path = get_workspace_path()
        initial_manifest = get_workspace_manifest()
        current_combo = initial_manifest.general_config.current_combo
        initial_sources = initial_manifest.get_repo_sources(current_combo)
        initial_hooks = initial_manifest.repo_hooks
        initial_combo = current_combo

        source_global_manifest_repo = find_source_manifest_repo(initial_manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo)
        pull_workspace_manifest_repo(initial_manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo, False)
        cfg_manifest_repos, user_cfg_manifest_repos, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
        if source_global_manifest_repo in cfg_manifest_repos:
            global_manifest_directory = config['cfg_file'].manifest_repo_abs_path(source_global_manifest_repo)
            verify_single_manifest(config['cfg_file'], source_global_manifest_repo, get_workspace_manifest_file(), args.verbose)
        elif source_global_manifest_repo in user_cfg_manifest_repos:
            global_manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(source_global_manifest_repo)
            verify_single_manifest(config['user_cfg_file'], source_global_manifest_repo, get_workspace_manifest_file(), args.verbose)
        else:
            global_manifest_directory = None

        if global_manifest_directory is not None:
            update_editor_config(config, global_manifest_directory)

        if not args.update_local_manifest:
            self.__check_for_new_manifest(args, config, initial_manifest, workspace_path, global_manifest_directory)
        check_dirty_repos(initial_manifest, workspace_path)

        # Determine if sparse checkout needs to be disabled for this operation
        sparse_settings = initial_manifest.sparse_settings
        sparse_enabled = sparse_checkout_enabled(workspace_path, initial_sources)
        sparse_reset_required = False
        if sparse_settings is None:
            sparse_reset_required = True
        elif args.update_local_manifest:
            sparse_reset_required = True
        if sparse_enabled and sparse_reset_required:
            print(SPARSE_RESET)
            reset_sparse_checkout(workspace_path, initial_sources)

        # Get the latest manifest if requested
        if args.update_local_manifest:  # NOTE: hyphens in arg name replaced with underscores due to argparse
            self.__update_local_manifest(args, config, initial_manifest, workspace_path, global_manifest_directory)
        manifest = get_workspace_manifest()
        if args.update_local_manifest:
            try:
                repo_sources_to_sync = manifest.get_repo_sources(current_combo)
            except ValueError:
                # The manifest file was updated and the initial combo is no longer present so use the default combo
                current_combo = manifest.general_config.default_combo
                repo_sources_to_sync = manifest.get_repo_sources(current_combo)
        else:
            repo_sources_to_sync = manifest.get_repo_sources(current_combo)
        manifest.write_current_combo(current_combo)

        # At this point both new and old manifest files are ready so we can deinit any
        # submodules that are removed due to a manifest update.
        if not args.skip_submodule:
            deinit_submodules(workspace_path, initial_manifest, initial_combo,
                              manifest, current_combo, args.verbose)

        sync_error = False
        # Calculate the hooks which need to be updated, added or removed for the sync
        if args.update_local_manifest:
            new_hooks = manifest.repo_hooks
            hooks_add = set(new_hooks).difference(set(initial_hooks))
            hooks_update = set(initial_hooks).intersection(set(new_hooks))
            hooks_uninstall = set(initial_hooks).difference(set(new_hooks))
        else:
            hooks_add = None
            hooks_update = initial_hooks
            hooks_uninstall = None
        # Update submodule configuration
        if not args.update_local_manifest: #Performance optimization, __update_local_manifest() will do this
            self.__check_submodule_config(workspace_path, manifest, repo_sources_to_sync)
        clean_git_globalconfig()
        for repo_to_sync in repo_sources_to_sync:
            local_repo_path = os.path.join(workspace_path, repo_to_sync.root)
            # Update any hooks
            if global_manifest_directory is not None:
                update_hooks(hooks_add, hooks_update, hooks_uninstall, local_repo_path, repo_to_sync, config, global_manifest_directory)
            repo = Repo(local_repo_path)
            #Fetch notes
            repo.remotes.origin.fetch("refs/notes/*:refs/notes/*")
            if repo_to_sync.commit is None and repo_to_sync.tag is None:
                local_commits = False
                initial_active_branch = repo.active_branch
                repo.remotes.origin.fetch("refs/heads/{0}:refs/remotes/origin/{0}".format(repo_to_sync.branch))
                #The new branch may not exist in the heads list yet if it is a new branch
                repo.git.checkout(repo_to_sync.branch)
                if not args.fetch:
                    print (SYNCING.format(repo_to_sync.root, repo.active_branch))
                else:
                    print (FETCHING.format(repo_to_sync.root, repo.active_branch))
                try:
                    repo.remotes.origin.fetch()
                except GitCommandError as e:
                    prune_needed = False
                    prune_needed_heuristic_str = "error: some local refs could not be updated"
                    if e.stdout.strip().find(prune_needed_heuristic_str) != -1:
                        prune_needed = True
                    if e.stderr.strip().find(prune_needed_heuristic_str) != -1:
                        prune_needed = True
                    if prune_needed:
                        time.sleep(1.0)
                        repo.git.remote('prune', 'origin')
                        time.sleep(1.0)
                        repo.remotes.origin.fetch()
                    else:
                        raise
                if has_primary_repo_remote(repo, args.verbose):
                    fetch_from_primary_repo(repo, repo_to_sync, args.verbose)
                if not args.override and not repo.is_ancestor(ancestor_rev='HEAD', rev='origin/{}'.format(repo_to_sync.branch)):
                    print(SYNC_COMMITS_ON_TARGET.format(repo_to_sync.branch, repo_to_sync.root))
                    local_commits = True
                    sync_error = True
                if not args.fetch and (not local_commits or args.override):
                    repo.head.reset(commit='origin/{}'.format(repo_to_sync.branch), working_tree=True)

                # Check to see if mirror is up to date
                if not in_sync_with_primary(repo, repo_to_sync, args.verbose):
                    print(MIRROR_BEHIND_PRIMARY_REPO)

                # Switch back to the initially active branch before exiting
                repo.heads[initial_active_branch.name].checkout()

                # Warn user if local branch is behind target branch
                try:
                    latest_sha = get_latest_sha(repo, repo_to_sync.branch)
                    commit_count = int(repo.git.rev_list('--count', '{}..HEAD'.format(latest_sha)))
                    branch_origin = next(itertools.islice(repo.iter_commits(), commit_count, commit_count + 1))
                    behind_count = int(repo.git.rev_list('--count', '{}..{}'.format(branch_origin.hexsha, latest_sha)))
                    if behind_count:
                        print(SYNC_NEEDS_REBASE.format(
                            behind_count=behind_count,
                            target_remote='origin',
                            target_branch=repo_to_sync.branch,
                            local_branch=initial_active_branch.name,
                            repo_folder=repo_to_sync.root))
                        print()
                except:
                    print(SYNC_REBASE_CALC_FAIL)
            elif args.verbose:
                print(NO_SYNC_DETACHED_HEAD.format(repo_to_sync.root))

            # Update commit message templates
            if global_manifest_directory is not None:
                update_repo_commit_template(workspace_path, repo, repo_to_sync, config, global_manifest_directory)

        if sync_error:
            print(SYNC_ERROR)

        # Initialize submodules
        if not args.skip_submodule:
            cache_path = None
            cache_obj = get_repo_cache_obj(config)
            if cache_obj is not None:
                cache_path = cache_obj.get_cache_path(SUBMODULE_CACHE_REPO_NAME)
            maintain_submodules(workspace_path, manifest, current_combo, args.verbose, cache_path)

        # Restore sparse checkout state
        if sparse_enabled:
            print(SPARSE_CHECKOUT)
            sparse_checkout(workspace_path, repo_sources_to_sync, manifest)

    def __update_local_manifest(self, args, config, initial_manifest, workspace_path, global_manifest_directory):
        #if the manifest repository for the current manifest was not found then there is no project with the manifest
        #specified project name in the index file for any of the manifest repositories
        if global_manifest_directory is None:
            raise EdkrepoManifestNotFoundException(SOURCE_MANIFEST_REPO_NOT_FOUND.format(initial_manifest.project_info.codename))

        local_manifest_dir = os.path.join(workspace_path, 'repo')
        current_combo = initial_manifest.general_config.current_combo
        initial_sources = initial_manifest.get_repo_sources(current_combo)
        # Do a fetch for each repo in the initial to ensure that newly created upstream branches are available
        for initial_repo in initial_sources:
            local_repo_path = os.path.join(workspace_path, initial_repo.root)
            repo = Repo(local_repo_path)
            origin = repo.remotes.origin
            try:
                origin.fetch()
            except GitCommandError as e:
                prune_needed = False
                prune_needed_heuristic_str = "error: some local refs could not be updated"
                if e.stdout.strip().find(prune_needed_heuristic_str) != -1:
                    prune_needed = True
                if e.stderr.strip().find(prune_needed_heuristic_str) != -1:
                    prune_needed = True
                if prune_needed:
                    # The sleep is to give the operating system time to close all the file handles that Git has open
                    time.sleep(1.0)
                    repo.git.remote('prune', 'origin')
                    time.sleep(1.0)
                    origin.fetch()
                else:
                    raise

        #see if there is an entry in CiIndex.xml that matches the prject name of the current manifest
        index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
        ci_index_xml = CiIndexXml(index_path)
        if initial_manifest.project_info.codename not in ci_index_xml.project_list:
            raise EdkrepoManifestNotFoundException(SYNC_MANIFEST_NOT_FOUND.format(initial_manifest.project_info.codename))
        initial_manifest_remotes = {name:url for name, url in initial_manifest.remotes}
        ci_index_xml_rel_path = os.path.normpath(ci_index_xml.get_project_xml(initial_manifest.project_info.codename))
        global_manifest_path = os.path.join(global_manifest_directory, ci_index_xml_rel_path)
        new_manifest_to_check = ManifestXml(global_manifest_path)

        # Does the current combo exist in the new manifest? If not check to see if you can use the repo sources from
        # the default combo
        initial_combos = combinations_in_manifest(initial_manifest)
        new_combos = combinations_in_manifest(new_manifest_to_check)
        if current_combo not in new_combos:
            new_sources_for_current_combo = new_manifest_to_check.get_repo_sources(new_manifest_to_check.general_config.default_combo)
            new_sources = new_sources_for_current_combo
        else:
            new_sources_for_current_combo = new_manifest_to_check.get_repo_sources(current_combo)
            new_sources = new_manifest_to_check.get_repo_sources(current_combo)

        remove_included_config(initial_manifest.remotes, initial_manifest.submodule_alternate_remotes, local_manifest_dir)
        write_included_config(new_manifest_to_check.remotes, new_manifest_to_check.submodule_alternate_remotes, local_manifest_dir)

        self.__check_submodule_config(workspace_path, new_manifest_to_check, new_sources_for_current_combo)

        # Check that the repo sources lists are the same. If they are not the same and the override flag is not set, throw an exception.
        if not args.override and set(initial_sources) != set(new_sources):
            raise EdkrepoManifestChangedException(SYNC_REPO_CHANGE.format(initial_manifest.project_info.codename))
        elif args.override and set(initial_sources) != set(new_sources):
            #get a set of repo source tuples that are not in both the new and old manifest
            uncommon_sources = []
            initial_common = []
            new_common = []
            for initial in initial_sources:
                common = False
                for new in new_sources:
                    if initial.root == new.root:
                        if initial.remote_name == new.remote_name:
                            if initial.remote_url == new.remote_url:
                                # If the source is unchanged between the old and the new manifest,
                                # add it to the common lists
                                common = True
                                initial_common.append(initial)
                                new_common.append(new)
                                break
                # If the source is different between the old and the new manifest, add it to the uncommon list
                if not common:
                    uncommon_sources.append(initial)
            for new in new_sources:
                common = False
                for initial in initial_sources:
                    if new.root == initial.root:
                        if new.remote_name == initial.remote_name:
                            if new.remote_url == initial.remote_url:
                                common = True
                                break
                # If the source is different between the old and the new manifest, add it to the uncommon list
                if not common:
                    uncommon_sources.append(new)
            uncommon_sources = set(uncommon_sources)
            initial_common = set(initial_common)
            new_common = set(new_common)
            sources_to_move = []
            sources_to_remove = []
            sources_to_clone = []
            for source in uncommon_sources:
                found_source = False
                for source_to_check in initial_sources:
                    if source_to_check.root == source.root:
                        if source_to_check.remote_name == source.remote_name:
                            if source_to_check.remote_url == source.remote_url:
                                found_source = True
                                break
                # If the source that is different came from the old manifest, then it is now outdated and either needs
                # to be deleted or moved to an archival location.
                if found_source:
                    roots = [s.root for s in new_sources]
                    # If there is a source in the new manifest that goes into the same folder name as a source in the
                    # old manifest, then we need to move that old folder to an archival location.
                    if source.root in roots:
                        sources_to_move.append(source)
                    else:
                        # If it doesn't exist at all in the new manifest, tell the user it is old and no longer used.
                        sources_to_remove.append(source)
                else:
                    # If the source that is different came from the new manifest, then we need to clone that new
                    # Git repository.
                    sources_to_clone.append(source)
            init_color_console(False)
            # Move the obsolete Git repositories to archival locations.
            for source in sources_to_move:
                old_dir = os.path.join(workspace_path, source.root)
                new_dir = generate_name_for_obsolete_backup(old_dir)
                print(SYNC_SOURCE_MOVE_WARNING.format(source.root, new_dir))
                new_dir = os.path.join(workspace_path, new_dir)
                try:
                    shutil.move(old_dir, new_dir)
                except:
                    print(SYNC_MOVE_FAILED.format(initial_dir=source.root, new_dir=new_dir))
                    raise
            # Tell the user about any Git repositories that are no longer used.
            if len(sources_to_remove) > 0:
                print(SYNC_REMOVE_WARNING)
            for source in sources_to_remove:
                path_to_source = os.path.join(workspace_path, source.root)
                print(path_to_source)
            if len(sources_to_remove) > 0:
                print(SYNC_REMOVE_LIST_END_FORMATTING)
            # Clone any new Git repositories
            clone_repos(args, workspace_path, sources_to_clone, new_manifest_to_check.repo_hooks, config, new_manifest_to_check)
            # Make a list of and only checkout repos that were newly cloned. Sync keeps repos on their initial active branches
            # cloning the entire combo can prevent existing repos from correctly being returned to their proper branch
            repos_to_checkout = []
            if sources_to_clone:
                for new_source in new_sources_for_current_combo:
                    for source in sources_to_clone:
                        if source.root == new_source.root:
                            repos_to_checkout.append(source)
            repos_to_checkout.extend(self.__check_combo_sha_tag_branch(workspace_path, initial_common, new_common))
            if repos_to_checkout:
                checkout_repos(args.verbose, args.override, repos_to_checkout, workspace_path, new_manifest_to_check)

        #remove the old manifest file and copy the new one
        print(UPDATING_MANIFEST)
        local_manifest_path = os.path.join(local_manifest_dir, 'Manifest.xml')
        os.remove(local_manifest_path)
        shutil.copy(global_manifest_path, local_manifest_path)

        # Update the source manifest repository tag in the local copy of the manifest XML
        new_manifest = ManifestXml(local_manifest_path)
        try:
            if 'source_manifest_repo' in vars(args).keys():
                find_source_manifest_repo(new_manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo)
            else:
                find_source_manifest_repo(new_manifest, config['cfg_file'], config['user_cfg_file'], None)
        except EdkrepoManifestNotFoundException:
            pass

    def __check_combo_sha_tag_branch(self, workspace_path, initial_sources, new_sources):
        # Checks for changes in the defined SHAs, Tags or branches in the checked out combo. Returns
        # a list of repos to checkout. Checks to see if user is on appropriate SHA, tag or branch and
        # throws and exception if not.
        repos_to_checkout = []
        for initial_source in initial_sources:
            for new_source in new_sources:
                if initial_source.root == new_source.root and initial_source.remote_name == new_source.remote_name and initial_source.remote_url == new_source.remote_url:
                    local_repo_path = os.path.join(workspace_path, initial_source.root)
                    repo = Repo(local_repo_path)
                    if initial_source.commit and initial_source.commit != new_source.commit:
                        if repo.head.object.hexsha != initial_source.commit:
                            print(SYNC_BRANCH_CHANGE_ON_LOCAL.format(initial_source.branch, new_source.branch, initial_source.root))
                        repos_to_checkout.append(new_source)
                        break
                    elif initial_source.tag and initial_source.tag != new_source.tag:
                        tag_sha = repo.git.rev_list('-n 1', initial_source.tag) #according to gitpython docs must change - to _
                        if tag_sha != repo.head.object.hexsha:
                            print(SYNC_BRANCH_CHANGE_ON_LOCAL.format(initial_source.branch, new_source.branch, initial_source.root))
                        repos_to_checkout.append(new_source)
                        break
                    elif initial_source.branch and initial_source.branch != new_source.branch:
                        if repo.active_branch.name != initial_source.branch:
                            print(SYNC_BRANCH_CHANGE_ON_LOCAL.format(initial_source.branch, new_source.branch, initial_source.root))
                        repos_to_checkout.append(new_source)
                        break
        return repos_to_checkout

    def __check_for_new_manifest(self, args, config, initial_manifest, workspace_path, global_manifest_directory):
        #if the manifest repository for the current manifest was not found then there is no project with the manifest
        #specified project name in the index file for any of the manifest repositories
        if global_manifest_directory is None:
            if args.override:
                return
            else:
                raise EdkrepoManifestNotFoundException(SYNC_MANIFEST_NOT_FOUND.format(initial_manifest.project_info.codename))

        #see if there is an entry in CiIndex.xml that matches the prject name of the current manifest
        index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
        ci_index_xml = CiIndexXml(index_path)
        if initial_manifest.project_info.codename not in ci_index_xml.project_list:
            if args.override:
                return
            else:
                raise EdkrepoManifestNotFoundException(SYNC_MANIFEST_NOT_FOUND.format(initial_manifest.project_info.codename))
        ci_index_xml_rel_path = ci_index_xml.get_project_xml(initial_manifest.project_info.codename)
        global_manifest_path = os.path.join(global_manifest_directory, os.path.normpath(ci_index_xml_rel_path))
        global_manifest = ManifestXml(global_manifest_path)
        if not initial_manifest.equals(global_manifest, True):
            init_color_console(False)
            print(SYNC_MANIFEST_DIFF_WARNING)
            print(SYNC_MANIFEST_UPDATE)

    def __check_submodule_config(self, workspace_path, manifest, repo_sources):
        gitconfigpath = os.path.normpath(expanduser("~/.gitconfig"))
        gitglobalconfig = git.GitConfigParser(gitconfigpath, read_only=False)
        try:
            local_manifest_dir = os.path.join(workspace_path, "repo")
            includeif_regex = re.compile('^includeIf "gitdir:(/.+)/"$')
            rewrite_everything = False
            #Generate list of .gitconfig files that should be present in the workspace
            included_configs = []
            for remote in manifest.remotes:
                included_config_name = os.path.join(local_manifest_dir, INCLUDED_FILE_NAME.format(remote.name))
                included_config_name = get_actual_path(included_config_name)
                remote_alts = [submodule for submodule in manifest.submodule_alternate_remotes if submodule.remote_name == remote.name]
                if remote_alts:
                    included_configs.append((remote.name, included_config_name))
            for source in repo_sources:
                for included_config in included_configs:
                    #If the current repository has a .gitconfig (aka it has a submodule)
                    if included_config[0] == source.remote_name:
                        if not os.path.isfile(included_config[1]):
                            rewrite_everything = True
                        gitdir = str(os.path.normpath(os.path.join(workspace_path, source.root)))
                        gitdir = get_actual_path(gitdir)
                        gitdir = gitdir.replace('\\', '/')
                        if sys.platform == "win32":
                            gitdir = '/{}'.format(gitdir)
                        #Make sure the .gitconfig file is referenced by the global git config
                        found_include = False
                        for section in gitglobalconfig.sections():
                            data = includeif_regex.match(section)
                            if data:
                                if data.group(1) == gitdir:
                                    found_include = True
                                    break
                        if not found_include:
                            #If the .gitconfig file is missing from the global git config, add it.
                            if sys.platform == "win32":
                                path = '/{}'.format(included_config[1])
                            else:
                                path = included_config[1]
                            path = path.replace('\\', '/')
                            section = 'includeIf "gitdir:{}/"'.format(gitdir)
                            gitglobalconfig.add_section(section)
                            gitglobalconfig.set(section, 'path', path)
                            gitglobalconfig.release()
                            gitglobalconfig = git.GitConfigParser(gitconfigpath, read_only=False)
            if rewrite_everything:
                #If one or more of the .gitconfig files are missing, re-generate all the .gitconfig files
                remove_included_config(manifest.remotes, manifest.submodule_alternate_remotes, local_manifest_dir)
                write_included_config(manifest.remotes, manifest.submodule_alternate_remotes, local_manifest_dir)
        finally:
            gitglobalconfig.release()


