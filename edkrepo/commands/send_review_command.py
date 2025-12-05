#!/usr/bin/env python3
#
## @file
# send_review_command.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
from datetime import datetime
import itertools
import json
import re
import subprocess
import webbrowser
from enum import Enum

from git import Repo
from colorama import Fore
from git.exc import GitCommandError

from edkrepo.commands.edkrepo_command import EdkrepoCommand, OverrideArgument
import edkrepo.commands.humble.send_review_humble as humble
import edkrepo.commands.arguments.send_review_args as arguments
import edkrepo.common.common_repo_functions as common_repo_functions
import edkrepo.common.edkrepo_exception as edkrepo_exception
import edkrepo.common.ui_functions as ui_functions
import edkrepo.config.config_factory as config_factory


class SendReviewCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'send-review'
        metadata['help-text'] = arguments.SEND_REVIEW_COMMAND_DESCRIPTION
        metadata['alias'] = 'sr'
        args = []
        metadata['arguments'] = args
        args.append({'name': 'repository',
                     'positional': True,
                     'required': False,
                     'description': arguments.REPO_DESCRIPTION,
                     'help-text': arguments.REPO_HELP})
        args.append({'name': 'noweb',
                     'short-name': 'n',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.NOWEB_HELP})
        args.append({'name': 'reviewers',
                     'positional': False,
                     'required': False,
                     'action': 'store',
                     'nargs': '+',
                     'help-text': arguments.REVIEWERS_HELP})
        args.append({'name': 'dry-run',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.DRY_RUN_HELP})
        args.append({'name': 'draft',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.DRAFT_HELP})
        args.append({'name': 'title',
                     'positional': False,
                     'required' : False,
                     'action' : 'store',
                     'nargs' : '+',
                     'help-text' : arguments.TITLE_HELP})
        args.append(OverrideArgument)
        return metadata

    def run_command(self, args, config):
        workspace_path = config_factory.get_workspace_path()
        manifest = config_factory.get_workspace_manifest()
        # Note: the repo object is accessed via ModifiedRepo.git
        repo = ModifiedRepo(manifest, workspace_path, args.repository)
        review_type = self.__get_review_type(manifest, repo)
        if review_type == Reviews.PR_FORK:
            raise edkrepo_exception.EdkrepoWarningException('humble.SEND_REVIEW_PR_FORK_NOT_IMPLEMENTED')

        # Get the path for the netrc file to pass to curl, if not found, raise an error message and an exception
        netrc_path = common_repo_functions.get_netrc_path()

        local_branch = repo.git.active_branch
        local_name = repo.git.heads[local_branch.name]
        target_branch = repo.manifest.branch

        if repo.git.heads[local_branch.name].tracking_branch():
            if str(local_name) == str(target_branch):
                if args.dry_run:
                    ui_functions.print_warning_msg(humble.SEND_REVIEW_ON_TARGET.format(target_branch), header=True)
                else:
                    raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_ON_TARGET.format(target_branch))

        warning = False
        target_remote = common_repo_functions.DEFAULT_REMOTE_NAME

        commit_count = int(repo.git.git.rev_list('--count', '{}/{}..HEAD'.format(target_remote, target_branch)))
        if commit_count > 1:
            if review_type == Reviews.PR_BRANCH or Reviews.PR_FORK:
                print()
                ui_functions.print_info_msg(humble.PR_MULTIPLE_COMMITS.format(commit_count=commit_count), header=False)
            if args.verbose:
                ui_functions.print_info_msg(repo.git.git.rev_list('{}/{}..HEAD'.format(target_remote, target_branch)), header=False)

        latest_sha = common_repo_functions.get_latest_sha(repo.git, target_branch, repo.manifest.remote_url)
        try:
            repo.git.commit(latest_sha)
        except ValueError:
            repo.git.remotes.origin.fetch('refs/heads/{}'.format(target_branch))
        branch_origin = next(itertools.islice(repo.git.iter_commits(), commit_count, commit_count + 1))
        behind_count = int(repo.git.git.rev_list('--count', '{}..{}'.format(branch_origin.hexsha, latest_sha)))
        if behind_count:
            warning = True
            print()
            rebase_str = humble.SEND_REVIEW_NEEDS_REBASE.format(behind_count=behind_count,target_remote=target_remote,
                                                                target_branch=target_branch, local_branch=local_branch)
            ui_functions.print_warning_msg(rebase_str, header=True)

        if repo.git.is_dirty(untracked_files=False):
            warning = True
            staged_for_commit = get_changed_file_list(repo.git.index.diff('HEAD'))
            not_staged = get_changed_file_list(repo.git.index.diff(None))
            if staged_for_commit:
                print()
                ui_functions.print_warning_msg(humble.SEND_REVIEW_UNCOMMITTED_STAGED, header=True)
                print()
                for file in staged_for_commit:
                    ui_functions.print_warning_msg("        {}{}{}".format(Fore.GREEN, file, Fore.RESET), header=False)
            if not_staged:
                print()
                ui_functions.print_warning_msg(humble.SEND_REVIEW_UNCOMMITTED_NO_STAGE, header=True)
                print()
                for file in not_staged:
                    ui_functions.print_warning_msg("        {}{}{}".format(Fore.RED, file, Fore.RESET), header=False)
        branch_head = repo.git.commit('HEAD')
        touched_files = common_repo_functions.get_touched_files(repo.git, branch_origin, branch_head)
        target_url = repo.manifest.remote_url

        if not args.dry_run:
            print()
            create_review_string = (humble.CREATING_REVIEW.format(local_branch=local_branch, local_repo=repo.git.git_dir,
                                    target_branch=target_branch, remote_url=target_url))
            ui_functions.print_info_msg(create_review_string, header=False)

        if warning and not args.dry_run and not args.override:
            print()
            raise edkrepo_exception.EdkrepoWarningException(humble.SEND_REVIEW_WARNING)

        if args.dry_run:
            self.__print_dry_run_header(repo, touched_files, target_url)

        if review_type == Reviews.PR_BRANCH:
            self.__send_github_pr_branch_mode(args, config, local_name, target_branch, repo, manifest, netrc_path)

    def __print_dry_run_header(self, repo, touched_files, target_url):
        print()
        review_header_create = (humble.CREATING_REVIEW_DRY_RUN.format(local_branch=repo.git.active_branch,
                                                                      local_repo=repo.git.git_dir,
                                                                      target_branch=repo.manifest.branch,
                                                                      remote_url=target_url))
        ui_functions.print_info_msg(review_header_create, header=False)
        print()
        ui_functions.print_info_msg(humble.FILES, header=False)
        for touched_file in touched_files:
            ui_functions.print_info_msg(touched_file, header=False)

    def __send_github_pr_branch_mode(self, args, config, current_branch, target_branch, modified_repo, manifest, netrc_path):
        """
        Creates a GitHub PR using the following steps:
        1. Creates a local PR branch using the title parameter OR verifies that current branch is a PR branch
        2. Push that branch to GitHub
        3. Using the GitHub Rest API open a PR and name it 'Title'
        """

        amend_existing = False
        pr_branch_name = None
        pr_number = None
        title_string = None

        # Get all active PRs by their PR number in remote, else None if no active PRs
        active_prs = self.__get_active_prs_on_branch(args, current_branch, modified_repo, manifest, netrc_path)
        if active_prs:
            amend_existing = True
            pr_branch_name = str(current_branch)
        else:
            if not args.title:
                # If there is only one commit to on the branch, then we can use the title of that commit as the title
                # of the PR if the user did not otherwise specify a title.
                commit_shas = modified_repo.git.git.rev_list('{}/{}..HEAD'.format(common_repo_functions.DEFAULT_REMOTE_NAME, target_branch))
                commit_shas = commit_shas.splitlines()
                if len(commit_shas) != 1:
                    raise edkrepo_exception.EdkrepoInvalidParametersException(humble.NO_TITLE)
                commit_message = modified_repo.git.commit(commit_shas[0]).message.splitlines()
                if len(commit_message) < 1:
                    raise edkrepo_exception.EdkrepoInvalidParametersException(humble.NO_TITLE)
                title_string = commit_message[0]
            else:
                title_string = ' '.join(args.title)

            pr_branch_name = self.__create_pr_branch(config, modified_repo.git, title_string)

            # Only check out the PR branch if we are not in dry-run mode
            if not args.dry_run:
                modified_repo.git.heads[pr_branch_name].checkout()

        pr_branch_str = '{}:{}'.format(pr_branch_name, pr_branch_name)

        if not amend_existing:
            # Push the branch to GitHub and then use the GitHub API to open a PR
            if args.dry_run:
                output_data = (modified_repo.git.git.execute(['git', 'push', 'origin', '--dry-run', pr_branch_str],
                                                             with_extended_output=True,
                                                             with_stdout=True))
                print()
                ui_functions.print_info_msg(humble.STATUS_CODE, header=False)
                ui_functions.print_info_msg(output_data[0], header=False)
                ui_functions.print_info_msg(humble.OUTPUT, header=False)
                ui_functions.print_info_msg(output_data[1], header=False)
                ui_functions.print_info_msg(output_data[2], header=False)

                # Delete the branch, this is just a dry run
                modified_repo.git.delete_head(modified_repo.git.heads[pr_branch_name])

            if not args.dry_run:
                manual_pr_create = None
                try:
                    output_data = (modified_repo.git.git.execute(['git', 'push', 'origin', pr_branch_str],
                                                                 with_extended_output=True, with_stdout=True))
                    for output in output_data:
                        ui_functions.print_info_msg(output, header=False)
                    if isinstance(output_data[2], str):
                        for token in output_data[2].split():
                            if "http" in token and "new" in token:
                                manual_pr_create = token
                except GitCommandError as e:
                    ui_functions.print_error_msg(e.stdout, header=True)
                    print()
                    ui_functions.print_error_msg(humble.INITIAL_BRANCH_PUSH_FAILED.format(pr_branch_name), header=True)
                    print()
                    raise(edkrepo_exception.EdkrepoGitException(humble.NO_PR_CREATED))

                # Since this is not a dry run use the GitHub PR API to open a PR

                # Pull proxy information from git config
                proxy_str = common_repo_functions.get_proxy_str()
                if args.verbose:
                    ui_functions.print_info_msg(humble.PROXY_STR.format(proxy_str), header=False)
                remote = manifest.get_remote(modified_repo.manifest.remote_name)
                pr_create_url = 'https://api.github.com/repos/{}/{}/pulls'.format(remote.owner, remote.name)

                # See https://docs.github.com/en/rest/reference/pulls#create-a-pull-request for data format
                if args.draft:
                    data = '{{"title": "{}", "head": "{}", "base": "{}", "draft": "True"}}'.format(title_string, pr_branch_name, target_branch)
                else:
                    data = '{{"title": "{}", "head": "{}", "base": "{}"}}'.format(title_string, pr_branch_name, target_branch)

                curl_path = common_repo_functions.find_curl()
                if args.verbose:
                    ui_functions.print_info_msg(humble.CURL_PATH.format(curl_path), header=False)
                if not curl_path:
                    ui_functions.print_error_msg(humble.CURL_NOT_FOUND, header=True)
                    ui_functions.print_error_msg(humble.CREATE_PR_MANUALLY.format(manual_pr_create), header=True)
                    raise edkrepo_exception.EdkrepoWarningException(humble.NO_PR_CREATED)
                if proxy_str:
                    curl_args = [curl_path, '--netrc-file', netrc_path, '-X', 'POST', '-H',
                                'Accept: application/vnd.github.v3+json', pr_create_url, '-d', data, '--proxy', proxy_str]
                else:
                    curl_args = [curl_path, '--netrc-file', netrc_path, '-X', 'POST', '-H',
                                'Accept: application/vnd.github.v3+json', pr_create_url, '-d', data]
                curl_process = subprocess.Popen(curl_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = curl_process.communicate()
                if stdout:
                    results = json.loads(stdout)
                    if 'html_url' in results.keys():
                        ui_functions.print_info_msg(humble.PULL_REQUEST_CREATED.format(results['html_url']), header=False)
                        if 'number' in results.keys():
                            pr_number = results['number']
                            # Add reviewers
                            
                            ui_functions.print_info_msg(humble.ADD_REVIEWERS, header=False)
                            if pr_number and args.reviewers:
                                self.__github_add_reviewers(args, pr_patch_url, netrc_path, curl_path, proxy_str)

                        if not args.noweb:
                            webbrowser.open(results['html_url'])
                    else:
                        if args.verbose:
                            ui_functions.print_error_msg(humble.PULL_REQUEST_FAILURE_MESSAGE.format(results['message']), header=True)
                        ui_functions.print_error_msg(humble.CREATE_PR_MANUALLY.format(manual_pr_create), header=True)
                        raise(edkrepo_exception.EdkrepoWarningException(humble.NO_PR_CREATED))

                else:
                    ui_functions.print_error_msg(humble.CREATE_PR_MANUALLY.format(''), header=True)
                    raise(edkrepo_exception.EdkrepoWarningException(humble.NO_PR_CREATED))

        else:
            # Just push the branch to GitHub. Since it is overwriting a branch with an open PR GitHub should handle the
            # updates
            # In order to update the existing branch a force push is required
            if args.dry_run:
                if args.title:
                    title_string = ' '.join(args.title)
                    ui_functions.print_info_msg(humble.CHANGING_TITLE_DRY_RUN.format(title_string), header=False)

                output_data = (modified_repo.git.git.execute(['git', 'push', 'origin', '--dry-run', pr_branch_str, '--force'],
                                                             with_extended_output=True, with_stdout=True))
                print()
                ui_functions.print_info_msg(humble.STATUS_CODE, header=False)
                ui_functions.print_info_msg(output_data[0], header=False)
                ui_functions.print_info_msg(humble.OUTPUT, header=False)
                ui_functions.print_info_msg(output_data[1], header=False)
                ui_functions.print_info_msg(output_data[2], header=False)
            if not args.dry_run:
                output_data = (modified_repo.git.git.execute(['git', 'push', 'origin', pr_branch_str, '--force'],
                                                             with_extended_output=True, with_stdout=True))
                for output in output_data:
                    ui_functions.print_info_msg(output, header=False)

                proxy_str = common_repo_functions.get_proxy_str()
                if args.title:
                    title_string = ' '.join(args.title)
                    data = '{{"title": "{}"}}'.format(title_string)
                else:
                    title_string = None
                    data = None

                remote = manifest.get_remote(modified_repo.manifest.remote_name)
                curl_path = common_repo_functions.find_curl()
                if not curl_path:
                    ui_functions.print_error_msg(humble.CURL_NOT_FOUND, header=True)

                for pr_number in active_prs.keys():
                    pr_patch_url = 'https://api.github.com/repos/{}/{}/pulls/{}'.format(remote.owner, remote.name, pr_number)
                    if args.title:
                        if proxy_str:
                            curl_args = [curl_path, '--netrc-file', netrc_path, '-X', 'PATCH', '-H',
                                            'Accept: application/vnd.github.v3+json', pr_patch_url, '-d', data, '--proxy', proxy_str]
                        else:
                            curl_args = [curl_path, '--netrc-file', netrc_path, '-X', 'PATCH', '-H',
                                            'Accept: application/vnd.github.v3+json', pr_patch_url, '-d', data]
                        curl_process = subprocess.Popen(curl_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = curl_process.communicate()
                        if stdout:
                            results = json.loads(stdout)
                            if 'html_url' not in results.keys():
                                if args.verbose:
                                    ui_functions.print_error_msg(humble.PULL_REQUEST_FAILURE_MESSAGE.format(results['message']), header=True)
                                ui_functions.print_error_msg(humble.CHANGE_TITLE_MANUALLY, header=True)
                                raise edkrepo_exception.EdkrepoWarningException(humble.NO_PR_UPDATED)
                        else:
                            ui_functions.print_error_msg(humble.CHANGE_TITLE_MANUALLY, header=True)
                            raise edkrepo_exception.EdkrepoWarningException(humble.NO_PR_UPDATED)

                        ui_functions.print_info_msg(humble.CHANGING_TITLE.format(title_string), header=False)
                    if args.reviewers:
                        self.__github_add_reviewers(args, pr_patch_url, netrc_path, curl_path, proxy_str)
                for pr in active_prs:
                    print()
                    ui_functions.print_info_msg(humble.PULL_REQUEST_UPDATED.format(active_prs[pr]), header=False)
                    webbrowser.open(active_prs[pr])

    def __github_add_reviewers(self, args, pr_patch_url, netrc_path, curl_path, proxy_str=None):
        reviewer_array = args.reviewers[0].split(' ')
        pr_url = '{}/requested_reviewers'.format(pr_patch_url)
        reviewer_request = ('{{"reviewers":{}}}'.format(reviewer_array)).replace("'", '"')
        if proxy_str:
            reviewer_args = [curl_path, '--netrc-file', netrc_path, '-X', 'POST', '-H',
                            'Accept: application/vnd.github.v3+json', pr_url, '-d', reviewer_request,
                            '--proxy', proxy_str]
        else:
            reviewer_args = [curl_path, '--netrc-file', netrc_path, '-X', 'POST', '-H',
                            'Accept: application/vnd.github.v3+json', pr_url, '-d', reviewer_request]
        reviewer_process = subprocess.Popen(reviewer_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        reviewer_process.communicate()


    def __create_pr_branch(self, config, repo, title):
        """
        Creates a PR branch using the following steps:
        1. Normalize the 'Title' parameter by lower casing and replacing whitespace with '_'
        2. Create a local branch based on the currently checked out branch with the following
        naming convention: pull_request/github_username/date/title
        Note: timestamps are in the format year-month-day_hours-minutes
        """
        chars_to_strip = r'[^a-zA-Z0-9_-]'  # Non-alphanumeric characters excluding underscore and hyphen
        pr_branch_prefix = 'pull_request'
        normalized_title = str(title).strip().replace(' ', '_').lower()
        normalized_title, n_subbed = re.subn(chars_to_strip, '', normalized_title)
        # datetime format codes documented here:
        # https://docs.python.org/3.8/library/datetime.html#strftime-and-strptime-format-codes
        normalized_date = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M')
        git_email_string = common_repo_functions.get_git_config_email()
        if not git_email_string:
            raise edkrepo_exception.EdkRepoGitEmailNotFoundException(humble.GIT_EMAIL_NOT_FOUND)
        pr_branch_name = '/'.join([pr_branch_prefix, git_email_string.split('@')[0].lower(), normalized_date, normalized_title])
        if n_subbed > 0:
            ui_functions.print_info_msg(humble.PR_TITLE_STRIPPED_CHARS.format(n_subbed))

        pr_branch = repo.create_head(pr_branch_name)
        return pr_branch.name


    def __get_active_prs_on_branch(self, args, current_branch, modified_repo, manifest, netrc_path):
        remote = manifest.get_remote(modified_repo.manifest.remote_name)
        curl_path = common_repo_functions.find_curl()
        if not curl_path:
            ui_functions.print_error_msg(humble.CURL_NOT_FOUND, header=True)
            raise edkrepo_exception.EdkrepoWarningException(humble.CURL_NOT_FOUND)
        proxy_str = common_repo_functions.get_proxy_str()
        find_pr_url = 'https://api.github.com/repos/{}/{}/pulls'.format(remote.owner, remote.name)
        data = 'head={}:{}'.format(remote.owner, current_branch)

        if proxy_str:
            curl_args = [curl_path, '--netrc-file', netrc_path, '-X', 'GET', '-G', '-H',
                            'Accept: application/vnd.github.v3+json', find_pr_url, '-d', data, '--proxy', proxy_str]
        else:
            curl_args = [curl_path, '--netrc-file', netrc_path, '-X', 'GET', '-G', '-H',
                            'Accept: application/vnd.github.v3+json', find_pr_url, '-d', data]
        curl_process = subprocess.Popen(curl_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = curl_process.communicate()
        if stdout:
            results = json.loads(stdout)
            pr_count = len(results)
            if pr_count >= 1:
                try:
                    active_prs = {results[i]['number']: results[i]['html_url'] for i in range(pr_count)}
                except KeyError as e:
                    if args.verbose:
                        ui_functions.print_error_msg(results)
                        ui_functions.print_info_msg(curl_args)
                    raise edkrepo_exception.EdkrepoGithubApiFailException(humble.REST_CALL_ERROR.format(e))
                if pr_count > 1:
                    print()
                    ui_functions.print_info_msg(humble.MULTIPLE_OPEN_PRS.format(pr_count=pr_count, branch_name=current_branch))
                return active_prs
            else:
                return None
        else:
            raise edkrepo_exception.EdkrepoWarningException(humble.CURRENT_BRANCH_NOT_FOUND.format(current_branch))

    def __get_review_type(self, manifest, repo):
        remote_review_dest = manifest.get_remote(repo.manifest.remote_name)
        review_type = remote_review_dest.review_type
        if review_type and review_type.lower() == 'pull request':
            if not remote_review_dest.pr_strategy or remote_review_dest.pr_strategy.lower() == 'branch':
                return Reviews.PR_BRANCH
            elif remote_review_dest.pr_strategy.lower() == 'fork':
                return Reviews.PR_FORK
            else:
                raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_INVALID_PR_STRATEGY.format(remote_review_dest.pr_strategy))


def get_changed_file_list (diff):
    files = set()
    files.update([x.a_path for x in diff])
    files.update([x.b_path for x in diff])
    return files


class ModifiedRepo():
    """
    self.git is a Repo object
    self.manifest is the repo source tuple affiliated with the Repo object
    """
    def __init__(self, manifest, workspace_path, repo_reference=None):
        if repo_reference:
            for manifest_repo in manifest.get_repo_sources(manifest.general_config.current_combo):
                repo_path = os.path.join(workspace_path, manifest_repo.root)
                if manifest_repo.root == repo_reference or manifest_repo.remote_name == repo_reference:
                    self.manifest = manifest_repo
                    self.git = Repo(repo_path)
                    if self.git.head.is_detached:
                        raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_DETACHED_HEAD)
                    return
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_NO_REPO.format(repo_reference))
        modified_repos = []
        for manifest_repo in manifest.get_repo_sources(manifest.general_config.current_combo):
            repo_path = os.path.join(workspace_path, manifest_repo.root)
            git_repo = Repo(repo_path)
            if manifest_repo.patch_set:
                raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_PATCHSET_REPO)
            if not git_repo.head.is_detached:
                commits_ahead = common_repo_functions.get_commits_ahead(git_repo,
                                                "origin/{}".format(manifest_repo.branch),
                                                git_repo.active_branch)
                if len(list(commits_ahead)) > 0:
                    modified_repos.append((manifest_repo, git_repo))
        if len(modified_repos) == 0:
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_NO_LOCAL_BRANCHES)
        if len(modified_repos) > 1:
            raise edkrepo_exception.EdkrepoInvalidParametersException(humble.SEND_REVIEW_LOCAL_BRANCHES_IN_MULTIPLE_REPOS)
        self.manifest = modified_repos[0][0]
        self.git = modified_repos[0][1]


class Reviews(Enum):
    PR_BRANCH = 1
    PR_FORK = 2
