#!/usr/bin/env python3
#
## @file
# clone_utilities.py
#
# Copyright (c) 2024, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import subprocess

import git
from git import Repo

import edkrepo.common.edkrepo_exception as edkrepo_exception
import edkrepo.common.humble as humble
import edkrepo.common.ui_functions as ui_functions
import edkrepo.common.workspace_maintenance.manifest_repos_maintenance as manifest_repos_maintenance

def generate_clone_cmd(repo_to_clone, workspace_dir, args=None, cache_path=None):
    '''Generates and returns a string representing a git clone command which can be passed to subprocess for execution.

    Arguments:
    args - all command line arguments
    repo_to_clone - a repo_source tuple describing the repository to be cloned
    workspace_dir - the workspace directory into which the repository will be cloned.
    cache_path - The path to an EdkRepo managed cache
    '''
    local_repo_path = os.path.join(workspace_dir, repo_to_clone.root)
    base_clone_cmd = 'git clone {} {} --progress'.format(repo_to_clone.remote_url, local_repo_path)
    base_clone_cmd_cache = 'git clone {} {} --reference-if-able {} --progress'.format(repo_to_clone.remote_url, local_repo_path, cache_path)
    clone_arg_string = None
    clone_cmd_args = {}
    active_filters = []

    if repo_to_clone.branch:
        clone_cmd_args['target_branch'] = '-b {}'.format(repo_to_clone.branch)

    if args:
        try:
            if args.treeless:
                clone_cmd_args['treeless'] = '--filter=tree:0'
                active_filters.append('treeless')
        except AttributeError:
            pass
        try:
            if args.blobless:
                clone_cmd_args['blobless'] = '--filter=blob:none'
                active_filters.append('blobless')
        except AttributeError:
            pass
        try:
            if args.full:
                clone_cmd_args['full'] = ''
                active_filters.append('full')
        except AttributeError:
            pass
        try:
            if args.single_branch:
                clone_cmd_args['single-branch'] = '--single-branch'
        except AttributeError:
            pass
        try:
            if args.no_tags:
                clone_cmd_args['no-tags'] = '--no-tags'
        except AttributeError:
            pass

    try:
        if repo_to_clone.treeless:
            clone_cmd_args['treeless_manifest_setting'] = '--filter=tree:0'
    except AttributeError:
        pass
    try:
        if repo_to_clone.blobless:
            clone_cmd_args['blobless_manifest_setting'] = '--filter=blob:none'
    except AttributeError:
        pass

    if len(active_filters) > 1:
        raise edkrepo_exception.EdkrepoInvalidConfigOptionException(humble.CONFLICTING_PARTIAL_CLONE)
    elif len(active_filters) == 1:
        clone_cmd_args['treeless_manifest_setting'] = ''
        clone_cmd_args['blobless_manifest_setting'] = ''
    elif 'treeless_manifest_setting' in clone_cmd_args and 'blobless_manifest_setting' in clone_cmd_args:
        raise edkrepo_exception.EdkrepoInvalidConfigOptionException(humble.CONFLICTING_PARTIAL_CLONE)

    if clone_cmd_args:
        clone_arg_string = ' '.join([clone_cmd_args[arg] for arg in clone_cmd_args.keys()])

    if clone_arg_string is None:
        if cache_path is None:
            return base_clone_cmd
        else:
            return base_clone_cmd_cache
    else:
        if cache_path is None:
            return ' '.join([base_clone_cmd, clone_arg_string])
        else:
            return ' '.join([base_clone_cmd_cache, clone_arg_string])

def generate_clone_order(manifest, repo_sources):
    '''Generates and returns a list of repo_source tuples representing the order in which repositories should be cloned.

    Arguments:
    repo_sources - a list of repo_source tuples representing all repositories to be cloned.
    manifest - the ManifestXml object representing the workspace to be created.
    '''
    nested_repos_present = any(repo.nested_repo for repo in repo_sources)
    if not nested_repos_present:
        return repo_sources

    ordered_repos = [repo for repo in repo_sources if not repo.nested_repo]
    remaining_repos = [repo for repo in repo_sources if repo.nested_repo]

    # Keep looping until no more repos can be added
    while remaining_repos:
        print('remaining_repos:{}'.format([repo.root for repo in remaining_repos]))
        added_in_this_iteration = [] # Reset to empty list each iteration
        added_in_this_iteration = [repo for repo in remaining_repos if manifest.get_parent_of_nested_repo(repo_sources, repo.root) in ordered_repos]
        ordered_repos.extend(added_in_this_iteration)
        remaining_repos = [repo for repo in remaining_repos if repo not in added_in_this_iteration]
        if not added_in_this_iteration:
            break

    return ordered_repos

def calculate_source_manifest_repo_directory(args, config, manifest):
    '''Calculates and returns the absolute path to the source manifest repository directory.

    Arguments:
    args - all command line arguments, required when the user passes the --source-manifest-repo flag.
    config - the dictionary representing both the cfg_file and the user_cfg_file contents.
    manifest - the ManifestXml object representing the workspace to be created.
    '''
    try:
        if 'source_manifest_repo' in vars(args).keys():
            src_manifest_repo = manifest_repos_maintenance.find_source_manifest_repo(
                manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo, False)
        else:
            src_manifest_repo = manifest_repos_maintenance.find_source_manifest_repo(
                manifest, config['cfg_file'], config['user_cfg_file'], None, False)
    except edkrepo_exception.EdkrepoManifestNotFoundException:
        src_manifest_repo = None
    if src_manifest_repo:
        cfg, user_cfg, conflicts = manifest_repos_maintenance.list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
        if src_manifest_repo in cfg:
            global_manifest_directory = config['cfg_file'].manifest_repo_abs_path(src_manifest_repo)
        elif src_manifest_repo in user_cfg:
            global_manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(src_manifest_repo)
        else:
            global_manifest_directory = None
    else:
        global_manifest_directory = None

    return global_manifest_directory

