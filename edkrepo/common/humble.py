#!/usr/bin/env python3
#
## @file
# humble.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''Contains informational and error messages outputted by the run_command functions of Edkrepo commands'''

from colorama import Fore
from colorama import Style

# General error messages used by commands
UNSUPPORTED_COMBO = 'The selected COMBINATION/SHA is not present in the project manifest file or does not exist. '
UNCOMMITED_CHANGES = 'Uncommited changes present in {0} repo. '
UPDATING_MANIFEST = 'Updating local manifest file ...'
MISSING_BRANCH_COMMIT = 'Either the BRANCH name, TAG name or COMMIT ID must be specified in the combination field of the manifest file.'
WARNING_MESSAGE = 'One or more warnings present.\n  (use the "--override" flag to ignore warnings)'
AMEND = '"git commit --amend" to include these files in your commit'
RESET_HEAD = 'use "git reset HEAD <file>..."'
CHECKOUT_HEAD = 'use "git checkout HEAD <file>..."'
CHECKOUT = 'use "git checkout -- <file>..."'
ADD = 'use "git add <file>..."'
COMMIT_NOT_FOUND = 'The commit {} does not exist.'
BRANCH_BEHIND = 'Your branch \'{local_branch}\' is {behind_count} commit(s) behind \'{target_remote}/{target_branch}\' and should be rebased.'
COMMAND_NOT_SUPPORTED_MAC_OS = ' is not supported on macOS.'
COMMAND_NOT_SUPPORT_LINUX = ' is not supported on Linux.'
KEYBOARD_INTERRUPT = '\n\nKeyboard Interrupt'
SUBMODULE_FAILURE = 'Error while performing submodule initialization and clone operations for {} repo.\n'
NOT_GIT_REPO = 'The current directory does not appear to be a git repository'
MULTIPLE_SOURCE_ATTRIBUTES_SPECIFIED = 'BRANCH or TAG name present with COMMIT ID in combination field for {} repo. Using COMMIT ID.\n'
TAG_AND_BRANCH_SPECIFIED = 'BRANCH AND TAG name present in combination field for {} repo. Using TAG.\n'
CHECKING_CONNECTION = 'Checking connection to remote url: {}\n'

#Error messages for sync_command.py
SYNC_EXIT = 'Exiting without performing sync operations.'
SYNC_UNCOMMITED_CHANGES = UNCOMMITED_CHANGES + SYNC_EXIT
SYNC_COMMITS_ON_TARGET = 'Commits were found on {0} branch.\n  (use the "--override" flag to overwrite these commits)\nRepo {1} was not updated.'
SYNC_ERROR = '\nError: Some repositories were not updated.'
SYNC_MANIFEST_NOT_FOUND = 'A manifest for project, {0}, was not found.\nTo complete this operation please rerun the command with the --override flag\n' + SYNC_EXIT
SYNC_URL_CHANGE = 'The URL for the remote, {0} has changed.\n' + SYNC_EXIT
SYNC_COMBO_CHANGE = 'The current checked out combination, {0}, does not exist in the latest manifest for project, {1}\n'
SYNC_REPO_CHANGE = 'The latest manifest for project, {0}, requires a change in currently cloned repositories.\nTo complete this operation please rerun the command with the --override flag\n' + SYNC_EXIT
SYNC_SOURCE_MOVE_WARNING = '{}{}WARNING:{}{} {{}} being moved to {{}}'.format(Style.BRIGHT, Fore.RED, Style.RESET_ALL, Fore.RED)
SYNC_REMOVE_WARNING = '{}{}WARNING:{}{} The following repos no longer exist in the new manifest and can no \nlonger be used for submitting code. Please manually delete the following \ndirectories after saving any work you have in them:'.format(Style.BRIGHT, Fore.RED, Style.RESET_ALL, Fore.RED)
SYNC_MANIFEST_DIFF_WARNING = '{}{}WARNING:{}{} The global manifest for this project differs from the local manifest.'.format(Style.BRIGHT, Fore.RED, Style.RESET_ALL, Fore.RED)
SYNC_NEEDS_REBASE = BRANCH_BEHIND + '\n' + '  (use "git rebase {target_remote}/{target_branch} {local_branch}" inside the {repo_folder} folder to rebase your commit)'
SYNC_UPDATE_FIX = 'To checkout the new SHA/tag/branch run edkrepo checkout on the current combo.\n'
SYNC_BRANCH_CHANGE_ON_LOCAL = 'The SHA, tag or branch defined in the current combo has changed from {} to {} for the {} repo.\n The current workspace is not on the SHA/tag/branch defined in the initial combo. Unable to checkout new SHA/tag/branch.\n' + SYNC_UPDATE_FIX
SYNC_REBASE_CALC_FAIL = 'Unable to calculate if a rebase is required for the current branch'
SYNC_INCOMPATIBLE_COMBO = 'No compatible combinations found in the latest manifest file. Cloning a new workspace is recommended. ' + SYNC_EXIT

