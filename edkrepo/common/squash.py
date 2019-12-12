#!/usr/bin/env python3
#
## @file
# squash.py
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
from subprocess import check_call

from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoWorkspaceInvalidException
from edkrepo.common.humble import COMMIT_NOT_FOUND, NOT_GIT_REPO, SQUASH_COMMON_ANCESTOR_REQUIRED

def get_git_repo_root():
    path = os.path.realpath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(path, '.git')):
            return path
        if os.path.dirname(path) == path:
            break
        path = os.path.dirname(path)
    raise EdkrepoWorkspaceInvalidException(NOT_GIT_REPO)

def split_commit_range(commit_range):
    if len(commit_range.split('...')) == 2:
        return commit_range.split('...')
    else:
        return commit_range.split('..')

def get_start_and_end_commit(commit_ish, repo):
    #Determine the start and end commit for the upcoming squash
    (commit1, commit2) = split_commit_range(commit_ish)
    try:
        repo.rev_parse(commit1)
    except:
        raise EdkrepoInvalidParametersException(COMMIT_NOT_FOUND.format(commit1))
    try:
        repo.rev_parse(commit2)
    except:
        raise EdkrepoInvalidParametersException(COMMIT_NOT_FOUND.format(commit2))
    if len(repo.git.rev_list(commit_ish).split()) <= 0:
        raise EdkrepoInvalidParametersException(SQUASH_COMMON_ANCESTOR_REQUIRED.format(commit1, commit2))
    if str(repo.commit(commit1)) not in repo.git.rev_list(commit2).split():
        temp_commit = commit1
        commit1 = commit2
        commit2 = temp_commit
        if str(repo.commit(commit1)) not in repo.git.rev_list(commit2).split():
            raise EdkrepoInvalidParametersException(SQUASH_COMMON_ANCESTOR_REQUIRED.format(commit1, commit2))
    start_commit = get_oldest_ancestor(commit1, commit2, repo)
    end_commit = str(repo.commit(commit2))
    return (start_commit, end_commit)

def get_oldest_ancestor(commit1, commit2, repo):
    a = repo.git.rev_list('--first-parent', commit1).split()
    b = repo.git.rev_list('--first-parent', commit2).split()
    for commit in a:
        if commit in b:
            return commit
    return None

def commit_list_to_message(commit_list, one_line, repo):
    message_list = []
    for commit in commit_list:
        if one_line:
            message_list.append('{}: {}'.format(commit, repo.commit(commit).message.split('\n')[0]))
        else:
            for line in repo.commit(commit).message.split('\n'):
                message_list.append(line)
    return '\n'.join(message_list)

def squash_commits(start_commit, end_commit, branch_name, commit_message, repo, reset_author=True):
    #Create a branch at the latest commit
    local_branch = repo.create_head(branch_name, end_commit)
    repo.heads[local_branch.name].checkout()
    #Set up environment variables for automating the interactive rebase
    git_automation_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'git_automation')
    if sys.platform == "win32":
        os.environ['GIT_SEQUENCE_EDITOR'] = 'py "{}"'.format(os.path.join(git_automation_dir, "rebase_squash.py"))
        os.environ['GIT_EDITOR'] = 'py "{}"'.format(os.path.join(git_automation_dir, "commit_msg.py"))
    else:
        os.environ['GIT_SEQUENCE_EDITOR'] = os.path.join(git_automation_dir, "rebase_squash.py")
        os.environ['GIT_EDITOR'] = os.path.join(git_automation_dir, "commit_msg.py")
    os.environ['COMMIT_MESSAGE'] = commit_message
    #Do an interactive rebase back to the oldest commit, squashing all commits between then and now
    check_call(['git', 'rebase', '-i', '{}'.format(start_commit)])
    if reset_author:
        repo.git.commit('--amend', '--no-edit', '--reset-author', '--signoff')
    del os.environ['GIT_SEQUENCE_EDITOR']
    del os.environ['GIT_EDITOR']
    del os.environ['COMMIT_MESSAGE']
