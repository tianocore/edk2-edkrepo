#!/usr/bin/env python3
#
## @file
# f2f_cherry_pick_command.py
#
# Copyright (c) 2018 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from collections import namedtuple
from difflib import SequenceMatcher
import json
import os
import re
from subprocess import check_call, Popen, PIPE, STDOUT
import sys
import time
import uuid

from git import Repo
from colorama import Fore

from edkrepo.common.common_repo_functions import sparse_checkout_enabled, get_full_path
from edkrepo.commands.edkrepo_command import EdkrepoCommand, ColorArgument
from edkrepo.common.edkrepo_exception import EdkrepoAbortCherryPickException, EdkrepoInvalidParametersException, EdkrepoWorkspaceInvalidException
from edkrepo.common.edkrepo_exception import EdkrepoNotFoundException, EdkrepoGitException
from edkrepo.common.humble import NOT_GIT_REPO, COMMIT_NOT_FOUND
from edkrepo.common.squash import get_git_repo_root, split_commit_range, get_start_and_end_commit
from edkrepo.common.squash import commit_list_to_message, squash_commits
from edkrepo.common.ui_functions import init_color_console
from edkrepo.common.workspace_maintenance.workspace_maintenance import case_insensitive_equal
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest

import edkrepo.commands.arguments.f2f_cherry_pick_args as arguments
import edkrepo.commands.humble.f2f_cherry_pick_humble as humble

FolderCherryPick = namedtuple('FolderCherryPick', ['source', 'destination', 'intermediate', 'source_excludes'])
ChangeIdRegex = re.compile(r"^\s*[Cc]hange-Id:\s*(\S+)\s*$")

RepoInfo = namedtuple('RepoInfo', ['repo_path', 'json_path', 'repo'])
CommitInfo = namedtuple('CommitInfo', ['start_commit', 'end_commit', 'source_commit', 'single_commit', 'original_branch', 'original_head', 'append_sha', 'squash', 'todo_commits', 'complete_commits'])
CherryPickInfo = namedtuple('CherryPickInfo', ['f2f_cherry_pick_src', 'f2f_src_branch', 'f2f_dest_branch', 'num_cherry_picks', 'cherry_pick_operations', 'cherry_pick_operations_template'])

class F2fCherryPickCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'f2f-cherry-pick'
        metadata['help-text'] = arguments.F2F_CHERRY_PICK_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'commit-ish',
                     'positional' : True,
                     'position' : 0,
                     'required': False,
                     'description' : arguments.F2F_CHERRY_PICK_COMMIT_ISH_DESCRIPTION,
                     'help-text' : arguments.F2F_CHERRY_PICK_COMMIT_ISH_HELP})
        args.append({'name': 'template',
                     'positional': False,
                     'required': False,
                     'action': 'store',
                     'nargs': 1,
                     'help-text': arguments.F2F_CHERRY_PICK_TEMPLATE_HELP})
        args.append({'name': 'folders',
                     'positional': False,
                     'required': False,
                     'action': 'store',
                     'nargs': '+',
                     'help-text': arguments.F2F_CHERRY_PICK_FOLDERS_HELP})
        args.append({'name': 'continue',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.F2F_CHERRY_PICK_CONTINUE_HELP})
        args.append({'name': 'abort',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.F2F_CHERRY_PICK_ABORT_HELP})
        args.append({'name': 'list-templates',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.F2F_CHERRY_PICK_LIST_TEMPLATES_HELP})
        args.append({'name': 'append-sha',
                     'short-name': 'x',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.F2F_CHERRY_PICK_APPEND_COMMIT_HELP})
        args.append({'name': 'squash',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.F2F_CHERRY_PICK_SQUASH_HELP})
        args.append(ColorArgument)
        return metadata

    def run_command(self, args, config):
        init_color_console(args.color)
        if args.list_templates:
            _list_templates()
            return
        continue_operation = vars(args)['continue']
        commit_ish = vars(args)['commit-ish']
        json_path = os.path.join('.git', 'f2f_cherry_pick_status.json')
        if commit_ish is None and not continue_operation and not args.abort:
            raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_COMMIT_REQUIRED)
        if not continue_operation and not args.abort:
            (repo_info, cherry_pick_operations) = _start_new_cherry_pick(args, json_path)
            (commit_info, cherry_pick_operations) = _prep_new_cherry_pick(args, repo_info.repo, commit_ish, config, cherry_pick_operations)
            f2f_src_branch = None
            f2f_dest_branch = None
            f2f_cherry_pick_src = None
            num_cherry_picks = None
            cherry_pick_operations_template = None
            cherry_pick_info = CherryPickInfo(f2f_cherry_pick_src, f2f_src_branch, f2f_dest_branch, num_cherry_picks, cherry_pick_operations, cherry_pick_operations_template)
        else:
            try:
                (repo_info, commit_info, cherry_pick_info) = _resume_cherry_pick(args, json_path) # Continuing or aborting
            except EdkrepoAbortCherryPickException:
                return

        _complete_cherry_pick(args, continue_operation, repo_info, commit_info, cherry_pick_info)

def _start_new_cherry_pick(args, json_path):
    (cherry_pick_operations, repo_path) = _parse_arguments(args)
    json_path = os.path.join(repo_path, json_path)
    if os.path.isfile(json_path):
        raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_IN_PROGRESS)
    # Initialize GitPython
    repo = Repo(repo_path)
    repo_info = RepoInfo(repo_path, json_path, repo)
    return (repo_info, cherry_pick_operations)