#informational messages for sync_command.py
SYNCING = 'Syncing {0} to latest {1} branch ...'
FETCHING = 'Fetching latest code for {0} from {1} branch ...'
NO_SYNC_DETACHED_HEAD = 'No need to sync repo {0} since it is in detached HEAD state'
SYNC_MANIFEST_UPDATE = 'To update to the latest manifest please run edkrepo sync --update-local-manifest. {}'.format(Fore.RESET)
SYNC_REMOVE_LIST_END_FORMATTING = '{}'.format(Style.RESET_ALL)
SYNC_MOVE_FAILED = '''{}{}WARNING:{}{} Moving {{initial_dir}} to {{new_dir}} failed.
{}{}{}Most likely files from the original directory are open in an editor or IDE.
It is likely that {{new_dir}} contains your original code now.
Please close any open editors to reconcile this problem.
You may need to manually rename {{new_dir}} to {{initial_dir}} in some circumstances.\n{}'''.format(Style.BRIGHT, Fore.RED, Style.RESET_ALL, Fore.RED, Style.RESET_ALL, Style.BRIGHT, Fore.YELLOW, Style.RESET_ALL)

#error messages for clone_command.py
CLONE_EXIT = '\nExiting without performing clone operation.'
CLONE_INVALID_WORKSPACE = 'The WORKSPACE argument must refer to an empty directory.' + CLONE_EXIT
CLONE_INVALID_PROJECT_ARG = 'The PROJECT NAME OR MANIFEST argument must refer to a valid project or manifest file.' + CLONE_EXIT
CLONE_INVALID_COMBO_ARG = UNSUPPORTED_COMBO + CLONE_EXIT
CLONE_INVALID_LOCAL_ROOTS = 'The selected combination is invalid; it contains duplicate local roots.' + CLONE_EXIT

# General sparse checkout messages
SPARSE_CHECKOUT = 'Performing sparse checkout...'
SPARSE_RESET = 'Resetting sparse checkout state...'

# Error messages for checkout_command.py
CHECKOUT_EXIT = 'Exiting without performing checkout opereration.'
CHECKOUT_INVALID_COMBO = UNSUPPORTED_COMBO + CHECKOUT_EXIT
CHECKOUT_CURRENT_COMBO = 'The selected combination, {0}, is already checked out ' + CHECKOUT_EXIT
CHECKOUT_UNCOMMITED_CHANGES = 'Uncommited changes present in workspace, unable to complete checkout.\nTo discard all local changes to tracked files rerun edkrepo checkout with the "--override" flag.\n'
CHECKOUT_NO_REMOTE = 'The specified remote branch for the {0} repo does not exist.'
CHECKOUT_COMBO_UNSUCCESSFULL = 'The combination {} was not able to be checked out successfully. Returning to initially active combination.'

# Informational messages for checkout_command.py
CHECKING_OUT_COMBO = 'Checking out combination: {0} ...'
CHECKING_OUT_BRANCH = 'Checking out {0} branch for {1} repo ...'
CHECKING_OUT_COMMIT = 'Checking detached HEAD on commit {0} for {1} repo ...'

# Messages for config_factory.py
MIRROR_PRIMARY_REPOS_MISSING = 'The edkrepo global configuration file missing [primary-repos] section.'
MIRROR_DECODE_WARNING = 'WARNING: Could not decode so assuming a primary repo: {}'
MAX_PATCH_SET_INVALID = 'Invalid value detected in user configuration file for max-patch-set (must be an integer).'

# Manifest verification error messages
VERIFY_ERROR_HEADER = 'Manifest repository verification errors:'
VERIFY_EXCEPTION_MSG = 'Manifest repository verification failed'
INDEX_DUPLICATE_NAMES = 'Project {} already exists in {}'
LOAD_MANIFEST_FAILED = 'Unable to process {}: {} ({})'
MANIFEST_NAME_INCONSISTENT = 'Index project name {} does not match codename {} in {}'

