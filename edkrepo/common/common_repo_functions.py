#!/usr/bin/env python3
#
## @file
# common_repo_functions.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import json
import os
import shutil
import sys
import urllib.request
import subprocess
import traceback
import hashlib
import time

import git
from git import Repo
import colorama

import edkrepo.common.clone_utilities as clone_utils
from edkrepo.common.edkrepo_exception import EdkrepoBranchExistsException, EdkrepoException, EdkrepoLocalBranchExistsException, EdkrepoRevertFailedException, EdkrepoCherryPickFailedException, EdkrepoBranchCollidesWithParentShaException
from edkrepo.common.edkrepo_exception import EdkrepoFetchBranchNotFoundException
from edkrepo.common.edkrepo_exception import EdkrepoPatchNotFoundException, EdkrepoPatchFailedException
from edkrepo.common.edkrepo_exception import EdkrepoRemoteNotFoundException, EdkrepoRemoteAddException, EdkrepoRemoteRemoveException
from edkrepo.common.edkrepo_exception import EdkrepoManifestInvalidException
from edkrepo.common.edkrepo_exception import EdkrepoUncommitedChangesException
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo.common.progress_handler import GitProgressHandler
from edkrepo.common.humble import APPLYING_CHERRY_PICK_FAILED, APPLYING_PATCH_FAILED, APPLYING_REVERT_FAILED, BRANCH_EXISTS, CHECKING_OUT_DEFAULT, CHECKING_OUT_PATCHSET, LOCAL_BRANCH_EXISTS
from edkrepo.common.humble import FETCH_BRANCH_DOES_NOT_EXIST, PATCHFILE_DOES_NOT_EXIST, COLLISION_DETECTED
from edkrepo.common.humble import REMOTE_CREATION_FAILED, REMOTE_NOT_FOUND, REMOVE_REMOTE_FAILED
from edkrepo.common.humble import MISSING_BRANCH_COMMIT
from edkrepo.common.humble import UNCOMMITED_CHANGES, CHECKOUT_UNCOMMITED_CHANGES
from edkrepo.common.humble import CHECKING_OUT_COMMIT, CHECKING_CONNECTION
from edkrepo.common.humble import CHECKING_OUT_BRANCH
from edkrepo.common.humble import CHECKOUT_NO_REMOTE
from edkrepo.common.humble import SPARSE_CHECKOUT
from edkrepo.common.humble import SPARSE_RESET
from edkrepo.common.humble import CHECKING_OUT_COMBO
from edkrepo.common.humble import CHECKOUT_INVALID_COMBO
from edkrepo.common.humble import CHECKOUT_COMBO_UNSUCCESSFULL
from edkrepo.common.humble import COMMIT_TEMPLATE_NOT_FOUND, COMMIT_TEMPLATE_CUSTOM_VALUE
from edkrepo.common.humble import COMMIT_TEMPLATE_RESETTING_VALUE
from edkrepo.common.humble import TAG_AND_BRANCH_SPECIFIED
from edkrepo.common.humble import MIRROR_BEHIND_PRIMARY_REPO, HOOK_NOT_FOUND_ERROR
from edkrepo.common.humble import INCLUDED_URL_LINE, INCLUDED_INSTEAD_OF_LINE, INCLUDED_FILE_NAME
from edkrepo.common.humble import ERROR_WRITING_INCLUDE, MULTIPLE_SOURCE_ATTRIBUTES_SPECIFIED
from edkrepo.common.humble import VERIFY_GLOBAL, VERIFY_ARCHIVED, VERIFY_PROJ, VERIFY_PROJ_FAIL
from edkrepo.common.humble import VERIFY_GLOBAL_FAIL
from edkrepo.common.humble import SUBMODULE_DEINIT_FAILED, BRANCH_COLLIDES_WITH_PARENT_SHA
from edkrepo.common.pathfix import get_actual_path, expanduser
from edkrepo.common.git_version import GitVersion
from project_utils.sparse import BuildInfo, process_sparse_checkout
from edkrepo.config.config_factory import get_workspace_path
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo.config.tool_config import CI_INDEX_FILE_NAME
from edkrepo.config.tool_config import SUBMODULE_CACHE_REPO_NAME
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException
from edkrepo_manifest_parser.edk_manifest import ManifestXml
from edkrepo.common.edkrepo_exception import EdkrepoHookNotFoundException
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
PATCH = "Patch"
REVERT = "Revert"
PATCHSET_CIRCULAR_DEPENDENCY_ERROR = "The PatchSet {} has a circular dependency with another PatchSet"

