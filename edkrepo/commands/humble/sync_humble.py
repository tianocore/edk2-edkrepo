#!/usr/bin/env python3
#
## @file
# sync_humble.py
#
# Copyright (c) 2023, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains informational and error messages outputted by
the run_command function method of the Sync command
'''

from edkrepo.common.humble import BRANCH_BEHIND

SYNC_EXIT = 'Exiting without performing sync operations.'
SYNC_UPDATE_FIX = 'To checkout the new SHA/tag/branch run edkrepo checkout on the current combo.\n'
SYNC_MANIFEST_NOT_FOUND = 'A manifest for project, {}, was not found.\nTo complete this operation please rerun the command with the --override flag\n' + SYNC_EXIT
SYNC_MANIFEST_UPDATE_FAILED = 'Failed to update manifest.'
SYNC_SOURCE_MOVE_WARNING = '{} being moved to {}'
SYNC_REMOVE_WARNING = 'The following repos no longer exist in the new manifest and can no \nlonger be used for submitting code. Please manually delete the following \ndirectories after saving any work you have in them:'
SYNC_MANIFEST_DIFF_WARNING = 'The global manifest for this project differs from the local manifest.'
SYNC_MANIFEST_UPDATE = 'To update to the latest manifest please run edkrepo sync --update-local-manifest.'
SYNC_REPO_CHANGE = 'The latest manifest for project, {}, requires a change in currently cloned repositories.\nTo complete this operation please rerun the command with the --override flag\n' + SYNC_EXIT
SYNCING = 'Syncing {0} to latest {1} branch ...'
FETCHING = 'Fetching latest code for {0} from {1} branch ...'
UPDATING_MANIFEST = 'Updating local manifest file ...'
NO_SYNC_DETACHED_HEAD = 'No need to sync repo {0} since it is in detached HEAD state'
SYNC_COMMITS_ON_TARGET = 'Commits were found on {0} branch.\n  (use the "--override" flag to overwrite these commits)\nRepo {1} was not updated.'
SYNC_ERROR = '\nError: Some repositories were not updated.'
SYNC_NEEDS_REBASE = BRANCH_BEHIND + '\n' + '  (use "git rebase {target_remote}/{target_branch} {local_branch}" inside the {repo_folder} folder to rebase your commit)'
SYNC_BRANCH_CHANGE_ON_LOCAL = 'The SHA, tag or branch defined in the current combo has changed from {} to {} for the {} repo.\n The current workspace is not on the SHA/tag/branch defined in the initial combo. Unable to checkout new SHA/tag/branch.\n' + SYNC_UPDATE_FIX
SYNC_REBASE_CALC_FAIL = 'Unable to calculate if a rebase is required for the current branch'
SYNC_MOVE_FAILED = '''Moving {initial_dir} to {new_dir} failed.
Most likely files from the original directory are open in an editor or IDE.
It is likely that {new_dir} contains your original code now.
Please close any open editors to reconcile this problem.
You may need to manually rename {new_dir} to {initial_dir} in some circumstances.\n'''
SYNC_AUTOMATIC_REMOTE_PRUNE = 'Performing automatic remote prune...'