def _prep_new_cherry_pick(args, repo, commit_ish, config, cherry_pick_operations):
    # Check for staged, unstaged, and untracked files

    # Require everything be totally clean before attempting Folder to Folder voodoo
    if repo.is_dirty(untracked_files=True):
        raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_DIRTY_WORKSPACE)
    original_head = str(repo.commit('HEAD'))
    # Make sure the repo is not in detached HEAD mode
    try:
        original_branch = repo.active_branch.name
    except:
        raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_BRANCH_REQUIRED)
    # Make sure sparse checkout is disabled
    try:
        workspace_path = get_workspace_path()
    except EdkrepoWorkspaceInvalidException:
        workspace_path = None
    if workspace_path is not None:
        manifest = get_workspace_manifest()
        sparse_enabled = sparse_checkout_enabled(workspace_path, manifest.get_repo_sources(manifest.general_config.current_combo))
        if sparse_enabled:
            raise EdkrepoWorkspaceInvalidException(humble.F2F_CHERRY_PICK_NO_SPARSE)
    single_commit = True
    append_sha = args.append_sha
    squash = args.squash
    source_commit = None
    todo_commits = []
    complete_commits = []
    try:
        repo.rev_parse(commit_ish)
        source_commit = str(repo.commit(commit_ish))
        todo_commits = [source_commit]
    except:
        if len(split_commit_range(commit_ish)) <= 1:
            raise EdkrepoInvalidParametersException(COMMIT_NOT_FOUND.format(commit_ish))
        todo_commits = repo.git.rev_list(commit_ish).split()
        # git-rev-list returns commits in reverse chronological order
        todo_commits.reverse()
        single_commit = False
        append_sha = False
    start_commit = None
    end_commit = None
    if not single_commit:
        # Determine the start and end commit for the upcoming squash
        (start_commit, end_commit) = get_start_and_end_commit(commit_ish, repo)
        # Note: source_commit will be replaced with the squashed commit later
        source_commit = end_commit
    # Determine what needs to be done to complete the cherry pick
    cherry_pick_operations = _init_f2f_cherry_pick_operations(cherry_pick_operations, repo,
                                                            original_head, original_head, config)
    commit_info = CommitInfo(start_commit, end_commit, source_commit, single_commit, original_branch, original_head, append_sha, squash, todo_commits, complete_commits)
    return commit_info, cherry_pick_operations

def _resume_cherry_pick(args, json_path):
    # Get path to Git repository
    repo_path = get_git_repo_root()
    json_path = os.path.join(repo_path, json_path)
    # Initialize GitPython
    repo = Repo(repo_path)
    if not os.path.isfile(json_path):
        if args.abort:
            raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_IN_PROGRESS_ABORT)
        else:
            raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_IN_PROGRESS_CONTINUE)
    (original_branch, original_head, single_commit,
     cherry_pick_operations, f2f_src_branch, f2f_dest_branch,
     f2f_cherry_pick_src, num_cherry_picks, source_commit, append_sha,
     cherry_pick_operations_template, complete_commits, todo_commits, squash) = _restore_f2f_cherry_pick_state(repo_path)
    if args.abort:
        _abort_cherry_pick(repo, json_path, original_branch, original_head, f2f_src_branch, f2f_dest_branch, f2f_cherry_pick_src)
        raise EdkrepoAbortCherryPickException(humble.F2F_CHERRY_PICK_ABORT_DETECTED)
    else:
        start_commit = None
        end_commit = None
        repo_info = RepoInfo(repo_path, json_path, repo)
        commit_info = CommitInfo(start_commit, end_commit, source_commit, single_commit, original_branch, original_head, append_sha, squash, todo_commits, complete_commits)
        cherry_pick_info = CherryPickInfo(f2f_cherry_pick_src, f2f_src_branch, f2f_dest_branch, num_cherry_picks, cherry_pick_operations, cherry_pick_operations_template)
        return (repo_info, commit_info, cherry_pick_info)

def _abort_cherry_pick(repo, json_path, original_branch, original_head, f2f_src_branch, f2f_dest_branch, f2f_cherry_pick_src):
    repo.git.reset('--hard')
    repo.heads[original_branch].checkout()
    repo.git.reset('--hard', original_head)
    os.remove(json_path)
    if f2f_src_branch in repo.heads:
        repo.git.branch('-D', f2f_src_branch) # Note: Head.delete() in GitPython is broken
    if f2f_dest_branch in repo.heads:
        repo.git.branch('-D', f2f_dest_branch)
    if f2f_cherry_pick_src in repo.heads:
        repo.git.branch('-D', f2f_cherry_pick_src)
    return

