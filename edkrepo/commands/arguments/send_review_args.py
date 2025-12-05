#!/usr/bin/env python3
#
## @file
# send_review_args.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""
Contains the help and description strings for arguments in the
combo command meta data.
"""

# Args for send_review_command.py
SEND_REVIEW_COMMAND_DESCRIPTION = 'Sends a local change for code review, required to make any official code change'
BRANCH_DESCRIPTION = 'Branch description'
BRANCH_HELP = 'Branch help'
REPO_DESCRIPTION = "Repository"
REPO_HELP = "The repository containing the code to be reviewed"
NOWEB_HELP = "Suppresses the default behavior of opening the review in a web browser"
REVIEWERS_HELP = 'Adds one or more reviewers via the command line.'
DRY_RUN_HELP = 'Lists the reviewers, target branch, and affected files but does not send a review.'
DRAFT_HELP = 'Creates a draft review.'
TITLE_HELP = 'The title of the PR. Also used to generate the name of the PR branch'
