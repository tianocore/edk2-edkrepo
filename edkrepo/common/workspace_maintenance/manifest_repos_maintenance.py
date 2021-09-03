#!/usr/bin/env python3
#
## @file
# manifest_repos_maintenance.py
#
# Copyright (c) 2017 - 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import traceback
import shutil

import git
from git import Repo

import edkrepo.config.config_factory as cfg
from edkrepo.config.tool_config import CI_INDEX_FILE_NAME
from edkrepo.common.edkrepo_exception import EdkrepoUncommitedChangesException, EdkrepoInvalidParametersException
from edkrepo.common.edkrepo_exception import EdkrepoManifestNotFoundException
from edkrepo.common.progress_handler import GitProgressHandler
import edkrepo.common.workspace_maintenance.humble.manifest_repos_maintenance_humble as humble
from edkrepo.common.workspace_maintenance.workspace_maintenance import generate_name_for_obsolete_backup
from edkrepo.common.workspace_maintenance.workspace_maintenance import case_insensitive_single_match
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml

def pull_single_manifest_repo(url, branch, local_path, reset_hard=False):
    '''
    Clones or syncs a single global manifest repository as defined in either
    the edkrepo.cfg or the edkrepo_user.cfg
    '''
    # If a relative path is used join to the edkrepo global data directory path
    if not os.path.isabs(local_path):
        local_path = os.path.join(cfg.get_edkrepo_global_data_directory(), local_path)
    # Clone the repository if it does not exist locally
    if not os.path.exists(local_path):
        print(humble.CLONE_SINGLE_MAN_REPO.format(local_path, url))
        repo = Repo.clone_from(url, local_path, progress=GitProgressHandler(), branch=branch)
    # Sync the repository if it exists locally
    else:
        repo = Repo(local_path)
        if url in repo.remotes['origin'].urls:
            if repo.is_dirty(untracked_files=True) and not reset_hard:
                raise EdkrepoUncommitedChangesException(humble.SINGLE_MAN_REPO_DIRTY.format(local_path))
            elif repo.is_dirty(untracked_files=True) and reset_hard:
                repo.git.reset('--hard')
            print(humble.SYNC_SINGLE_MAN_REPO.format(local_path))
            if repo.active_branch.name != branch:
                print(humble.SINGLE_MAN_REPO_NOT_CFG_BRANCH.format(repo.active_branch.name, local_path))
                print(humble.SINGLE_MAN_REPO_CHECKOUT_CFG_BRANCH.format(branch))
                repo.git.checkout(branch)
            repo.remotes.origin.pull()
        # If the URL specified for this manifest repo has moved back up the existing
        # local copy and clone the new repository
        else:
            new_path = generate_name_for_obsolete_backup(local_path)
            new_path = os.path.join(os.path.dirname(local_path), new_path)
            print(humble.SINGLE_MAN_REPO_MOVED.format(new_path))
            shutil.move(local_path, new_path)
            print (humble.CLONE_SINGLE_MAN_REPO.format(local_path, url))
            repo = Repo.clone_from(url, local_path, progress=GitProgressHandler(), branch=branch)

def pull_all_manifest_repos(edkrepo_cfg, edkrepo_user_cfg, reset_hard=False):
    '''
    Clones or syncs all global manifest repositories defined in both the
    edkrepo_cfg and the edkrepo_user.cfg)
    '''
    cfg_man_repos = []
    user_cfg_man_repos = []
    conflicts = []
    cfg_man_repos, user_cfg_man_repos, conflicts = list_available_manifest_repos(edkrepo_cfg, edkrepo_user_cfg)
    for conflict in conflicts:
        print(humble.CONFLICT_NO_CLONE.format(conflict))
    for repo in cfg_man_repos:
        pull_single_manifest_repo(edkrepo_cfg.get_manifest_repo_url(repo),
                                  edkrepo_cfg.get_manifest_repo_branch(repo),
                                  edkrepo_cfg.get_manifest_repo_local_path(repo),
                                  reset_hard)
    for repo in user_cfg_man_repos:
        pull_single_manifest_repo(edkrepo_user_cfg.get_manifest_repo_url(repo),
                                  edkrepo_user_cfg.get_manifest_repo_branch(repo),
                                  edkrepo_user_cfg.get_manifest_repo_local_path(repo),
                                  reset_hard)


