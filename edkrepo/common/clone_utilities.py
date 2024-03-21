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