def clone_repos(args, workspace_dir, repos_to_clone, project_client_side_hooks, config, manifest, global_manifest_path, cache_obj=None):
    try:
        if 'source_manifest_repo' in vars(args).keys():
            src_manifest_repo = find_source_manifest_repo(
                manifest, config['cfg_file'], config['user_cfg_file'], args.source_manifest_repo, False)
        else:
            src_manifest_repo = find_source_manifest_repo(
                manifest, config['cfg_file'], config['user_cfg_file'], None, False)
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

    for repo_to_clone in repos_to_clone:
        clone_utils.clone_single_repository(manifest, repo_to_clone, workspace_dir, global_manifest_path, args, cache_obj)
        
        if global_manifest_directory:
            repo = Repo(os.path.join(workspace_dir, repo_to_clone.root))
            # Install git hooks if there is a manifest repo associated with the manifest being cloned
            install_hooks(project_client_side_hooks, os.path.join(workspace_dir, repo_to_clone.root), repo_to_clone, config, global_manifest_directory)
            # Add the commit template if it exists.
            update_repo_commit_template(workspace_dir, repo, repo_to_clone, global_manifest_directory)

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
    prefix_required = find_git_version() >= GitVersion('2.34.0')
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
                if prefix_required:
                    path = '%(prefix){}'.format(path)
                    section = 'includeIf "gitdir:%(prefix){}/"'.format(gitdir)
                else:
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
        if repo.is_dirty(untracked_files=True, submodules=False):
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

def checkout_repos(verbose, override, repos_to_checkout, workspace_path, manifest, global_manifest_path):
    if not override:
        try:
            check_dirty_repos(manifest, workspace_path)
        except EdkrepoUncommitedChangesException:
            raise EdkrepoUncommitedChangesException(CHECKOUT_UNCOMMITED_CHANGES)
    #check_branches(repos_to_checkout, workspace_path)
    for repo_to_checkout in repos_to_checkout:
        if verbose:
            if repo_to_checkout.patch_set:
                print(CHECKING_OUT_PATCHSET.format(repo_to_checkout.patch_set, repo_to_checkout.root))
            elif repo_to_checkout.branch is not None and repo_to_checkout.commit is None:
                print(CHECKING_OUT_BRANCH.format(repo_to_checkout.branch, repo_to_checkout.root))
            elif repo_to_checkout.commit is not None:
                print(CHECKING_OUT_COMMIT.format(repo_to_checkout.commit, repo_to_checkout.root))
        local_repo_path = os.path.join(workspace_path, repo_to_checkout.root)
        repo = Repo(local_repo_path)

        # Checkout the repo onto the correct patchset/branch/commit/tag if multiple attributes are provided in
        # the source section for the manifest the order of priority is the followiwng 1)patchset 2)commit
        # 3) tag 4)branch with the highest priority attribute provided beinng checked out
        if repo_to_checkout.patch_set:
            try:
                patchset_branch_creation_flow(repo_to_checkout, repo, workspace_path, manifest, global_manifest_path, override)
            except EdkrepoLocalBranchExistsException:
                raise
        else:
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