def detect_manifest_repo_conflicts_duplicates(edkrepo_cfg, edkrepo_user_cfg):
    '''
    Determines whether there is are conflicting or duplicated manifest
    repositories listed in the edkrepo.cfg and the edkrepo_user.cfg.
    '''
    conflicts = []
    duplicates = []
    if not edkrepo_user_cfg.manifest_repo_list:
        return conflicts, duplicates
    else:
        config_repos = set(edkrepo_cfg.manifest_repo_list)
        user_cfg_repos = set(edkrepo_user_cfg.manifest_repo_list)
    if config_repos.isdisjoint(user_cfg_repos):
        return conflicts, duplicates
    else:
        for repo in config_repos.intersection(user_cfg_repos):
            if edkrepo_cfg.get_manifest_repo_url(repo) != edkrepo_user_cfg.get_manifest_repo_url(repo):
                conflicts.append(repo)
            elif edkrepo_cfg.get_manifest_repo_branch(repo) != edkrepo_user_cfg.get_manifest_repo_branch(repo):
                conflicts.append(repo)
            elif edkrepo_cfg.get_manifest_repo_local_path(repo) != edkrepo_user_cfg.get_manifest_repo_local_path(repo):
                conflicts.append(repo)
            else:
                duplicates.append(repo)
    return conflicts, duplicates

def list_available_manifest_repos(edkrepo_cfg, edkrepo_user_cfg):
    '''
    Checks for conflicts/duplicates within all manifest repositories defined in
    both the edkrepo.cfg and the edkrepo_user.cfg and resturns a list of available
    manifest_repos for each and a list of conflicting manifest repository entries.
    '''
    cfg_man_repos = []
    user_cfg_man_repos = []
    conflicts, duplicates = detect_manifest_repo_conflicts_duplicates(edkrepo_cfg, edkrepo_user_cfg)
    if not conflicts and not duplicates:
        cfg_man_repos.extend(edkrepo_cfg.manifest_repo_list)
        user_cfg_man_repos.extend(edkrepo_user_cfg.manifest_repo_list)
    elif conflicts:
        for conflict in conflicts:
            # In the case of a conflict do not pull conflicting repo
            cfg_man_repos.extend(edkrepo_cfg.manifest_repo_list)
            cfg_man_repos.remove(conflict)
            user_cfg_man_repos.extend(edkrepo_user_cfg.manifest_repo_list)
            user_cfg_man_repos.remove(conflict)
    elif duplicates:
        for duplicate in duplicates:
            # the duplicate needs to be ignored in on of the repo lists so it is
            # not cloned/pulled twice
            cfg_man_repos.extend(edkrepo_cfg.manifest_repo_list)
            user_cfg_man_repos.extend(edkrepo_user_cfg.manifest_repo_list)
            user_cfg_man_repos.remove(duplicate)
    return cfg_man_repos, user_cfg_man_repos, conflicts


def find_project_in_single_index (project, index_file, manifest_dir):
    '''
    Finds a project in a single global manifest repositories index file. If found
    returns (True, path to file) if not returns (False, None)
    '''
    global_manifest_path = None
    try:
        proj_name = case_insensitive_single_match(project, index_file.project_list)
    except:
        proj_name = None
    if proj_name is None:
        try:
            proj_name = case_insensitive_single_match(project, index_file.archived_project_list)
        except:
            proj_name = None
    if proj_name:
        ci_index_xml_rel_path = os.path.normpath(index_file.get_project_xml(proj_name))
        global_manifest_path = os.path.join(manifest_dir, ci_index_xml_rel_path)
        return True, global_manifest_path
    else:
        return False, global_manifest_path


def find_project_in_all_indices (project, edkrepo_cfg, edkrepo_user_cfg, except_msg_man_repo, except_msg_not_found, man_repo=None):
    '''
    Finds the project in all manifest repositories listed in the edkrepo.efg and
    edkrepo_user.cfg. If a project with the same name is found uses man_repo to select
    the correct entry
    '''
    cfg_man_repos, user_cfg_man_repos, conflicts = list_available_manifest_repos(edkrepo_cfg, edkrepo_user_cfg)
    projects = {}
    for repo in cfg_man_repos:
        manifest_dir = edkrepo_cfg.manifest_repo_abs_path(repo)
        index_file = CiIndexXml(os.path.join(manifest_dir, CI_INDEX_FILE_NAME))
        found, man_path = find_project_in_single_index(project, index_file, manifest_dir)
        if found:
            projects[repo] = ('edkrepo_cfg', man_path)
    for repo in user_cfg_man_repos:
        manifest_dir = edkrepo_user_cfg.manifest_repo_abs_path(repo)
        index_file = CiIndexXml(os.path.join(manifest_dir, CI_INDEX_FILE_NAME))
        found, man_path = find_project_in_single_index(project, index_file, manifest_dir)
        if found:
            projects[repo] = ('edkrepo_user_cfg', man_path)
    if len(projects.keys()) == 1:
        repo = list(projects.keys())[0]
        return repo, projects[repo][0], projects[repo][1]
    elif len(projects.keys()) > 1 and man_repo:
        try:
            return man_repo, projects[man_repo][0], projects[man_repo][1]
        except KeyError:
            raise EdkrepoInvalidParametersException(except_msg_man_repo)
    elif os.path.isabs(project):
        manifest = ManifestXml(project)
        try:
            found_manifest_repo, found_cfg, found_project = find_project_in_all_indices(manifest.project_info.codename,
                                                                                        edkrepo_cfg,
                                                                                        edkrepo_user_cfg,
                                                                                        except_msg_man_repo,
                                                                                        except_msg_not_found,
                                                                                        man_repo)
            return found_manifest_repo, found_cfg, project
        except EdkrepoManifestNotFoundException:
            return None, None, project
    elif os.path.isfile(os.path.join(os.getcwd(), project)):
        manifest = ManifestXml(os.path.join(os.getcwd(), project))
        try:
            found_manifest_repo, found_cfg, found_project = find_project_in_all_indices(manifest.project_info.codename,
                                                                                        edkrepo_cfg,
                                                                                        edkrepo_user_cfg,
                                                                                        except_msg_man_repo,
                                                                                        except_msg_not_found,
                                                                                        man_repo)
            return found_manifest_repo, found_cfg, project
        except EdkrepoManifestNotFoundException:
            return None, None, os.path.join(os.getcwd(), project)
    elif not os.path.dirname(project):
        for repo in cfg_man_repos:
            if (man_repo and (repo == man_repo)) or not man_repo:
                for dirpath, dirname, filenames in os.walk(edkrepo_cfg.manifest_repo_abs_path(repo)):
                    if project in filenames:
                        return repo, 'edkrepo_cfg', os.path.join(dirpath, project)
        for repo in user_cfg_man_repos:
            if (man_repo and (repo == man_repo)) or not man_repo:
                for dirpath, dirname, filenames in os.walk(edkrepo_user_cfg.manifest_repo_abs_path(repo)):
                    if project in filenames:
                        return repo, 'edkrepo_user_cfg', os.path.join(dirpath, project)
        raise EdkrepoManifestNotFoundException(humble.PROJ_NOT_IN_REPO.format(project))
    else:
        raise EdkrepoManifestNotFoundException(humble.PROJ_NOT_IN_REPO.format(project))