def _complete_cherry_pick(args, continue_operation, repo_info, commit_info, cherry_pick_info):
    # Unpack namedtuples

    (repo_path, json_path, repo) = (repo_info.repo_path, repo_info.json_path, repo_info.repo)
    (start_commit, end_commit, source_commit, single_commit, original_branch, original_head, append_sha, squash, todo_commits, complete_commits) = \
        (commit_info.start_commit, commit_info.end_commit, commit_info.source_commit, commit_info.single_commit,
         commit_info.original_branch, commit_info.original_head, commit_info.append_sha, commit_info.squash, commit_info.todo_commits, commit_info.complete_commits)
    (f2f_cherry_pick_src, f2f_src_branch, f2f_dest_branch, num_cherry_picks, cherry_pick_operations, cherry_pick_operations_template) = \
        (cherry_pick_info.f2f_cherry_pick_src, cherry_pick_info.f2f_src_branch, cherry_pick_info.f2f_dest_branch,
         cherry_pick_info.num_cherry_picks, cherry_pick_info.cherry_pick_operations, cherry_pick_info.cherry_pick_operations_template)

    merge_conflict = False
    try:
        #
        # Step 1 - If a range of commits was provided, squash them
        #
        if not single_commit and not continue_operation and squash:
            if args.template is not None:
                projects = args.template[0].split(':')
                commit_message = humble.F2F_CHERRY_PICK_TEMPLATE_COMMIT_MESSAGE.format(projects[0], projects[1])
            else:
                commit_message = humble.F2F_CHERRY_PICK_NON_TEMPLATE_COMMIT_MESSAGE
                for operation in cherry_pick_operations:
                    for folder in operation:
                        commit_message += '{} -> {}\n'.format(folder.source, folder.destination)
                commit_message += humble.F2F_CHERRY_PICK_NON_TEMPLATE_COMMIT_MESSAGE_LINE2
            commit_message += get_squash_commit_message_list(cherry_pick_operations, repo, start_commit, end_commit)
            commit_message += '\n'
            f2f_cherry_pick_src = get_unique_branch_name('f2f-cherry-pick-src', repo)
            squash_commits(start_commit, end_commit, f2f_cherry_pick_src, commit_message, repo)
            source_commit = str(repo.commit(f2f_cherry_pick_src))
            todo_commits = [source_commit]
        if not cherry_pick_operations_template:
            cherry_pick_operations_template = cherry_pick_operations
        if continue_operation:
            print(humble.F2F_CHERRY_PICK_NUM_COMMITS_CONTINUE.format(len(todo_commits)))
        else:
            print(humble.F2F_CHERRY_PICK_NUM_COMMITS_NEW.format(len(todo_commits)))
        while todo_commits:
            source_commit = todo_commits[0]
            print(humble.F2F_CHERRY_PICK_ESTIMATE_REMAINING_OPERATIONS.format(len(todo_commits), len(todo_commits) * len(cherry_pick_operations_template)))
            print(humble.F2F_CHERRY_PICK_CURRENT_COMMIT.format(source_commit))
            if not continue_operation:
                # Now that the change delta is known, we can optimize the cherry pick operation
                cherry_pick_operations = _optimize_f2f_cherry_pick_operations(cherry_pick_operations_template, repo, source_commit)
                num_cherry_picks = len(cherry_pick_operations)
                f2f_src_branch = get_unique_branch_name('f2f-src', repo)
                f2f_dest_branch = get_unique_branch_name('f2f-dest', repo)

                # Inform the user w.r.t. what is about to happen
                if num_cherry_picks == 1:
                    print(humble.F2F_CHERRY_PICK_NUM_CHERRY_PICKS_SINGULAR.format(len(cherry_pick_operations)))
                else:
                    print(humble.F2F_CHERRY_PICK_NUM_CHERRY_PICKS_PLURAL.format(len(cherry_pick_operations)))
                for index in range(len(cherry_pick_operations)):
                    print(humble.F2F_CHERRY_PICK_CHERRY_PICK_NUM.format(index + 1))
                    for folder in cherry_pick_operations[index]:
                        print("{} -> {} -> {}".format(folder.source, folder.intermediate, folder.destination))
                        if len(folder.source_excludes) > 0:
                            print(humble.F2F_CHERRY_PICK_CHERRY_PICK_EXCLUDE_LIST.format(repr(folder.source_excludes)))
                    print()
            if continue_operation:
                #
                # Finish up the current cherry pick operation now that merge conflicts are resolved
                #
                git_automation_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'git_automation')
                if not os.path.isfile(os.path.join(git_automation_dir, "commit_msg.py")):
                    git_automation_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
                    git_automation_dir = os.path.join(git_automation_dir, 'edkrepo', 'git_automation')
                    if not os.path.isfile(os.path.join(git_automation_dir, "commit_msg.py")):
                        raise EdkrepoNotFoundException(humble.F2F_CHERRY_PICK_COMMIT_MSG_PY_NOT_FOUND)
                if sys.platform == "win32":
                    os.environ['GIT_EDITOR'] = 'py "{}"'.format(os.path.join(git_automation_dir, "commit_msg.py"))
                else:
                    os.environ['GIT_EDITOR'] = os.path.join(git_automation_dir, "commit_msg.py")
                os.environ['COMMIT_MESSAGE_NO_EDIT'] = '1'
                try:
                    repo.git.commit('--allow-empty')
                finally:
                    del os.environ['GIT_EDITOR']
                    del os.environ['COMMIT_MESSAGE_NO_EDIT']
                try:
                    _post_cherry_pick_processing(repo, cherry_pick_operations.pop(0), f2f_dest_branch, single_commit,
                                                    original_branch, source_commit, append_sha)
                    os.remove(json_path)
                finally:
                    repo.heads[original_branch].checkout()
                    repo.git.reset('--hard')
                    if f2f_src_branch in repo.heads:
                        repo.git.branch('-D', f2f_src_branch)
                    if f2f_dest_branch in repo.heads:
                        repo.git.branch('-D', f2f_dest_branch)
                continue_operation = False
            for index in range(len(cherry_pick_operations)):
                f2f_src_branch = get_unique_branch_name('f2f-src', repo)
                f2f_dest_branch = get_unique_branch_name('f2f-dest', repo)
                try:
                    cherry_pick_operation = cherry_pick_operations[index]
                    #
                    # Transform the source commit into a cherry-pick'able commit
                    #
                    repo.create_head(f2f_src_branch, source_commit)
                    repo.heads[f2f_src_branch].checkout()
                    repo.git.reset('--hard')
                    _prepare_source_branch(cherry_pick_operation, f2f_src_branch, repo)
                    if len(repo.commit(f2f_src_branch).stats.files) <= 0:
                        # After the filter-branch, there is nothing left to cherry pick, so move on to the next cherry pick
                        repo.heads[original_branch].checkout()
                        repo.git.reset('--hard')
                        num_cherry_picks -= 1
                        continue
                    #
                    # Transform the destination to receive the cherry pick
                    #
                    repo.heads[original_branch].checkout()
                    repo.git.reset('--hard')
                    repo.create_head(f2f_dest_branch, str(repo.commit('HEAD')))
                    repo.heads[f2f_dest_branch].checkout()
                    _prepare_destination_branch(cherry_pick_operation, f2f_dest_branch, repo)
                    #
                    # Step 6 - Do the cherry pick
                    #
                    merge_conflict = _perform_cherry_pick(str(repo.commit(f2f_src_branch)), repo, args.verbose)
                    if merge_conflict:
                        _save_f2f_cherry_pick_state(
                            repo_path, original_branch, original_head,
                            single_commit, cherry_pick_operations[index:], f2f_src_branch,
                            f2f_dest_branch, f2f_cherry_pick_src, num_cherry_picks, source_commit, append_sha,
                            todo_commits, complete_commits, cherry_pick_operations_template, squash)
                        return
                    #
                    # Cherry Pick the results to the target branch
                    #
                    _post_cherry_pick_processing(repo, cherry_pick_operation, f2f_dest_branch, single_commit,
                                                    original_branch, source_commit, append_sha)
                finally:
                    if not merge_conflict:
                        repo.heads[original_branch].checkout()
                        repo.git.reset('--hard')
                        if f2f_src_branch in repo.heads:
                            repo.git.branch('-D', f2f_src_branch)
                        if f2f_dest_branch in repo.heads:
                            repo.git.branch('-D', f2f_dest_branch)
            # If there are multiple cherry-pick operations, we need to squash the results
            if num_cherry_picks > 1:
                start_commit = str(repo.commit('HEAD~{}'.format(num_cherry_picks)))
                end_commit = str(repo.commit('HEAD'))
                commit_message = repo.commit('HEAD').message
                print(commit_message)
                f2f_cherry_pick_squash = get_unique_branch_name('f2f-cherry-pick-squash', repo)
                try:
                    squash_commits(start_commit, end_commit, f2f_cherry_pick_squash, commit_message, repo, False)
                    repo.heads[original_branch].checkout()
                    repo.git.reset('--hard', '{}'.format(start_commit))
                    repo.git.cherry_pick(str(repo.commit(f2f_cherry_pick_squash)))
                finally:
                    if f2f_cherry_pick_squash in repo.heads:
                        repo.git.branch('-D', f2f_cherry_pick_squash)
            # Current source_commit is successful, let user know and move the commit to the completed list
            print()
            print(humble.F2F_CHERRY_PICK_SUCCESSFUL)
            todo_commits.remove(source_commit)
            complete_commits.append(source_commit)
    finally:
        if not merge_conflict:
            repo.heads[original_branch].checkout()
            repo.git.reset('--hard')  # Removed reference to original_head so we're just resetting on the original branch...
            if f2f_cherry_pick_src in repo.heads:
                repo.git.branch('-D', f2f_cherry_pick_src)

