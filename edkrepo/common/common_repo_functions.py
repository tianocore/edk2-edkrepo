#!/usr/bin/env python3
#
## @file
# common_repo_functions.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import collections
import os
import shutil
import sys
import unicodedata
import urllib.request
import subprocess
import traceback

import git
from git import Repo
import colorama

from edkrepo.config.config_factory import get_edkrepo_global_data_directory
from edkrepo.common.edkrepo_exception import EdkrepoManifestInvalidException
from edkrepo.common.edkrepo_exception import EdkrepoUncommitedChangesException
from edkrepo.common.edkrepo_exception import EdkrepoVerificationException
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo.common.progress_handler import GitProgressHandler
from edkrepo.common.humble import MISSING_BRANCH_COMMIT
from edkrepo.common.humble import UNCOMMITED_CHANGES, CHECKOUT_UNCOMMITED_CHANGES
from edkrepo.common.humble import CHECKING_OUT_COMMIT, CHECKING_CONNECTION
from edkrepo.common.humble import CHECKING_OUT_BRANCH
from edkrepo.common.humble import VERIFY_ERROR_HEADER
from edkrepo.common.humble import VERIFY_EXCEPTION_MSG
from edkrepo.common.humble import INDEX_DUPLICATE_NAMES
from edkrepo.common.humble import LOAD_MANIFEST_FAILED
from edkrepo.common.humble import MANIFEST_NAME_INCONSISTENT
from edkrepo.common.humble import CHECKOUT_NO_REMOTE
from edkrepo.common.humble import SPARSE_CHECKOUT
from edkrepo.common.humble import SPARSE_RESET
from edkrepo.common.humble import CHECKING_OUT_COMBO
from edkrepo.common.humble import CHECKOUT_INVALID_COMBO
from edkrepo.common.humble import CHECKOUT_COMBO_UNSUCCESSFULL
from edkrepo.common.humble import GEN_A_NOT_IN_B, GEN_FOUND_MULT_A_IN_B
from edkrepo.common.humble import COMMIT_TEMPLATE_NOT_FOUND, COMMIT_TEMPLATE_CUSTOM_VALUE
from edkrepo.common.humble import ADD_PRIMARY_REMOTE, REMOVE_PRIMARY_REMOTE
from edkrepo.common.humble import FETCH_PRIMARY_REMOTE, MIRROR_PRIMARY_SHA, TAG_AND_BRANCH_SPECIFIED
from edkrepo.common.humble import MIRROR_BEHIND_PRIMARY_REPO, HOOK_NOT_FOUND_ERROR, SUBMODULE_FAILURE
from edkrepo.common.humble import INCLUDED_URL_LINE, INCLUDED_INSTEAD_OF_LINE, INCLUDED_FILE_NAME
from edkrepo.common.humble import ERROR_WRITING_INCLUDE, MULTIPLE_SOURCE_ATTRIBUTES_SPECIFIED
from edkrepo.common.humble import VERIFY_GLOBAL, VERIFY_ARCHIVED, VERIFY_PROJ, VERIFY_PROJ_FAIL
from edkrepo.common.humble import VERIFY_PROJ_NOT_IN_INDEX, VERIFY_GLOBAL_FAIL
from edkrepo.common.humble import SUBMODULE_DEINIT_FAILED
from edkrepo.common.pathfix import get_actual_path, expanduser
from project_utils.sparse import BuildInfo, process_sparse_checkout
from edkrepo.config.config_factory import get_workspace_path
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo.config.tool_config import CI_INDEX_FILE_NAME
from edkrepo.config.tool_config import SUBMODULE_CACHE_REPO_NAME
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml
from edkrepo.common.edkrepo_exception import EdkrepoNotFoundException, EdkrepoGitException, EdkrepoWarningException
from edkrepo.common.edkrepo_exception import EdkrepoFoundMultipleException, EdkrepoHookNotFoundException
from edkrepo.common.edkrepo_exception import EdkrepoGitConfigSetupException, EdkrepoManifestInvalidException, EdkrepoManifestNotFoundException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo, list_available_manifest_repos
from edkrepo.common.workspace_maintenance.workspace_maintenance import case_insensitive_single_match
import edkrepo.common.ui_functions as ui_functions
from edkrepo_manifest_parser import edk_manifest
from edkrepo_manifest_parser.edk_manifest_validation import validate_manifestrepo
from edkrepo_manifest_parser.edk_manifest_validation import get_manifest_validation_status
from edkrepo_manifest_parser.edk_manifest_validation import print_manifest_errors
from edkrepo_manifest_parser.edk_manifest_validation import validate_manifestfiles
from project_utils.submodule import deinit_full, maintain_submodules