def patchset_branch_creation_flow(repo, repo_obj, workspace_path, manifest, global_manifest_path, override):
    json_path = os.path.join(workspace_path, "repo")
    json_path = os.path.join(json_path, "patchset_{}.json".format(os.path.basename(repo_obj.working_dir)))
    patchset = manifest.get_patchset(repo.patch_set, repo.remote_name)
    operations_list = manifest.get_patchset_operations(patchset.name, patchset.remote)
    ops = []
    for operations in operations_list:
        for operation in operations:
            ops.append(operation._asdict())

    if repo.patch_set in repo_obj.branches:
        try:
            COLLISION = is_branch_name_collision(json_path, patchset, repo_obj, global_manifest_path, ops, override)
        except EdkrepoLocalBranchExistsException:
            raise
        if COLLISION:
            ui_functions.print_info_msg(COLLISION_DETECTED.format(repo.patch_set))
            create_local_branch(repo.patch_set, patchset, global_manifest_path, manifest, repo_obj)
        else:
            repo_obj.git.checkout(repo.patch_set)
    else:
        create_local_branch(repo.patch_set, patchset, global_manifest_path, manifest, repo_obj)

def is_branch_name_collision(json_path, patchset_obj, repo, global_manifest_path, operations, override):
    repo_name = os.path.basename(repo.working_dir)
    patchset_name = patchset_obj.name
    COLLISION = False
    BRANCH_IN_JSON = False
    for branch in repo.branches:
        if str(branch) == patchset_name:
            if not os.path.isfile(json_path):
                break
            with open(json_path, 'r+') as f:
                data = json.load(f)
                patchset_data = data[repo_name]
                for patchset in patchset_data:
                    if patchset_name == patchset['parent_sha']:
                        # Do not match a patchset branch name against a daisy-chained-patchset parent_sha value
                        continue
                    if patchset_name in patchset.values():
                        BRANCH_IN_JSON = True

                        # detect change in branch
                        head = repo.git.execute(['git', 'rev-parse', patchset_name])
                        if patchset['head_sha'] != head:
                            COLLISION = True

                        # detect change in patch file
                        if patchset['patch_file']:
                            for patch in patchset['patch_file']:
                                patch_file = patch['file_name']
                                hash_of_patch_file = get_hash_of_file(os.path.normpath(os.path.join(global_manifest_path, patch_file)))
                                if patch['hash'] != hash_of_patch_file:
                                    COLLISION = True

                        # detect change in local manifest
                        if patchset['remote'] != patchset_obj.remote or patchset['parent_sha'] != patchset_obj.parent_sha \
                             or patchset['fetch_branch'] != patchset_obj.fetch_branch or operations != patchset['patchset_operations']:
                            COLLISION = True

                        if COLLISION:
                            branch.rename(patchset_name + '_' + time.strftime("%Y/%m/%d_%H_%M_%S"))
                            patchset[patchset_name] = patchset_name + '_' + time.strftime("%Y/%m/%d_%H_%M_%S")
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            return True
    if not BRANCH_IN_JSON:
        if not override:
            raise EdkrepoLocalBranchExistsException(LOCAL_BRANCH_EXISTS.format(patchset_name))
        else:
            return False
    else:
        return False

def patchset_operations_similarity(initial_patchset, new_patchset, initial_manifest, new_manifest):
    return initial_manifest.get_patchset_operations(initial_patchset.name, initial_patchset.remote) \
            == new_manifest.get_patchset_operations(new_patchset.name, new_patchset.remote)

def create_repos(repos_to_create, workspace_path, manifest, global_manifest_path):
    for repo_to_create in repos_to_create:
        local_repo_path = os.path.join(workspace_path, repo_to_create.root)
        repo = Repo(local_repo_path)
        json_path = os.path.join(workspace_path, "repo")
        json_path = os.path.join(json_path, "patchset_{}.json".format(os.path.basename(repo.working_dir)))
        repo_name = os.path.basename(repo.working_dir)
        patch_set = repo_to_create.patch_set
        for branch in repo.branches:
            if str(branch) == patch_set:
                COLLISION = False
                with open(json_path, 'r+') as f:
                    data = json.load(f)
                    patchset_data = data[repo_name]
                    for patch_data in patchset_data:
                        if patch_set in patch_data.values():
                            branch.rename(patch_set + '_' + time.strftime("%Y/%m/%d_%H_%M_%S"))
                            patch_data[patch_set] = patch_set + '_' + time.strftime("%Y/%m/%d_%H_%M_%S")
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            COLLISION = True
                            break
                if COLLISION:
                    patchset = manifest.get_patchset(repo_to_create.patch_set, repo_to_create.remote_name)
                    create_local_branch(patch_set, patchset, global_manifest_path, manifest, repo)

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


