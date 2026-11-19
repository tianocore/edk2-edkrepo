#!/usr/bin/env python3
#
## @file
# git_exclude_maintenance.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import ntpath
import os

def write_git_exclude(repo_path, exclude_pattern):
    '''Writes the given exclude patterns to the .git/info/exclude file in the specified repository.

    Arguments:
    repo_path - The path to the repository
    exclude_patterns - A list of patterns to add to the exclude file
    '''
    exclude_file_path = os.path.join(repo_path, '.git', 'info', 'exclude')
    with open(exclude_file_path, 'a') as exclude_file:
        exclude_file.write(exclude_pattern + '\n')

def generate_exclude_pattern(parent_repo_path, nested_repo_path):
    '''Generates a git/info/exclude entry for the nested repository.
     \ are replaced with / to align with .gitignore syntax. '''
    path_module = ntpath if ntpath.splitdrive(parent_repo_path)[0] or ntpath.splitdrive(nested_repo_path)[0] else os.path
    parent_repo_path = path_module.normpath(parent_repo_path)
    nested_repo_path = path_module.normpath(nested_repo_path)
    common_path = path_module.commonpath([parent_repo_path, nested_repo_path])
    # / as the common prefix is valid but not meaningful in this context
    # Corner cases such as different casing (in Case Sensitive filesystems), the presence of redundant separators, etc... result
    # in os.path.commonpath not raising a value error. Manual verification raises the expected ValueError to catch these.
    if common_path == path_module.sep or not (parent_repo_path.startswith(common_path) and nested_repo_path.startswith(common_path)):
        raise ValueError
    relative_path = path_module.relpath(nested_repo_path, common_path).replace("\\", "/")
    return '{}/'.format(relative_path)