CLEAR_LINE = '\x1b[K'
DEFAULT_REMOTE_NAME = 'origin'
PRIMARY_REMOTE_NAME = 'primary'


def clone_repos(args, workspace_dir, repos_to_clone, project_client_side_hooks, config, manifest, cache_obj=None):
    for repo_to_clone in repos_to_clone:
        local_repo_path = os.path.join(workspace_dir, repo_to_clone.root)
        local_repo_url = repo_to_clone.remote_url
        cache_path = None
        if cache_obj is not None:
            cache_path = cache_obj.get_cache_path(local_repo_url)
        ui_functions.print_info_msg("Cloning from: " + str(local_repo_url), header = False)
        if cache_path is not None:
            ui_functions.print_info_msg('+ Using cache at {}'.format(cache_path))
            repo = Repo.clone_from(local_repo_url, local_repo_path,
                                   progress=GitProgressHandler(),
                                   reference_if_able=cache_path,
                                   no_checkout=True)
        else:
            repo = Repo.clone_from(local_repo_url, local_repo_path,
                                   progress=GitProgressHandler(),
                                   no_checkout=True)
        # Fetch notes
        repo.remotes.origin.fetch("refs/notes/*:refs/notes/*")

        # Add the primary remote so that a reference to the latest code is available when
        # using a mirror.
        if add_primary_repo_remote(repo, repo_to_clone, args.verbose):
            fetch_from_primary_repo(repo, repo_to_clone, args.verbose)

        # Handle branch/commit/tag checkout if needed. If a combination of these are specified the
        # order of importance is 1)commit 2)tag 3)branch with only the higest priority being checked
        # out
        if repo_to_clone.commit:
            if args.verbose and (repo_to_clone.branch or repo_to_clone.tag):
                ui_functions.print_info_msg(MULTIPLE_SOURCE_ATTRIBUTES_SPECIFIED.format(repo_to_clone.root))
            repo.git.checkout(repo_to_clone.commit)
        elif repo_to_clone.tag and repo_to_clone.commit is None:
            if args.verbose and repo_to_clone.branch:
                ui_functions.print_info_msg(TAG_AND_BRANCH_SPECIFIED.format(repo_to_clone.root))
            repo.git.checkout(repo_to_clone.tag)
        elif repo_to_clone.branch and (repo_to_clone.commit is None and repo_to_clone.tag is None):
            if repo_to_clone.branch not in repo.remotes['origin'].refs:
                raise EdkrepoManifestInvalidException('The specified remote branch does not exist')
            branch_name = repo_to_clone.branch
            local_branch = repo.create_head(branch_name, repo.remotes['origin'].refs[branch_name])
            repo.heads[local_branch.name].set_tracking_branch(repo.remotes['origin'].refs[branch_name])
            repo.heads[local_branch.name].checkout()
        else:
            raise EdkrepoManifestInvalidException(MISSING_BRANCH_COMMIT)

        try:
            if 'source_manifest_repo' in vars(args).keys():
                src_manifest_repo = find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo, False)
            else:
                src_manifest_repo = find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], None, False)
        except EdkrepoManifestNotFoundException:
            src_manifest_repo = None
        if src_manifest_repo:
            cfg, user_cfg, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])
            if src_manifest_repo in cfg:
                global_manifest_directory = config['cfg_file'].manifest_repo_abs_path(src_manifest_repo)
            elif src_manifest_repo in user_cfg:
                global_manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(src_manifest_repo)
            else:
                global_manifest_directory = None
        else:
            global_manifest_directory = None
        if global_manifest_directory:
            # Install git hooks if there is a manifest repo associated with the manifest being cloned
            install_hooks(project_client_side_hooks, local_repo_path, repo_to_clone, config, global_manifest_directory)

            # Add the commit template if it exists.
            update_repo_commit_template(workspace_dir, repo, repo_to_clone, config, global_manifest_directory)

        # Check to see if mirror is in sync with primary repo
        if not in_sync_with_primary(repo, repo_to_clone, args.verbose):
            ui_functions.print_warning_msg(MIRROR_BEHIND_PRIMARY_REPO)