def checkout(combination, global_manifest_path, verbose=False, override=False, log=None, cache_obj=None):
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

    # Determine if there is a difference in the sparse states of the two combos
    # sparse_diff = True if there is a difference in sparse enable or if there
    # is a statically defined sparse list for the combo
    sparse_diff = False
    sources_to_check = [(x, y) for x in initial_repo_sources for y in repo_sources if x.root == y.root]
    for source in sources_to_check:
        if source[0].sparse != source[1].sparse:
            sparse_diff = True
        if sparse_diff:
            break
    if set([combo, manifest.general_config.current_combo]).isdisjoint(set([data.combination for data in manifest.sparse_data])) == False :
        if combo != manifest.general_config.current_combo:
            sparse_diff =  True

    # Recompute the sparse checkout if the dynamic sparse list is being used or
    # there is a difference in the sparse settings / static sparse definition
    # between the two combos
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
        checkout_repos(verbose, override, repo_sources, workspace_path, manifest, global_manifest_path)
        current_repos = repo_sources
        # Update the current checkout combo in the manifest only if this
        # combination exists in the manifest
        if combination_is_in_manifest(combo, manifest):
            manifest.write_current_combo(combo)
    except EdkrepoException as e:
        if verbose:
            traceback.print_exc()
        ui_functions.print_error_msg(e)
        print (CHECKOUT_COMBO_UNSUCCESSFULL.format(combo))
        # Return to the initial combo, since there was an issue with cheking out the selected combo
        checkout_repos(verbose, override, initial_repo_sources, workspace_path, manifest, global_manifest_path)
    finally:
        cache_path = None
        if cache_obj is not None:
            cache_path = cache_obj.get_cache_path(SUBMODULE_CACHE_REPO_NAME)
        maintain_submodules(workspace_path, manifest, submodule_combo, verbose, cache_path)
        if sparse_enabled or sparse_diff:
            print(SPARSE_CHECKOUT)
            sparse_checkout(workspace_path, current_repos, manifest)

def get_latest_sha(repo, branch, remote_or_url='origin'):
    if repo is None:
        try:
            ls_remote_output = subprocess.run('git ls-remote {} refs/heads/{}'.format(remote_or_url, branch),
                                               stdout=subprocess.PIPE, universal_newlines=True, shell=True).stdout
        except:
            return None
    else:
        try:
            ls_remote_output = repo.git.ls_remote(remote_or_url, 'refs/heads/{}'.format(branch))
        except:
            return None
    if ls_remote_output == '':
        return None
    output_split = ls_remote_output.split()
    (latest_sha, ref_name) = (output_split[0], output_split[1])
    if ref_name == 'refs/heads/{}'.format(branch):
        return latest_sha
    else:
        return None

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

def update_repo_commit_template(workspace_dir, repo, repo_info, global_manifest_directory):
    # Open the local manifest and get any templates
    manifest = edk_manifest.ManifestXml(os.path.join(workspace_dir, 'repo', 'Manifest.xml'))
    templates = manifest.commit_templates

    #Check for the presence of a globally defined commit template
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
                    if os.path.isfile(current_template):
                        print(COMMIT_TEMPLATE_CUSTOM_VALUE.format(repo_info.remote_name))
                        return
                    else:
                        print(COMMIT_TEMPLATE_NOT_FOUND.format(current_template))
                        print(COMMIT_TEMPLATE_RESETTING_VALUE)

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

def find_git_version():
    git_version_output = subprocess.run('git --version', stdout=subprocess.PIPE, universal_newlines=True, shell=True)
    cur_git_ver_string = git_version_output.stdout
    cur_git_version = GitVersion(cur_git_ver_string)

    return cur_git_version