def _post_cherry_pick_processing(repo, cherry_pick_operation, f2f_dest_branch, single_commit,
                                 original_branch, source_commit, append_sha):
    if single_commit:
        strip_commit_message(repo.commit(f2f_dest_branch), repo, source_commit, append_sha)
    #
    # Transform the destination back to the original name
    #
    _finalize_destination_branch(cherry_pick_operation, f2f_dest_branch, repo)
    #
    # Step 8 - Cherry-pick to the target branch
    #
    repo.heads[original_branch].checkout()
    repo.git.cherry_pick('--allow-empty', str(repo.commit(f2f_dest_branch)))

def inside_directory(parent_path, child_path):
    parent_path = parent_path.replace('/', os.sep)
    child_path = child_path.replace('/', os.sep)
    parent_path = os.path.join(parent_path, '')
    return os.path.commonprefix([parent_path, child_path]) == parent_path

def get_common_folder_name(folder1, folder2, config):
    ignored_folders = config['cfg_file'].f2f_cp_ignored_folders
    match = SequenceMatcher(None, folder1, folder2).find_longest_match(0, len(folder1), 0, len(folder2))
    if match.size > 3:
        for folder in ignored_folders:
            replace_regex = re.compile(re.escape(folder), re.IGNORECASE)
            folder1 = replace_regex.sub('', folder1)
            folder2 = replace_regex.sub('', folder2)
            match = SequenceMatcher(None, folder1, folder2).find_longest_match(0, len(folder1), 0, len(folder2))
            if match.size <= 3:
                break
    if match.size > 0:
        return folder1[match.a:match.a + match.size]
    else:
        return ''

def get_unique_branch_name(branch_name_prefix, repo):
    branch_names = [x.name for x in repo.heads]
    if branch_name_prefix not in branch_names:
        return branch_name_prefix
    index = 1
    while True:
        branch_name = "{}-{}".format(branch_name_prefix, index)
        if branch_name not in branch_names:
            return branch_name

def cherry_pick_operations_to_include_folder_list(cherry_pick_operations):
    include_folder_list = []
    for cherry_pick_operation in cherry_pick_operations:
        include_folder_list.extend([folder.source for folder in cherry_pick_operation])
    return include_folder_list

def get_commit_list(include_folder_list, repo, start_commit, end_commit):
    commit_list = repo.git.rev_list('{}..{}'.format(start_commit, end_commit)).split()
    include_commit_list = []
    for commit in commit_list:
        changed_files = list(repo.commit(commit).stats.files)
        for folder in include_folder_list:
            if _path_in_changed_files(folder, changed_files):
                include_commit_list.append(commit)
                break
    return include_commit_list

def get_squash_commit_message_list(cherry_pick_operations, repo, start_commit, end_commit):
    include_folder_list = cherry_pick_operations_to_include_folder_list(cherry_pick_operations)
    return commit_list_to_message(get_commit_list(include_folder_list, repo, start_commit, end_commit), True, repo)