def write_included_config(remotes, submodule_alt_remotes, repo_directory):
    included_configs = []
    for remote in remotes:
        included_config_name = os.path.join(repo_directory, INCLUDED_FILE_NAME.format(remote.name))
        included_config_name = get_actual_path(included_config_name)
        remote_alts = [submodule for submodule in submodule_alt_remotes if submodule.remote_name == remote.name]
        if remote_alts:
            with open(included_config_name, mode='w') as f:
                for alt in remote_alts:
                    url = f.write(INCLUDED_URL_LINE.format(alt.alternate_url))
                    instead_of = f.write(INCLUDED_INSTEAD_OF_LINE.format(alt.original_url))
                    if url == 0 or instead_of == 0:
                        raise EdkrepoGitConfigSetupException(ERROR_WRITING_INCLUDE.format(remote.name))
            included_configs.append((remote.name, included_config_name))
    return included_configs

def remove_included_config(remotes, submodule_alt_remotes, repo_directory):
    includes_to_remove = []
    for remote in remotes:
        include_to_remove = os.path.join(repo_directory, INCLUDED_FILE_NAME.format(remote.name))
        remote_alts = [submodule for submodule in submodule_alt_remotes if submodule.remote_name == remote.name]
        if remote_alts:
            includes_to_remove.append(include_to_remove)
    for include_to_remove in includes_to_remove:
        if os.path.isfile(include_to_remove):
            os.remove(include_to_remove)

def write_conditional_include(workspace_path, repo_sources, included_configs):
    gitconfigpath = os.path.normpath(expanduser("~/.gitconfig"))
    for source in repo_sources:
        for included_config in included_configs:
            if included_config[0] == source.remote_name:
                gitdir = str(os.path.normpath(os.path.join(workspace_path, source.root)))
                gitdir = get_actual_path(gitdir)
                gitdir = gitdir.replace('\\', '/')
                if sys.platform == "win32":
                    gitdir = '/{}'.format(gitdir)
                    path = '/{}'.format(included_config[1])
                else:
                    path = included_config[1]
                path = path.replace('\\', '/')
                section = 'includeIf "gitdir:{}/"'.format(gitdir)
                with git.GitConfigParser(gitconfigpath, read_only=False) as gitglobalconfig:
                    gitglobalconfig.add_section(section)
                    gitglobalconfig.set(section, 'path', path)

