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

import edkrepo.common.common_repo_functions as edkrepo_common
import edkrepo.common.edkrepo_exception as edkrepo_exception
import edkrepo.common.humble as humble
import edkrepo.common.ui_functions as ui_functions

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

    if repo_to_clone.branch:
        clone_cmd_args['target_branch'] = '-b {}'.format(repo_to_clone.branch)
    
    if args:
        try:
            if args.treeless:
                clone_cmd_args['treeless'] = '--filter=tree:0'
        except AttributeError:
            pass
        try:
            if args.blobless:
                clone_cmd_args['blobless'] = '--filter=blob:none'
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

def clone_single_repository(manifest, repo_to_clone, workspace_dir, global_manifest_path, args=None, cache_obj=None):
    '''Clones a single repository and checks it out onto the ref defined in the project manifest file.
    
    Arguments:
    manifest - the EdkManifest object representing the full project
    repo_to_clone - a repo_source tuple describing the repository to be cloned
    workspace_dir - the workspace directory into which the repository will be cloned
    global_manifest_path - the path to the global manifest dir
    args - all command line arguments
    cache_obj - An EdkRepo cache object
    '''
    if repo_to_clone.patch_set:
        patchset = manifest.get_patchset(repo_to_clone.patch_set, repo_to_clone.remote_name)
    elif not repo_to_clone.branch and not repo_to_clone.tag and not repo_to_clone.commit:
        raise edkrepo_exception.EdkrepoManifestInvalidException(humble.MISSING_BRANCH_COMMIT)

    if cache_obj:
        cache_path = cache_obj.get_cache_path(repo_to_clone.remote_url)
        ui_functions.print_info_msg('Cloning {} Repository from local cache: {}'.format(repo_to_clone.root, cache_path), header=False)
    else:
        cache_path = None
        ui_functions.print_info_msg('Cloning {} Repository from: {}'.format(repo_to_clone.root, str(repo_to_clone.remote_url)), header=False)

    clone_cmd = generate_clone_cmd(repo_to_clone, workspace_dir, args, cache_path)
    clone_cmd_output = subprocess.run(clone_cmd, stdout=subprocess.PIPE, universal_newlines=True, shell=True)
    repo = Repo(os.path.join(workspace_dir, repo_to_clone.root))

    if repo_to_clone.patch_set:
        edkrepo_common.create_local_branch(repo_to_clone.patch_set, patchset, global_manifest_path, manifest, repo)
    elif repo_to_clone.commit:
        if args.verbose and (repo_to_clone.branch or repo_to_clone.tag):
                ui_functions.print_info_msg(humble.MULTIPLE_SOURCE_ATTRIBUTES_SPECIFIED.format(repo_to_clone.root))
        repo.git.checkout(repo_to_clone.commit)
    elif repo_to_clone.tag and repo_to_clone.commit is None:
            if args.verbose and repo_to_clone.branch:
                ui_functions.print_info_msg(humble.TAG_AND_BRANCH_SPECIFIED.format(repo_to_clone.root))
            repo.git.checkout(repo_to_clone.tag)