def strip_commit_message(commit, repo, source_commit=None, append_sha=False):
    commit = repo.commit(commit)
    initial_lines = commit.message.split('\n')
    lines = []
    for line in initial_lines:
        stripped = line.strip().lower()
        if stripped.startswith('original-chg-id:'):
            continue
        if stripped.startswith('change-id:'):
            m = ChangeIdRegex.match(line)
            if m:
                lines.append("Original-chg-id: {}".format(m.group(1)))
            continue
        if stripped.startswith('reviewed-on:'):
            continue
        if stripped.startswith('tested-by:'):
            continue
        if stripped.startswith('reviewed-by:'):
            continue
        lines.append(line.strip())
    if append_sha and source_commit is not None:
        lines.append('(cherry picked from commit {})'.format(source_commit))
    commit_message = '\n'.join(lines)
    commit_message += '\n'
    git_automation_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'git_automation')
    if not os.path.isfile(os.path.join(git_automation_dir, "commit_msg.py")):
        git_automation_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        git_automation_dir = os.path.join(git_automation_dir, 'edkrepo', 'git_automation')
        if not os.path.isfile(os.path.join(git_automation_dir, "commit_msg.py")):
            raise EdkrepoNotFoundException(humble.F2F_CHERRY_PICK_COMMIT_MSG_PY_NOT_FOUND)
    if sys.platform == "win32":
        os.environ['GIT_EDITOR'] = 'py "{}"'.format(os.path.join(git_automation_dir, "commit_msg.py"))
    else:
        os.environ['GIT_EDITOR'] = os.path.join(git_automation_dir, "commit_msg.py")
    os.environ['COMMIT_MESSAGE'] = commit_message
    check_call(['git', 'commit', '--amend'])
    del os.environ['GIT_EDITOR']
    del os.environ['COMMIT_MESSAGE']

def _perform_cherry_pick(commit, repo, verbose):
    merge_conflict = False
    p = Popen(['git', 'cherry-pick', commit], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    stdout = p.communicate()[0]
    if not isinstance(stdout, str):
        stdout = stdout.decode("utf-8")
    if p.returncode != 0:
        if stdout.find('after resolving the conflicts') != -1:
            merge_conflict = True
            stdout = stdout.replace("hint: and commit the result with 'git commit'",'')
            sys.stdout.write(stdout)
            print()
            print(humble.F2F_CHERRY_PICK_MERGE_CONFLICT_LINE1)
            print(humble.F2F_CHERRY_PICK_MERGE_CONFLICT_LINE2)
            print()
            print(humble.F2F_CHERRY_PICK_MERGE_CONFLICT_LINE3)
            print(humble.F2F_CHERRY_PICK_MERGE_CONFLICT_LINE4)
        else:
            sys.stdout.write(stdout)
            raise EdkrepoGitException(humble.F2F_CHERRY_PICK_GIT_FAILURE.format(p.returncode))
    elif verbose:
        sys.stdout.write(stdout)
    return merge_conflict

def _prepare_source_branch(cherry_pick_operation, branch_name, repo):
    #
    # Step 2 - Remove everything except the source directories
    #
    remove_all_directories_except_included([folder.source for folder in cherry_pick_operation], 'HEAD~2..HEAD', repo)
    #
    # Step 3 - Remove all excluded directories
    #
    for folder in cherry_pick_operation:
        for exclude in folder.source_excludes:
            remove_single_directory(exclude, 'HEAD~2..HEAD', repo)
    #
    # Step 4 - Rename from source directory to intermediate directory
    #
    rename_dictionary = {}
    for folder in cherry_pick_operation:
        rename_dictionary[folder.source] = folder.intermediate
    rename_directories(rename_dictionary, 'HEAD~2..HEAD', repo)

def _prepare_destination_branch(cherry_pick_operation, branch_name, repo):
    #
    # Step 5 - Rename from destination directory to intermediate directory
    #
    rename_dictionary = {}
    for folder in cherry_pick_operation:
        rename_dictionary[folder.destination] = folder.intermediate
    rename_directories(rename_dictionary, 'HEAD~2..HEAD', repo)

def _finalize_destination_branch(cherry_pick_operation, branch_name, repo):
    #
    # Step 7 - Rename from intermediate directory to destination directory
    #
    rename_dictionary = {}
    for folder in cherry_pick_operation:
        rename_dictionary[folder.intermediate] = folder.destination
    rename_directories(rename_dictionary, 'HEAD~2..HEAD', repo)

def remove_all_directories_except_included(include_list, commit_range, repo, prune_empty=False):
    for include in include_list:
        if include.find(' ') != -1:
            raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_SPACES)
    command = "git filter-branch --index-filter 'git rm --cached -qr --ignore-unmatch -- . && git reset -q $GIT_COMMIT -- {}' {} -- {}"
    if prune_empty:
        prune_empty_str = '--prune-empty'
    else:
        prune_empty_str = ''
    command = command.format(' '.join(include_list), prune_empty_str, commit_range)
    run_filter_branch(command, repo)

def remove_single_directory(directory, commit_range, repo, prune_empty=False):
    command = "git filter-branch --index-filter 'git rm -fr --cached --ignore-unmatch {}' {} -- {}"
    if prune_empty:
        prune_empty_str = '--prune-empty'
    else:
        prune_empty_str = ''
    command = command.format(directory, prune_empty_str, commit_range)
    run_filter_branch(command, repo)

def rename_directories(rename_dictionary, commit_range, repo):
    sed_list = []
    for source in rename_dictionary:
        sed_list.append("sed \"s|\\t{}\\(.*\\)|\\t{}\\1|\"".format(source, rename_dictionary[source]))
    suffix = "| GIT_INDEX_FILE=$GIT_INDEX_FILE.new git update-index --index-info && mv \"$GIT_INDEX_FILE.new\" \"$GIT_INDEX_FILE\"' -- {}"
    command = "git filter-branch --index-filter 'git ls-files -s | {{}} {}".format(suffix)
    command = command.format(' | '.join(sed_list), commit_range)
    run_filter_branch(command, repo)