def install_hooks(hooks, local_repo_path, repo_for_install, config, global_manifest_directory):
    # Determine the which hooks are for the repo in question and which are from a URL based source or are in a global
    # manifest repo relative path
    hooks_url = []
    hooks_path = []
    for hook in hooks:
        if repo_for_install.remote_url == hook.remote_url:
            if str(hook.source).startswith('http'):
                hooks_url.append(hook)
            else:
                hooks_path.append(hook)

    # Download and install any URL sourced hooks
    for hook in hooks_url:
        if hook.dest_file:
            destination_path = os.path.join(local_repo_path, os.path.dirname(str(hook.dest_path)))
            hook_file_name = os.path.join(destination_path, str(hook.dest_name))
        else:
            destination = os.path.join(local_repo_path, hook.dest_path)
            hook_file_name = os.path.join(destination, hook.source.split('/')[-1])
        if not os.path.exists(destination):
            os.makedirs(destination)
        with urllib.request.urlopen(hook.source) as response, open(hook_file_name, 'wb') as out_file:
            data = response.read()
            out_file.write(data)

    # Copy any global manifest repository relative path source based hooks
    for hook in hooks_path:
        man_dir_rel_hook_path = os.path.join(global_manifest_directory, hook.source)
        if not os.path.exists(man_dir_rel_hook_path):
            raise EdkrepoHookNotFoundException(HOOK_NOT_FOUND_ERROR.format(hook.source, repo_for_install.root))
        if hook.dest_file:
            destination_path = os.path.join(local_repo_path, os.path.dirname(str(hook.dest_path)))
            hook_file_name = os.path.join(destination_path, str(hook.dest_file))
        else:
            destination_path = os.path.join(local_repo_path, hook.dest_path)
            hook_file_name = os.path.join(destination_path, (os.path.basename(str(hook.source))))
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        shutil.copy(man_dir_rel_hook_path, hook_file_name)
        if os.name == 'posix':
            # Need to make sure the script is executable or it will not run on Linux
            os.chmod(hook_file_name, os.stat(hook_file_name).st_mode | 0o111)

def uninstall_hooks(hooks, local_repo_path, repo_for_uninstall):
    for hook in hooks:
        if repo_for_uninstall.remote_url == hook.remote_url:
            if str(hook.source).startswith('http'):
                if hook.dest_file:
                    destination_path = os.path.join(local_repo_path, os.path.dirname(str(hook.dest_path)))
                    hook_file = os.path.join(destination_path, str(hook.dest_file))
                else:
                    destination = os.path.join(local_repo_path, hook.dest_path)
                    hook_file = os.path.join(destination, hook.source.split('/')[-1])
            else:
                if os.path.basename(str(hook.source)) == 'hook-dispatcher':
                    destination_path = os.path.join(local_repo_path, os.path.dirname(str(hook.dest_path)))
                    hook_file = os.path.join(destination_path, (os.path.basename(str(hook.dest_path))))
                else:
                    destination = os.path.join(local_repo_path, hook.dest_path)
                    hook_file = os.path.join(destination, (os.path.basename(str(hook.source))))
            os.remove(hook_file)

def update_hooks (hooks_add, hooks_update, hooks_uninstall, local_repo_path, repo, config, global_manifest_directory):
    if hooks_add:
        install_hooks(hooks_add, local_repo_path, repo, config, global_manifest_directory)
    if hooks_update:
        install_hooks(hooks_update, local_repo_path, repo, config, global_manifest_directory)
    if hooks_uninstall:
        uninstall_hooks(hooks_uninstall, local_repo_path, repo)

def sparse_checkout_enabled(workspace_dir, repo_list):
    repo_dirs = [os.path.join(workspace_dir, os.path.normpath(x.root)) for x in repo_list]
    if repo_dirs:
        build_info = BuildInfo(repo_dirs)
        if build_info.find_sparse_checkout():
            return True
    return False


def get_sparse_folder_list(repo):
    with repo.config_reader() as cr:
        if cr.has_option(section='core', option='sparsecheckout'):
            if not cr.get_value(section='core', option='sparsecheckout'):
                return None
    sparse_file_name = os.path.join('.git', 'info', 'sparse-checkout')
    sparse_file = os.path.normpath(os.path.join(repo.working_tree_dir, sparse_file_name))
    if not os.path.isfile(sparse_file):
        return []
    with open(sparse_file) as f:
        sparse_list = f.readlines()
    sparse_list = [x[1:].strip() for x in sparse_list]
    try:
        sparse_list.remove('*.*')
    except ValueError:
        pass
    try:
        sparse_list.remove('*')
    except ValueError:
        pass
    return sparse_list


