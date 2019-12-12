#!/usr/bin/env python3
#
## @file
# squash_command.py
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.squash_args as arguments
import edkrepo.commands.humble.squash_humble as humble
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoWorkspaceInvalidException
from edkrepo.common.squash import get_git_repo_root, split_commit_range, get_start_and_end_commit
from edkrepo.common.squash import commit_list_to_message, squash_commits

class SquashCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'squash'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'commit-ish',
                     'positional' : True,
                     'position' : 0,
                     'required': True,
                     'description' : arguments.COMMIT_ISH_DESCRIPTION,
                     'help-text' : arguments.COMMIT_ISH_HELP})
        args.append({'name' : 'new-branch',
                     'positional' : True,
                     'position' : 1,
                     'required': True,
                     'description' : arguments.NEW_BRANCH_DESCRIPTION,
                     'help-text' : arguments.NEW_BRANCH_HELP})
        args.append({'name': 'oneline',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.ONELINE_HELP})
        return metadata

    def run_command(self, args, config):
        commit_ish = vars(args)['commit-ish']
        new_branch = vars(args)['new-branch']
        one_line = vars(args)['oneline']
        repo_path = get_git_repo_root()
        #Initialize GitPython
        repo = Repo(repo_path)
        #Make sure the branch does not exist
        if branch_name_exists(new_branch, repo):
            raise EdkrepoInvalidParametersException(humble.BRANCH_EXISTS.format(new_branch))
        single_commit = True
        try:
            repo.rev_parse(commit_ish)
        except:
            if len(split_commit_range(commit_ish)) <= 1:
                raise EdkrepoInvalidParametersException(humble.MULTIPLE_COMMITS_REQUIRED)
            single_commit = False
        if single_commit:
            raise EdkrepoInvalidParametersException(humble.MULTIPLE_COMMITS_REQUIRED)
        (start_commit, end_commit) = get_start_and_end_commit(commit_ish, repo)
        if one_line:
            commit_message = humble.COMMIT_MESSAGE
        else:
            commit_message = ''
        commit_message += get_squash_commit_message_list(repo, start_commit, end_commit, one_line)
        if one_line:
            commit_message += '\n'
        original_branch = repo.heads[repo.active_branch.name]
        try:
            squash_commits(start_commit, end_commit, new_branch, commit_message, repo)
        except:
            if new_branch in repo.heads:
                original_branch.checkout()
                repo.git.branch('-D', new_branch)
            raise
        finally:
            original_branch.checkout()

def branch_name_exists(branch_name, repo):
    if branch_name in [x.name for x in repo.heads]:
        return True
    else:
        return False

def get_commit_list(repo, start_commit, end_commit):
    return repo.git.rev_list('{}..{}'.format(start_commit, end_commit)).split()

def get_squash_commit_message_list(repo, start_commit, end_commit, one_line):
    return commit_list_to_message(get_commit_list(repo, start_commit, end_commit), one_line, repo)