def find_source_manifest_repo(project_manifest, edkrepo_cfg, edkrepo_user_cfg, man_repo=None, update_source_manifest_repo=True):
    '''
    Finds the source manifest repo for a given project.
    '''
    if project_manifest.general_config.source_manifest_repo:
        source_manifest_repo = project_manifest.general_config.source_manifest_repo
        cfg_manifest_repos, user_cfg_manifest_repos, _ = list_available_manifest_repos(edkrepo_cfg, edkrepo_user_cfg)
        manifest_dir = None
        if source_manifest_repo in cfg_manifest_repos:
            manifest_dir = edkrepo_cfg.manifest_repo_abs_path(source_manifest_repo)
        elif source_manifest_repo in user_cfg_manifest_repos:
            manifest_dir = edkrepo_user_cfg.manifest_repo_abs_path(source_manifest_repo)
        if manifest_dir is not None:
            index_file_path = os.path.join(manifest_dir, CI_INDEX_FILE_NAME)
            if os.path.isfile(index_file_path):
                index_file = CiIndexXml(index_file_path)
                found, _ = find_project_in_single_index(project_manifest.project_info.codename, index_file, manifest_dir)
                if found:
                    return source_manifest_repo

    try:
        src_man_repo, _, _ = find_project_in_all_indices(project_manifest.project_info.codename,
                                                        edkrepo_cfg,
                                                        edkrepo_user_cfg,
                                                        humble.PROJ_NOT_IN_REPO.format(project_manifest.project_info.codename),
                                                        humble.SOURCE_MANIFEST_REPO_NOT_FOUND.format(project_manifest.project_info.codename),
                                                        man_repo)
    except EdkrepoManifestNotFoundException:
        src_man_repo = None
    if src_man_repo is not None and update_source_manifest_repo:
        project_manifest.write_source_manifest_repo(src_man_repo)
    return src_man_repo

def pull_workspace_manifest_repo(project_manifest, edkrepo_cfg, edkrepo_user_cfg, man_repo=None, reset_hard=False):
    '''
    Pulls only the global manifest repo for the current workspace.
    '''
    src_man_repo = find_source_manifest_repo(project_manifest, edkrepo_cfg, edkrepo_user_cfg, man_repo)
    config_repos, user_config_repos, conflicts = list_available_manifest_repos(edkrepo_cfg, edkrepo_user_cfg)
    if src_man_repo in config_repos:
        pull_single_manifest_repo(edkrepo_cfg.get_manifest_repo_url(src_man_repo),
                                  edkrepo_cfg.get_manifest_repo_branch(src_man_repo),
                                  edkrepo_cfg.get_manifest_repo_local_path(src_man_repo),
                                  reset_hard)
    elif src_man_repo in user_config_repos:
        pull_single_manifest_repo(edkrepo_user_cfg.get_manifest_repo_url(src_man_repo),
                                  edkrepo_user_cfg.get_manifest_repo_branch(src_man_repo),
                                  edkrepo_user_cfg.get_manifest_repo_local_path(src_man_repo),
                                  reset_hard)
    elif src_man_repo in conflicts:
        raise EdkrepoInvalidParametersException(humble.CONFLICT_NO_CLONE.format(src_man_repo))