def reset_sparse_checkout(workspace_dir, repo_list, disable=False):
    # Determine what repositories are targeted for sparse checkout
    repo_dirs = [workspace_dir]
    repo_dirs.extend([os.path.join(workspace_dir, os.path.normpath(x.root)) for x in repo_list])
    if repo_dirs:
        # Create sparse checkout object without DSC information and reset
        build_info = BuildInfo(repo_dirs)
        build_info.reset_sparse_checkout(disable)


def sparse_checkout(workspace_dir, repo_list, manifest):
    current_combo = manifest.general_config.current_combo
    try:
        process_sparse_checkout(workspace_dir, repo_list, current_combo, manifest)
    except RuntimeError as msg:
        print(msg)


def check_dirty_repos(manifest, workspace_path):
    repos = manifest.get_repo_sources(manifest.general_config.current_combo)
    for repo_to_check in repos:
        local_repo_path = os.path.join(workspace_path, repo_to_check.root)
        repo = Repo(local_repo_path)
        if repo.is_dirty(untracked_files=True):
            raise EdkrepoUncommitedChangesException(UNCOMMITED_CHANGES.format(repo_to_check.root))


def check_branches(sources, workspace_path):
    # check that the branches listed in the combination exist
    for repo_to_check in sources:
        repo = Repo(os.path.join(workspace_path, repo_to_check.root))
        if not repo_to_check.branch:
            continue
        if repo_to_check.branch not in repo.remotes['origin'].refs:
            try:
               repo.remotes.origin.fetch("refs/heads/{0}:refs/remotes/origin/{0}".format(repo_to_check.branch), progress=GitProgressHandler())
            except:
                raise EdkrepoManifestInvalidException(CHECKOUT_NO_REMOTE.format(repo_to_check.root))


def checkout_repos(verbose, override, repos_to_checkout, workspace_path, manifest):
    if not override:
        try:
            check_dirty_repos(manifest, workspace_path)
        except EdkrepoUncommitedChangesException:
            raise EdkrepoUncommitedChangesException(CHECKOUT_UNCOMMITED_CHANGES)
    check_branches(repos_to_checkout, workspace_path)
    for repo_to_checkout in repos_to_checkout:
        if verbose:
            if repo_to_checkout.branch is not None and repo_to_checkout.commit is None:
                print(CHECKING_OUT_BRANCH.format(repo_to_checkout.branch, repo_to_checkout.root))
            elif repo_to_checkout.commit is not None:
                print(CHECKING_OUT_COMMIT.format(repo_to_checkout.commit, repo_to_checkout.root))
        local_repo_path = os.path.join(workspace_path, repo_to_checkout.root)
        repo = Repo(local_repo_path)
        # Checkout the repo onto the correct branch/commit/tag if multiple attributes are provided in
        # the source section for the manifest the order of priority is the followiwng 1)commit
        # 2) tag 3)branch with the highest priority attribute provided beinng checked out
        if repo_to_checkout.commit:
            if verbose and (repo_to_checkout.branch or repo_to_checkout.tag):
                print(MULTIPLE_SOURCE_ATTRIBUTES_SPECIFIED.format(repo_to_checkout.root))
            if override:
                repo.git.checkout(repo_to_checkout.commit, '--force')
            else:
                repo.git.checkout(repo_to_checkout.commit)
        elif repo_to_checkout.tag and repo_to_checkout.commit is None:
            if verbose and (repo_to_checkout.branch):
                print(TAG_AND_BRANCH_SPECIFIED.format(repo_to_checkout.root))
            if override:
                repo.git.checkout(repo_to_checkout.tag, '--force')
            else:
                repo.git.checkout(repo_to_checkout.tag)
        elif repo_to_checkout.branch and (repo_to_checkout.commit is None and repo_to_checkout.tag is None):
            branch_name = repo_to_checkout.branch
            if branch_name in repo.heads:
                local_branch = repo.heads[branch_name]
            else:
                local_branch = repo.create_head(branch_name, repo.remotes['origin'].refs[branch_name])
            #check to see if the branch being checked out has a tracking branch if not set one up
            if repo.heads[local_branch.name].tracking_branch() is None:
                repo.heads[local_branch.name].set_tracking_branch(repo.remotes['origin'].refs[branch_name])
            if override:
                repo.heads[local_branch.name].checkout(force=True)
            else:
                repo.heads[local_branch.name].checkout()
        else:
            raise EdkrepoManifestInvalidException(MISSING_BRANCH_COMMIT)