# Messages for sparse_command.py
SPARSE_ENABLE_DISABLE = 'Unable to Enable and Disable sparse checkout at the same time.'
SPARSE_NO_CHANGE = 'No sparse checkout change required.'
SPARSE_ENABLE = 'Enable Sparse Checkout:'
SPARSE_DISABLE = 'Disable Sparse Checkout:'
SPARSE_STATUS = 'Sparse Status:'
SPARSE_CHECKOUT_STATUS = '- Sparse Checkout: {}'
SPARSE_BY_DEFAULT_STATUS = '- Sparse By Default: {}'
SPARSE_ENABLED_REPOS = 'Sparse Enabled Repos ({}):'

# General string processing messages
GEN_A_NOT_IN_B = 'Unable to find {} in {}'
GEN_FOUND_MULT_A_IN_B = 'Found multiple matches for {} in {}'

# Messages for commit templates
COMMIT_TEMPLATE_NOT_FOUND = 'WARNING: Missing template file: {}'
COMMIT_TEMPLATE_CUSTOM_VALUE = 'WARNING: Custom commit template in use for: {}'
COMMIT_TEMPLATE_RESETTING_VALUE = 'Resetting commit template to the default value'

# Primary repo support strings
ADD_PRIMARY_REMOTE = 'Adding remote: {}'
REMOVE_PRIMARY_REMOTE = 'Removing remote: {}'
FETCH_PRIMARY_REMOTE = 'Fetching data from {}'
MIRROR_PRIMARY_SHA = '- Mirror SHA1: {}\n- Primary SHA1: {}'
MIRROR_BEHIND_PRIMARY_REPO = 'WARNING: Mirror repo behind latest version of primary repo.'# Messages for installing git hooks
HOOK_NOT_FOUND_ERROR = 'WARNING: {} was not found and is unable to be installed for {} repo.'

# Submodule alternate URL configuration strings
INCLUDED_URL_LINE = '[url "{}"]\n'
INCLUDED_INSTEAD_OF_LINE = '	insteadOf = {}\n'
INCLUDED_FILE_NAME = '.gitconfig-{}'
ERROR_WRITING_INCLUDE = 'An error occured while writting the URL redirection configuration for {} repo.\n'

#Error messages for squash.py
SQUASH_COMMON_ANCESTOR_REQUIRED = '{} is not in the same branch history as {}, unable to operate on this commit range.'

# Messages for common_repo_functions.
VERIFY_GLOBAL = 'Verifying the active projects in the global manifest repository\n'
VERIFY_ARCHIVED = 'Verifying the archived projects in the global manifest repository\n'
VERIFY_GLOBAL_FAIL = 'Unable to verify the contents of the global manifest repository\n'
VERIFY_PROJ = 'Verifying the global manifest repository entry for project: {}\n'
VERIFY_PROJ_NOT_IN_INDEX = 'Unable to find and entry in the CiIndex for project: {}\n'
VERIFY_PROJ_FAIL = 'Unable to verify the global manifest repository entry for project: {}\n'

# Git Command Error Messages
GIT_CMD_ERROR = 'The git command: {} failed to complete successfully with the following errors.\n'

# Error messages for create_pin_command.py
CREATE_PIN_EXIT = 'Exiting without creating pin file ...'
PIN_PATH_NOT_PRESENT = 'Pin Path not present in Manifest.xml ' + CREATE_PIN_EXIT
PIN_FILE_ALREADY_EXISTS = 'A pin file with that name already exists for this project. Please rerun the command with a new filename. ' + CREATE_PIN_EXIT
MISSING_REPO = 'The {} repository is missing from your workspace. ' + CREATE_PIN_EXIT

# Informational messages for create_pin_command.py
GENERATING_PIN_DATA = 'Generating pin data for {0} project based on {1} combination ...'
GENERATING_REPO_DATA = 'Generating pin data for {0} repo:'
BRANCH = '    Branch : {0}'
COMMIT = '    Commit Id: {0}'
WRITING_PIN_FILE = 'Writing pin file to {0} ...'
COMMIT_MESSAGE = 'Pin file for project: {0} \nPin Description: {1}'

# Common submodule error messages
SUBMODULE_DEINIT_FAILED = 'Warning: Unable to remove all submodule content'

# Logging messages
NETRC_PATH = "The netrc path is: {}"
GIT_VERSION = "Git Version: {}"
LFS_VERSION = "LFS Version: {}"
EDKREPO_VERSION = "edkrepo Version: {}"
PYTHON_VERSION = "Python Version: {}"
ENVIRONMENT_VARIABLES = "Environment Variables: {}"
GIT_CONFIG = "Git Config: {}"
NETRC_NOT_FOUND = 'Path to netrc not found. Please ensure you have configured your netrc file properly according to your OS guide.'
