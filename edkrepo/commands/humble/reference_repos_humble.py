#!/usr/bin/env python3
#
## @file
# reference_repos_humble.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the reference_repos command and
reference repository clone operations.
'''

LIST_HEADER = 'Reference Repository Configuration:'
ENABLE_BY_DEFAULT = '  Enable by default:      {}'
DISSOCIATE_BY_DEFAULT = '  Dissociate by default:  {}'
ENABLED_FOR = '  Reference enabled for:  {}'
REPO_ENTRY = '    Name: {}  URL: {}  Path: {}'
NO_REPOS_CONFIGURED = '  No reference repositories configured.'
NAME_REQUIRED = 'The "name" argument is required to add or remove a reference repository.'
ADD_REQUIRED = 'The "name", "url", and "path" arguments are required to add a reference repository.'
ALREADY_EXISTS = 'A reference repository entry already exists with name: {}'
REMOVE_NOT_EXIST = 'No reference repository entry with name "{}" exists.'
REFERENCE_REPOS_ENABLED = 'Reference repository use enabled by default.'
REFERENCE_REPOS_DISABLED = 'Reference repository use disabled by default.'
DISSOCIATE_ENABLED = 'Dissociate mode enabled by default.'
DISSOCIATE_DISABLED = 'Dissociate mode disabled by default.'
REPO_ADDED = 'Reference repository "{}" added.'
REPO_REMOVED = 'Reference repository "{}" removed.'
NO_DISSOCIATE_WARNING = ('NOTE: this is a possibly dangerous operation; do not use it unless you understand what it '
                         'does. If you clone your repository using this option and then delete branches (or use any '
                         'other Git command that makes any existing commit unreferenced) in the source repository, '
                         'some objects may become unreferenced (or dangling). These objects may be removed by normal '
                         'Git operations (such as git commit) which automatically call git maintenance run --auto. '
                         'If these objects are removed and were referenced by the cloned repository, then the cloned '
                         'repository will become corrupt.\n'
                         'See: https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---shared')