def validate_manifest_repo(manifest_repo, verbose=False, archived=False):
    print(VERIFY_GLOBAL)
    if archived:
        print(VERIFY_ARCHIVED)
    manifest_validation_data = validate_manifestrepo(manifest_repo, archived)
    manifest_repo_error = get_manifest_validation_status(manifest_validation_data)
    if manifest_repo_error:
        print(VERIFY_GLOBAL_FAIL)
        if verbose:
            print_manifest_errors(manifest_validation_data)

def verify_single_manifest(cfg_file, manifest_repo, manifest_path, verbose=False):
    manifest = ManifestXml(manifest_path)
    print(VERIFY_PROJ.format(manifest.project_info.codename))
    index_path = os.path.join(cfg_file.manifest_repo_abs_path(manifest_repo), CI_INDEX_FILE_NAME)
    proj_val_data = validate_manifestfiles([manifest_path])
    proj_val_error = get_manifest_validation_status(proj_val_data)
    if proj_val_error:
        if verbose:
            print_manifest_errors(proj_val_data)
        raise EdkrepoManifestInvalidException(VERIFY_PROJ_FAIL.format(manifest.project_info.codename))

def sort_commits(manifest, workspace_path, max_commits=None):
    colorama.init()
    repo_sources_to_log = manifest.get_repo_sources(manifest.general_config.current_combo)

    commit_dictionary = {}
    for repo_to_log in repo_sources_to_log:
        local_repo_path = os.path.join(workspace_path, repo_to_log.root)
        repo = Repo(local_repo_path)
        print("Processing {} log...".format(repo_to_log.root), end='\r')
        if max_commits:
            commit_generator = repo.iter_commits(max_count=max_commits)
        else:
            commit_generator = repo.iter_commits()
        for commit in commit_generator:
            commit_dictionary[commit] = commit.committed_date
        print(CLEAR_LINE, end='')

    sorted_commit_list = sorted(commit_dictionary, key=commit_dictionary.get, reverse=True)
    if max_commits:
        sorted_commit_list = sorted_commit_list[:max_commits]
    return sorted_commit_list


def combinations_in_manifest(manifest):
    combination_names = [c.name for c in manifest.combinations]
    combination_names.extend([c.name for c in manifest.archived_combinations])
    return combination_names


def combination_is_in_manifest(combination, manifest):
    combination_names = combinations_in_manifest(manifest)
    return combination in combination_names