def run_filter_branch(command, repo):
    refs = repo.git.show_ref().split()
    for ref in refs:
        if ref.startswith('refs/original/'):
            repo.git.update_ref('-d', ref)
            break
    repo_path = repo.working_tree_dir
    rewrite_path = os.path.join(repo_path, ".git-rewrite")
    if os.path.isdir(rewrite_path):
        for x in range(10):
            time.sleep(1.0)
            if os.path.isdir(rewrite_path):
                break
        if os.path.isdir(rewrite_path):
            os.rmdir(rewrite_path)
    reset_environ = False
    try:
        if 'FILTER_BRANCH_SQUELCH_WARNING' not in os.environ:
            os.environ['FILTER_BRANCH_SQUELCH_WARNING'] = '1'
            reset_environ = True
        if sys.platform == "win32":
            bash_path = find_bash_windows()
            if bash_path is None:
                raise EdkrepoNotFoundException(humble.F2F_CHERRY_PICK_BASH_NOT_FOUND)
            command = command.replace('"', '""')
            check_call('"{}" -c "{}"'.format(bash_path, command), shell=True)
        else:
            check_call(command, shell=True)
    finally:
        if reset_environ:
            del os.environ['FILTER_BRANCH_SQUELCH_WARNING']
    refs = repo.git.show_ref().split()
    for ref in refs:
        if ref.startswith('refs/original/'):
            repo.git.update_ref('-d', ref)
            break

_bash_path = None
def find_bash_windows():
    global _bash_path
    if _bash_path is not None:
        return _bash_path
    git_path = get_full_path('git.exe')
    if git_path is not None:
        bash_path = os.path.join(os.path.dirname(os.path.dirname(git_path)), 'bin', 'bash.exe')
        if os.path.isfile(bash_path):
            _bash_path = bash_path
            return _bash_path
        bash_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(git_path))), 'bin', 'bash.exe')
        if os.path.isfile(bash_path):
            _bash_path = bash_path
            return _bash_path
    return None

def split_path(path):
    paths = []
    last_head = None
    (head, tail) = os.path.split(path)
    while last_head != head:
        paths.append(tail)
        last_head = head
        (head, tail) = os.path.split(head)
    paths.reverse()
    return (head, paths)

_git_ls_tree_cache = {}
def git_ls_tree(tree_ish, repo):
    global _git_ls_tree_cache
    # It takes git a considerable period of time compute ls-tree
    # This code flow uses ls-tree from the same tree-ish several times,
    # So caching the results provided a considerable performance benefit
    if tree_ish in _git_ls_tree_cache:
        return _git_ls_tree_cache[tree_ish]
    _git_ls_tree_cache[tree_ish] = repo.git.ls_tree('--name-only', '-r', tree_ish).split('\n')
    return _git_ls_tree_cache[tree_ish]

def git_is_file(path, tree_ish, repo, case_insensitive=False):
    if isinstance(tree_ish, list):
        for item in tree_ish:
            if git_is_file(path, item, repo, case_insensitive):
                return True
        return False
    files = git_ls_tree(tree_ish, repo)
    for file_path in files:
        if case_insensitive:
            if case_insensitive_equal(path, file_path):
                return True
        else:
            if path == file_path:
                return True
    return False

def git_is_dir(path, tree_ish, repo, case_insensitive=False):
    if isinstance(tree_ish, list):
        for item in tree_ish:
            if git_is_dir(path, item, repo, case_insensitive):
                return True
        return False
    files = git_ls_tree(tree_ish, repo)
    for file_path in files:
        file_path = os.path.dirname(file_path)
        while os.path.dirname(file_path) != file_path:
            if case_insensitive:
                if case_insensitive_equal(path, file_path):
                    return True
            else:
                if path == file_path:
                    return True
            file_path = os.path.dirname(file_path)
    return False

def git_path_exists(path, tree_ish, repo, case_insensitive=False):
    if git_is_file(path, tree_ish, repo, case_insensitive):
        return True
    if git_is_dir(path, tree_ish, repo, case_insensitive):
        return True
    return False

def _save_f2f_cherry_pick_state(repo_path, original_branch, original_head, single_commit, remaining_cp_operations,
                                f2f_src_branch, f2f_dest_branch, f2f_cp_src_branch, num_cherry_picks, source_commit,
                                append_sha, todo_commits, complete_commits, cp_operations_template, squash):
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        raise EdkrepoWorkspaceInvalidException(NOT_GIT_REPO)
    json_path = os.path.join(repo_path, '.git', 'f2f_cherry_pick_status.json')
    if os.path.isfile(json_path):
        os.remove(json_path)
    data = {}
    data['original_branch'] = original_branch
    data['original_head'] = original_head
    data['single_commit'] = single_commit
    remaining_cherry_pick_operations = []
    # Convert the namedtuples in to dictionaries so they can be stored
    for operation in remaining_cp_operations:
        remaining_operation = []
        for folder in operation:
            remaining_operation.append(folder._asdict())
        remaining_cherry_pick_operations.append(remaining_operation)

    cherry_pick_operations_template = []
    for cp_operation in cp_operations_template:
        op = []
        for folder in cp_operation:
            op.append(folder._asdict())
        cherry_pick_operations_template.append(op)

    data['in_progress_commit'] = {}
    data['in_progress_commit']['source_commit'] = source_commit
    data['in_progress_commit']['num_cherry_picks'] = num_cherry_picks
    data['in_progress_commit']['remaining_cherry_pick_operations'] = remaining_cherry_pick_operations

    data['f2f_src_branch'] = f2f_src_branch
    data['f2f_dest_branch'] = f2f_dest_branch
    data['f2f_cherry_pick_src'] = f2f_cp_src_branch

    data['append_sha'] = append_sha
    data['squash'] = squash
    data['all_cherry_pick_operations'] = cherry_pick_operations_template
    data['complete_commits'] = complete_commits
    data['todo_commits'] = todo_commits

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)