def get_unique_branch_name(branch_name_prefix, repo):
    branch_names = [x.name for x in repo.heads]
    if branch_name_prefix not in branch_names:
        return branch_name_prefix
    index = 1
    while True:
        branch_name = "{}-{}".format(branch_name_prefix, index)
        if branch_name not in branch_names:
            return branch_name


def get_hash_of_file(file):
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            sha256.update(chunk)

        return sha256.hexdigest()

def create_local_branch(name, patchset, global_manifest_path, manifest_obj, repo):
    for branch in repo.branches:
        if name == str(branch):
            raise EdkrepoBranchExistsException(BRANCH_EXISTS.format(name))

    path = repo.working_tree_dir
    repo_path = os.path.dirname(path)
    path = os.path.join(repo_path, "repo")
    json_path = os.path.join(path, "patchset_{}.json".format(os.path.basename(repo.working_dir)))
    remote_list = manifest_obj.remotes
    operations_list = manifest_obj.get_patchset_operations(patchset.name, patchset.remote)
    REMOTE_IN_REMOTE_LIST = False
    for remote in remote_list:
        if patchset.remote == remote.name:
            REMOTE_IN_REMOTE_LIST = True
            try:
                repo.remotes.origin.fetch(patchset.fetch_branch, progress=GitProgressHandler())
            except:
                raise EdkrepoFetchBranchNotFoundException(FETCH_BRANCH_DOES_NOT_EXIST.format(patchset.fetch_branch))
            parent_patchsets = _list_patchset_ancestors(manifest_obj, patchset)
            _checkout_parent(patchset, name, repo, parent_patchsets)
            try:
                apply_patchset_operations(repo, operations_list, global_manifest_path, remote_list)
                head_sha = repo.git.execute(['git', 'rev-parse', 'HEAD'])
            except (EdkrepoPatchFailedException, EdkrepoRevertFailedException, git.GitCommandError, EdkrepoCherryPickFailedException) as exception:
                print(exception)
                print(CHECKING_OUT_DEFAULT)
                repo.git.checkout(os.path.basename(repo.git.execute(['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'])))
                repo.git.execute(['git', 'branch', '-D', '{}'.format(name)])
                raise exception

    if not REMOTE_IN_REMOTE_LIST:
        raise EdkrepoRemoteNotFoundException(REMOTE_NOT_FOUND.format(patchset.remote))

    ops_list = []
    for operations in operations_list:
        for operation in operations:
            ops_list.append(operation._asdict())

    json_str = {
        patchset.name: name,
        "head_sha": head_sha,
        "remote": patchset.remote,
        "parent_sha": patchset.parent_sha,
        "fetch_branch": patchset.fetch_branch,
        "patchset_operations": ops_list,
        "patch_file": []
    }

    for operations in operations_list:
        for operation in operations:
            if operation.type == "Patch":
                json_str["patch_file"].append({
                        "file_name": operation.file,
                        "hash": get_hash_of_file(os.path.normpath(os.path.join(global_manifest_path, operation.file)))
                    })

    if not os.path.isfile(json_path):
        with open(json_path, 'w') as f:
            json.dump({os.path.basename(repo.working_dir): [json_str]}, f, indent=4)
        f.close()
    else:
        with open(json_path, "r+") as f:
            data = json.load(f)
            data[os.path.basename(repo.working_dir)].append(json_str)
            f.seek(0)
            json.dump(data, f, indent=4)
        f.close()

def _list_patchset_ancestors(manifest, patchset):
    parent_patchsets = []
    try:
        parent_patchsets.append(manifest.get_patchset(patchset.parent_sha, patchset.remote))
        while True:
            # Allow daisy-chaining PatchSet.  Continue until KeyError is caught.
            parent_patchsets.append(manifest.get_patchset(parent_patchsets[-1].parent_sha, parent_patchsets[-1].remote))
            if parent_patchsets.count(parent_patchsets[-1]) > 1:
                # Do not continue to branch creation step if a circular dependency is detected between multiple PatchSet.
                raise ValueError(PATCHSET_CIRCULAR_DEPENDENCY_ERROR.format(parent_patchsets[-1]))
    except KeyError:
        return parent_patchsets

