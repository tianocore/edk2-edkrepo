#!/usr/bin/env python3
#
## @file
# send_review_humble.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""
Contains informational and error messages outputted by
the run_command functions of Edkrepo commands
"""
from edkrepo.common.humble import AMEND, ADD, RESET_HEAD
from edkrepo.common.humble import CHECKOUT, CHECKOUT_HEAD, BRANCH_BEHIND
from edkrepo.common.humble import WARNING_MESSAGE

# Warning and error messages for send_review_command.py
SEND_REVIEW_EXIT = 'Exiting without sending review.\n'
SEND_REVIEW_USE_LOCAL = 'To send this review first switch to a local branch and then run "edkrepo send-review"\n'
SEND_REVIEW_LOCAL_BRANCHES_IN_MULTIPLE_REPOS = 'Local branches exist in more than one repository in the workspace. Please specify which repository to send a review for. ' + SEND_REVIEW_EXIT
SEND_REVIEW_NO_LOCAL_BRANCHES = 'No local branches exist to push for review. ' + SEND_REVIEW_EXIT
SEND_REVIEW_NO_REPO = 'No repo with the name {0} exists. ' + SEND_REVIEW_EXIT
SEND_REVIEW_NO_BRANCH = 'No branch with the name {0} exists. ' + SEND_REVIEW_EXIT
SEND_REVIEW_PATCHSET_REPO = 'Sending a review to a dynamically created branch is not allowed.'
SEND_REVIEW_DETACHED_HEAD = 'The selected repository is detached head mode. ' + SEND_REVIEW_EXIT
SEND_REVIEW_ON_TARGET = 'Attempting to send a review from the target branch: {}\n' + SEND_REVIEW_USE_LOCAL + SEND_REVIEW_EXIT
SEND_REVIEW_NEEDS_REBASE = BRANCH_BEHIND + '\n' + '  (use "edkrepo sync" then "git rebase {target_remote}/{target_branch} {local_branch}" to rebase your commit)'
SEND_REVIEW_MULTIPLE_COMMITS = 'Your branch has multiple commits and will generate {commit_count} separate reviews.'
SEND_REVIEW_UNCOMMITTED_STAGED = 'Uncommitted changes are present in the following staged files:\n  (use ' + AMEND + ')\n  (' + RESET_HEAD + ' before amending to unstage unwanted changes)\n  (' + CHECKOUT_HEAD + ' before amending to discard unwanted changes)'
SEND_REVIEW_UNCOMMITTED_NO_STAGE = 'Uncommitted changes are present in the following unstaged files:\n  (' + ADD + ' followed by ' + AMEND + ')\n  (' + CHECKOUT + ' to revert unwanted changes)'
SEND_REVIEW_WARNING = WARNING_MESSAGE + '\n' + SEND_REVIEW_EXIT
INITIAL_BRANCH_PUSH_FAILED = ('The branch {} was unable to be pushed to the remote server.\nRun "edkrepo self-check to'
                              ' verify connection and 1Source onboarding status')
NO_PR_CREATED = 'No pull request will be opened for this change'
CREATE_PR_MANUALLY = 'A pull request was unable to be opened via the GitHub PR API.\nTo open a PR for this change visit: {}'
PULL_REQUEST_FAILURE_MESSAGE = 'Pull request creation failed with: {}'
CURL_NOT_FOUND = 'Path to curl.exe not found.'
CURL_PATH = 'Path to curl.exe is: {}'
PROXY_STR = 'Proxy string is: {}'
NO_TITLE = 'The title argument is required for GitHub pull requests'
MULTIPLE_OPEN_PRS = 'You currently have {pr_count} pull requests open on branch "{branch_name}". All {pr_count} of them will be updated with this review.'
CURRENT_BRANCH_NOT_FOUND = 'Could not find current branch "{}" on GitHub.'
REST_CALL_ERROR = 'There was a problem in attempting to contact GitHub: {}'
GIT_EMAIL_NOT_FOUND = 'Email not found or configured in git config. Please set your git email using "git config --global user.email " \n' + SEND_REVIEW_EXIT

# informational messages for send_review_command.py
CREATING_REVIEW = 'Creating review for branch "{local_branch}" in local repository "{local_repo}" pushing to branch "{target_branch}" on remote url "{remote_url}"'
DRY_RUN = 'If run without the --dry-run flag edkrepo send-review will '
CREATING_REVIEW_DRY_RUN = DRY_RUN + 'create a review for branch: "{local_branch}" in local repository: "{local_repo}" and will push to branch: "{target_branch}" on remote_url: "{remote_url}"'
FILES = 'The following files will be pushed for review: '
STATUS_CODE = 'git push --dry-run returned the following status code: '
OUTPUT = 'git push --dry-run returned the following output: '
PULL_REQUEST_CREATED = 'A pull request was successfully opened and is available at: {}'
PULL_REQUEST_UPDATED = 'A pull request was successfully updated and is available at: {}'
PR_TITLE_STRIPPED_CHARS = 'To create a pull request branch, {} reserved characters were stripped from the given title. Please note that the actual title of the pull request is unaffected, only the branch name is changed.'
PR_MULTIPLE_COMMITS = 'After this review is sent, this pull request will have a total of {commit_count} commits on it.'
CHANGING_TITLE = 'Changed title of all active PRs on this branch to "{}"'
CHANGING_TITLE_DRY_RUN = DRY_RUN + 'change the title of all active PRs on this branch to "{}"'
CHANGE_TITLE_MANUALLY = 'Unable to change the title of the open pull request. Please change the title manually via the GitHub web UI.'
NO_PR_UPDATED = 'No pull request will be updated with this change'
ADD_REVIEWERS = 'Adding reviewers to pull request.'
SEND_REVIEW_INVALID_PR_STRATEGY = 'The specified PR strategy "{}" is invalid. Valid strategies are "branch" and "fork".'
SEND_REVIEW_PR_FORK_NOT_IMPLEMENTED = 'Sending reviews via the "fork" PR strategy is not yet supported.'
INVALID_REVIEWER = "Reviews may only be requested from collaborators. {} is not a collaborator of the {} repository."