def _restore_f2f_cherry_pick_state(repo_path):
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        raise EdkrepoWorkspaceInvalidException(NOT_GIT_REPO)
    json_path = os.path.join(repo_path, '.git', 'f2f_cherry_pick_status.json')
    with open(json_path, 'r') as f:
        data = json.load(f)
    # Convert the dictionaries to namedtuples
    remaining_cp_operations = []
    for operation in data['in_progress_commit']['remaining_cherry_pick_operations']:
        remaining_operation = []
        for folder in operation:
            remaining_operation.append(FolderCherryPick(**folder))
        remaining_cp_operations.append(remaining_operation)
    cp_operations_template = []
    for operation in data['all_cherry_pick_operations']:
        remaining_operation = []
        for folder in operation:
            remaining_operation.append(FolderCherryPick(**folder))
        cp_operations_template.append(remaining_operation)
    return (data['original_branch'], data['original_head'],
            data['single_commit'], remaining_cp_operations,
            data['f2f_src_branch'], data['f2f_dest_branch'],
            data['f2f_cherry_pick_src'], data['in_progress_commit']['num_cherry_picks'],
            data['in_progress_commit']['source_commit'], data['append_sha'],
            cp_operations_template, data['complete_commits'], data['todo_commits'], data['squash'])

def _init_f2f_cherry_pick_operations(cherry_pick_operations, repo, src_commit, dest_commit, config):
    repo_path = repo.working_tree_dir
    # Normalize all the paths
    used_common_folder_paths = []
    temp_cherry_pick_operations = []
    for operation in cherry_pick_operations:
        temp_folders = []
        for folder in operation:
            # Normalize the path strings for the source, destination, and excludes
            source = os.path.normpath(os.path.join(repo_path, folder.source))
            destination = os.path.normpath(os.path.join(repo_path, folder.destination))
            if not inside_directory(repo_path, source):
                raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NOT_IN_GIT_REPO.format(source))
            if not inside_directory(repo_path, destination):
                raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NOT_IN_GIT_REPO.format(destination))
            source = os.path.relpath(source, repo_path).replace(os.sep, '/')
            destination = os.path.relpath(destination, repo_path).replace(os.sep, '/')
            if not git_path_exists(source, src_commit, repo):
                print(humble.F2F_CHERRY_PICK_PATH_NOT_EXIST.format(source, src_commit))
                continue
            if not git_path_exists(destination, dest_commit, repo):
                print(humble.F2F_CHERRY_PICK_PATH_NOT_EXIST.format(destination, dest_commit))
                continue
            source_excludes = []
            for exclude in folder.source_excludes:
                exclude = os.path.normpath(os.path.join(repo_path, exclude))
                if not inside_directory(repo_path, exclude):
                    raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NOT_IN_GIT_REPO.format(exclude))
                exclude = os.path.relpath(exclude, repo_path).replace(os.sep, '/')
                if git_path_exists(exclude, src_commit, repo):
                    source_excludes.append(exclude)
            # Generate the intermediate folder path
            common_folder_name = _get_intermediate_folder_name(source, destination, used_common_folder_paths,
                                                               repo, src_commit, dest_commit, config)
            temp_folders.append(FolderCherryPick(source, destination, common_folder_name, source_excludes))
        temp_cherry_pick_operations.append(temp_folders)
    cherry_pick_operations = temp_cherry_pick_operations
    # If one of the folders is inside another folder,
    # the single cherry pick operation must be broken up in to multiple cherry pick operations
    temp_cherry_pick_operations = []
    removed_folders = []
    for operation in cherry_pick_operations:
        temp_folders = []
        for folder in operation:
            for child in operation:
                if inside_directory(folder.source, child.source):
                    if child not in removed_folders:
                        removed_folders.append(child)
                    append_to_excludes = True
                    for exclude in folder.source_excludes:
                        if inside_directory(exclude, child.source):
                            append_to_excludes = False
                            break
                        if exclude == child.source:
                            append_to_excludes = False
                            break
                    if append_to_excludes:
                        folder.source_excludes.append(child.source)
        for folder in operation:
            if folder not in removed_folders:
                temp_folders.append(folder)
        temp_cherry_pick_operations.append(temp_folders)
    while len(removed_folders) > 0:
        temp_folders = []
        temp_removed_folders = []
        for folder in removed_folders:
            for child in removed_folders:
                if inside_directory(folder.source, child.source):
                    if child not in temp_removed_folders:
                        temp_removed_folders.append(child)
                    if child.source not in folder.source_excludes:
                        folder.source_excludes.append(child.source)
        for folder in removed_folders:
            if folder not in temp_removed_folders:
                append_to_temp_folders = True
                for exclude in temp_removed_folders:
                    if inside_directory(exclude.source, folder.source):
                        append_to_temp_folders = False
                        break
                if append_to_temp_folders:
                    temp_folders.append(folder)
        temp_cherry_pick_operations.append(temp_folders)
        removed_folders = temp_removed_folders
    cherry_pick_operations = temp_cherry_pick_operations
    return cherry_pick_operations

def _get_intermediate_folder_name(source, destination, used_common_folder_paths, repo, src_commit, dest_commit, config):
    source_split_path = split_path(source)[1]
    destination_split_path = split_path(destination)[1]
    # Is this a top-level directory?
    if len(source_split_path) == 1 and len(destination_split_path) == 1:
        common_folder_path = get_common_folder_name(source, destination, config)
        # If a folder named with the longest common substring already exists, just use the destination folder name
        if len(common_folder_path) < 3:
            common_folder_path = destination
        elif _check_for_name_collision(common_folder_path, repo, src_commit, dest_commit) or \
           common_folder_path in used_common_folder_paths:
            common_folder_path = destination
    else: # It is a sub-directory
        common_split_path = []
        # Do the top-level directory names match?
        if source_split_path[0] == destination_split_path[0]:
            common_split_path.append(destination_split_path[0])
        else:
            # If not, try to convert the top-level name to a common name
            top_level = get_common_folder_name(source_split_path[0], destination_split_path[0], config)
            if len(top_level) < 3:
                top_level = destination_split_path[0]
            elif _check_for_name_collision(top_level, repo, src_commit, dest_commit):
                top_level = destination_split_path[0]
            common_split_path.append(top_level)
        # Are the sub-directory names the same?
        if source_split_path[-1] == destination_split_path[-1]:
            # If yes, match the remaining path string with the destination path string
            common_split_path.extend(destination_split_path[1:])
        else:
            # If no, convert to the longest common substring
            subdir_name = get_common_folder_name(source_split_path[-1], destination_split_path[-1], config)
            if len(subdir_name) < 3:
                subdir_name = destination_split_path[-1]
            else:
                # check for collisions
                temp_split_path = []
                temp_split_path.append(common_split_path[0])
                temp_split_path.extend(destination_split_path[1:-1])
                temp_split_path.append(subdir_name)
                temp_path = '/'.join(temp_split_path)
                if _check_for_name_collision(temp_path, repo, src_commit, dest_commit):
                    subdir_name = destination_split_path[-1]
            # Make any components of the path in between the top-level and the final sub-directory
            # match the destination path's folder structure
            common_split_path.extend(destination_split_path[1:-1])
            common_split_path.append(subdir_name)
        # Combine the split path to create the final path
        common_folder_path = '/'.join(common_split_path)
        if common_folder_path in used_common_folder_paths:
            common_folder_path = destination
    used_common_folder_paths.append(common_folder_path)
    return common_folder_path