def _checkout_parent(patchset, name, repo, parent_patchsets):
    if parent_patchsets:
        base_parent_sha = parent_patchsets[-1].parent_sha
    else:
        base_parent_sha = patchset.parent_sha

    if base_parent_sha in repo.tags:
        # tag names are prioritized over branch names
        repo.git.checkout("refs/tags/{}".format(base_parent_sha), b=name)
    elif base_parent_sha in repo.heads:
        # PatchSet should not use a branch name as the base parent_sha.
        raise EdkrepoBranchCollidesWithParentShaException(BRANCH_COLLIDES_WITH_PARENT_SHA)
    else:
        repo.git.checkout(base_parent_sha, b=name)

def is_merge_conflict(repo):
    status = repo.git.status(porcelain=True).split()
    return True if 'UU' in status else False

def apply_patchset_operations(repo, operations_list, global_manifest_path, remote_list):
    for operations in operations_list:
        for operation in operations:
            if operation.type == PATCH:
                path = os.path.normpath(os.path.join(global_manifest_path, operation.file))
                if os.path.isfile(path):
                    try:
                        repo.git.execute(['git', 'am', path, '--ignore-whitespace'])
                    except:
                        repo.git.execute(['git', 'am', '--abort'])
                        raise EdkrepoPatchFailedException(APPLYING_PATCH_FAILED.format(operation.file))
                else:
                    raise EdkrepoPatchNotFoundException(PATCHFILE_DOES_NOT_EXIST.format(operation.file))
            elif operation.type == REVERT:
                try:
                    repo.git.execute(['git', 'revert', operation.sha, '--no-edit'])
                except:
                    if is_merge_conflict(repo):
                        repo.git.execute(['git', 'revert', '--abort'])
                    raise EdkrepoRevertFailedException(APPLYING_REVERT_FAILED.format(operation.sha))
            else:
                if operation.source_remote:
                    REMOTE_FOUND = False
                    for remote in remote_list:
                        if operation.source_remote == remote.name:
                            REMOTE_FOUND = True
                            try:
                                repo.git.execute(['git', 'remote', 'add', operation.source_remote, remote.url])
                            except :
                                raise EdkrepoRemoteAddException(REMOTE_CREATION_FAILED.format(operation.source_remote))
                            try:
                                repo.git.execute(['git', 'fetch', operation.source_remote, operation.source_branch])
                            except:
                                raise EdkrepoFetchBranchNotFoundException(FETCH_BRANCH_DOES_NOT_EXIST.format(operation.source_branch))
                            try:
                                repo.git.execute(['git', 'cherry-pick', operation.sha, '-x'])
                            except:
                                if is_merge_conflict(repo):
                                    repo.git.execute(['git', 'cherry-pick', '--abort'])
                                raise EdkrepoCherryPickFailedException(APPLYING_CHERRY_PICK_FAILED.format(operation.sha))
                            try:
                                repo.git.execute(['git', 'remote', 'remove', operation.source_remote])
                            except:
                                raise EdkrepoRemoteRemoveException(REMOVE_REMOTE_FAILED.format(operation.source_remote))
                    if not REMOTE_FOUND:
                        raise EdkrepoRemoteNotFoundException(REMOTE_NOT_FOUND.format(operation.source_remote))
                else:
                    try:
                        repo.remotes.origin.fetch(operation.source_branch)
                    except:
                        raise EdkrepoFetchBranchNotFoundException(FETCH_BRANCH_DOES_NOT_EXIST.format(operation.source_branch))
                    try:
                        repo.git.execute(['git', 'cherry-pick', operation.sha, '-x'])
                    except:
                        if is_merge_conflict(repo):
                            repo.git.execute(['git', 'cherry-pick', '--abort'])
                        raise EdkrepoCherryPickFailedException(APPLYING_CHERRY_PICK_FAILED.format(operation.sha))