def checkout(combination, verbose=False, override=False, log=None, cache_obj=None):
    workspace_path = get_workspace_path()
    manifest = get_workspace_manifest()

    # Create combo so we have original input and do not introduce any
    # unintended behavior by messing with parameters.
    combo = combination
    submodule_combo = manifest.general_config.current_combo
    try:
        # Try to handle normalize combo name to match the manifest file.
        combo = case_insensitive_single_match(combo, combinations_in_manifest(manifest))
        submodule_combo = combo
    except:
        raise EdkrepoInvalidParametersException(CHECKOUT_INVALID_COMBO)

    repo_sources = manifest.get_repo_sources(combo)
    initial_repo_sources = manifest.get_repo_sources(manifest.general_config.current_combo)

    # Disable sparse checkout
    current_repos = initial_repo_sources
    sparse_enabled = sparse_checkout_enabled(workspace_path, initial_repo_sources)
    sparse_diff = False
    for source in initial_repo_sources:
        for src in repo_sources:
            if source.root == src.root:
                if source.sparse != src.sparse:
                    sparse_diff = True
        if sparse_diff:
            break
    # Sparse checkout only needs to be recomputed if
    # the dynamic sparse list is being used instead of the static sparse list
    # or the sparse settings between two combinations differ
    if sparse_enabled:
        sparse_settings = manifest.sparse_settings
        if sparse_settings is not None:
            sparse_enabled = False
    if sparse_enabled or sparse_diff:
        print(SPARSE_RESET)
        reset_sparse_checkout(workspace_path, current_repos)

    # Deinit all submodules due to the potential for issues when switching
    # branches.
    if combo != manifest.general_config.current_combo:
        try:
            deinit_full(workspace_path, manifest, verbose)
        except Exception as e:
            print(SUBMODULE_DEINIT_FAILED)
            if verbose:
                print(e)

    print(CHECKING_OUT_COMBO.format(combo))

    try:
        checkout_repos(verbose, override, repo_sources, workspace_path, manifest)
        current_repos = repo_sources
        # Update the current checkout combo in the manifest only if this
        # combination exists in the manifest
        if combination_is_in_manifest(combo, manifest):
            manifest.write_current_combo(combo)
    except:
        if verbose:
            traceback.print_exc()
        print (CHECKOUT_COMBO_UNSUCCESSFULL.format(combo))
        # Return to the initial combo, since there was an issue with cheking out the selected combo
        checkout_repos(verbose, override, initial_repo_sources, workspace_path, manifest)
    finally:
        cache_path = None
        if cache_obj is not None:
            cache_path = cache_obj.get_cache_path(SUBMODULE_CACHE_REPO_NAME)
        maintain_submodules(workspace_path, manifest, submodule_combo, verbose, cache_path)
        if sparse_enabled or sparse_diff:
            print(SPARSE_CHECKOUT)
            sparse_checkout(workspace_path, current_repos, manifest)

def get_latest_sha(repo, branch, remote_or_url='origin'):
    try:
        (latest_sha, _) = repo.git.ls_remote(remote_or_url, 'refs/heads/{}'.format(branch)).split()
    except:
        latest_sha = None
    return latest_sha

def get_full_path(file_name):
    paths = os.environ['PATH'].split(os.pathsep)
    if sys.platform == "win32":
        if os.environ['SystemRoot'] not in paths:
            paths.append(os.environ['SystemRoot'])
        if os.environ['windir'] not in paths:
            paths.append(os.environ['windir'])
    for path in paths:
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            return file_path
    return None

def update_repo_commit_template(workspace_dir, repo, repo_info, config, global_manifest_directory):
    # Open the local manifest and get any templates
    manifest = edk_manifest.ManifestXml(os.path.join(workspace_dir, 'repo', 'Manifest.xml'))
    templates = manifest.commit_templates

    #Check for the presence of a gloablly defined commit template
    global_template_in_use = False
    global_gitconfig_path = os.path.normpath(expanduser("~/.gitconfig"))
    with git.GitConfigParser(global_gitconfig_path, read_only=False) as gitglobalconfig:
        if gitglobalconfig.has_option(section='commit', option='template'):
            gitglobalconfig.get_value(section='commit', option='template')
            global_template_in_use = True
            print(COMMIT_TEMPLATE_CUSTOM_VALUE.format(repo_info.remote_name))

    # Apply the template based on current manifest
    with repo.config_writer() as cw:
        if not global_template_in_use:
            if cw.has_option(section='commit', option='template'):
                current_template = cw.get_value(section='commit', option='template').replace('"', '')
                if not current_template.startswith(os.path.normpath(global_manifest_directory).replace('\\', '/')):
                    print(COMMIT_TEMPLATE_CUSTOM_VALUE.format(repo_info.remote_name))
                    return

            if repo_info.remote_name in templates:
                template_path = os.path.normpath(os.path.join(global_manifest_directory, templates[repo_info.remote_name]))
                if not os.path.isfile(template_path):
                    print(COMMIT_TEMPLATE_NOT_FOUND.format(template_path))
                    return
                template_path = template_path.replace('\\', '/')    # Convert to git approved path
                cw.set_value(section='commit', option='template', value='"{}"'.format(template_path))
            else:
                if cw.has_option(section='commit', option='template'):
                    cw.remove_option(section='commit', option='template')
        else:
            if cw.has_option(section='commit', option='template'):
                cw.remove_option(section='commit', option='template')