def _check_for_name_collision(path, repo, src_commit, dest_commit):
    if git_path_exists(path, src_commit, repo):
        return True
    if src_commit != dest_commit:
        if git_path_exists(path, dest_commit, repo):
            return True
    return False

def _optimize_f2f_cherry_pick_operations(cherry_pick_operations, repo, source_commit):
    changed_files = list(repo.commit(source_commit).stats.files)
    temp_cherry_pick_operations = []
    for operation in cherry_pick_operations:
        temp_folders = []
        for folder in operation:
            if _path_in_changed_files(folder.source, changed_files):
                temp_folders.append(folder)
        if len(temp_folders) > 0:
            temp_cherry_pick_operations.append(temp_folders)
    return temp_cherry_pick_operations

def _path_in_changed_files(path, changed_files):
    for file_path in changed_files:
        while os.path.dirname(file_path) != file_path:
            if path == file_path:
                return True
            file_path = os.path.dirname(file_path)
    return False

def _list_templates():
    manifest = get_workspace_manifest()
    f2f_templates = manifest.folder_to_folder_mappings
    for template in f2f_templates:
        print('{}Template {}<-->{}{}'.format(Fore.MAGENTA, template.project1, template.project2, Fore.RESET))
        for folder in template.folders:
            print("{}<-->{}".format(folder.project1_folder, folder.project2_folder))
            if len(folder.excludes) > 0:
                print("Excludes:")
                for exclude in folder.excludes:
                    print('\t{}'.format(exclude.path))
        print()

def _parse_arguments(args):
    cherry_pick_operations = []
    if args.template is not None and args.folders is not None:
        raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_TEMPLATE_AND_FOLDERS)
    if args.template is not None:
        # Load the manifest XML and find the matching F2F template definition
        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()
        f2f_templates = manifest.folder_to_folder_mappings
        projects = args.template[0].split(':')
        project1 = projects[0]
        project2 = projects[1]
        template = None
        swap_done = False
        while template is None:
            for f2f_template in f2f_templates:
                if case_insensitive_equal(project1, f2f_template.project1) and case_insensitive_equal(project2, f2f_template.project2):
                    template = f2f_template
                    break
            if template is None:
                # The user could want to do a F2F cherry pick in the opposite direction to the template definition
                if not swap_done:
                    project1 = projects[1]
                    project2 = projects[0]
                    swap_done = True
                else:
                    raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_TEMPLATE.format(args.template[0]))
        # Now that the template is found, get the path to the template defined git repository
        repo_path = None
        for manifest_repo in manifest.get_repo_sources(manifest.general_config.current_combo):
            if manifest_repo.remote_name == template.remote_name:
                repo_path = os.path.normpath(os.path.join(workspace_path, manifest_repo.root))
                break
        if repo_path is None:
            raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_REMOTE.format(template.remote_name))
        # Convert the template in to FolderCherryPick named tuples
        cherry_pick_operation = []
        for folder in template.folders:
            if swap_done:
                source_folder = folder.project2_folder
                destination_folder = folder.project1_folder
            else:
                source_folder = folder.project1_folder
                destination_folder = folder.project2_folder
            source_excludes = []
            for exclude in folder.excludes:
                if os.path.commonprefix([source_folder, exclude.path]) == source_folder:
                    source_excludes.append(exclude.path)
            cherry_pick_operation.append(FolderCherryPick(source_folder, destination_folder, source_folder, source_excludes))
        cherry_pick_operations.append(cherry_pick_operation)
    else:
        # Note: the --folders mode works without a manifest XML file.
        # It is possible for this command to work without an edkrepo created workspace
        if args.folders is None:
            raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_ARGUMENTS)
        # Get the path to the git repository
        repo_path = get_git_repo_root()
        # Convert the command line arguments in to FolderCherryPick named tuples
        cherry_pick_operation = []
        for folder_pair in args.folders:
            (source_folder, destination_folder) = folder_pair.split(':')
            source_excludes = []
            cherry_pick_operation.append(FolderCherryPick(source_folder, destination_folder, source_folder, source_excludes))
        cherry_pick_operations.append(cherry_pick_operation)
    # Check for spaces in the source and destination folder names
    for operation in cherry_pick_operations:
        for folder in operation:
            if folder.source.find(' ') != -1:
                raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_SPACES.format(folder.source))
            if folder.destination.find(' ') != -1:
                raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_SPACES.format(folder.destination))
            for exclude in folder.source_excludes:
                if exclude.find(' ') != -1:
                    raise EdkrepoInvalidParametersException(humble.F2F_CHERRY_PICK_NO_SPACES.format(exclude))
    # The working directory must be the repo root for the filter branches to work correctly
    os.chdir(repo_path)
    return (cherry_pick_operations, repo_path)