def update_editor_config(config, global_manifest_directory):
    return

def has_primary_repo_remote(repo, verbose=False):
    """
    Checks to see if the repo has a primary remote.
    """
    return False

def add_primary_repo_remote(repo, repo_data, verbose=False):
    """
    Adds a primary remote if a mirror is being used.
    Returns:
      True - Primary remote added
      False - Primary remote not added
    """
    return True

def fetch_from_primary_repo(repo, repo_data, verbose=False):
    """
    Performs a fetch from the primary remote.
    """
    return

def in_sync_with_primary(repo, repo_data, verbose=False):
    """
    Checks to see if the current branch of the mirror is in sync with the
    primary repo branch.
    """
    return True

def check_single_remote_connection(remote_url):
    """
    Checks the connection to a single remote using git ls-remote remote_url -q invoked via subprocess
    instead of gitpython to ensure that ssh errors are caught and handled properly on both git bash
    and windows command line"""
    print(CHECKING_CONNECTION.format(remote_url))
    check_output = subprocess.Popen('git ls-remote {} -q'.format(remote_url), shell=True)
    check_output.communicate()

def find_project_in_index(project, ci_index_file, global_manifest_dir, except_message):
    """
    Finds a project in the CiIndexFile and returns the path to it within the global manifest repository.
    Raises and EdkrepoInvalidParametersException if not found"""
    try:
        proj_name = case_insensitive_single_match(project, ci_index_file.project_list)
    except:
        proj_name = None
    if proj_name:
        ci_index_xml_rel_path = os.path.normpath(ci_index_file.get_project_xml(proj_name))
        global_manifest_path = os.path.join(global_manifest_dir, ci_index_xml_rel_path)
    elif os.path.isabs(project):
        global_manifest_path = project
    else:
        if os.path.isfile(os.path.join(os.getcwd(), project)):
            global_manifest_path = os.path.join(os.getcwd(), project)
        elif os.path.isfile(os.path.join(global_manifest_dir, project)):
            global_manifest_path = os.path.join(global_manifest_dir, project)
        elif not os.path.dirname(project):
            for dirpath, _, filenames in os.walk(global_manifest_dir):
                if project in filenames:
                    global_manifest_path = os.path.join(dirpath, project)
                    break
            else:
                raise EdkrepoInvalidParametersException(except_message)
        else:
            raise EdkrepoInvalidParametersException(except_message)

    return global_manifest_path

def find_less():
    use_less = False
    if sys.platform == 'win32':
        git_path = get_full_path('git.exe')
        if git_path is not None:
            less_path = os.path.join(os.path.dirname(os.path.dirname(git_path)), 'usr', 'bin', 'less.exe')
            if os.path.isfile(less_path):
                use_less = True
                return less_path, use_less
            less_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(git_path))), 'usr', 'bin', 'less.exe')
            if os.path.isfile(less_path):
                use_less = True
                return less_path, use_less
        return None, use_less
    else:
        use_less = False
        less_path = get_full_path('less')
        if less_path:
            use_less = True
        return less_path, use_less


def find_curl():
    if sys.platform == 'win32':
        git_path = get_full_path('git.exe')
        if git_path is not None:
            curl_path = os.path.join(os.path.dirname(os.path.dirname(git_path)), 'mingw64', 'bin', 'curl.exe')
            if os.path.isfile(curl_path):
                return curl_path
            curl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(git_path))), 'mingw64', 'bin', 'curl.exe')
            if os.path.isfile(curl_path):
                return curl_path
        return None
    else:
        curl_path = get_full_path('curl')
        return curl_path