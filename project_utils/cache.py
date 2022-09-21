#!/usr/bin/env python3
#
## @file
# cache.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
from collections import namedtuple
import os
import shutil

from git import Repo

import edkrepo.common.ui_functions as ui_functions
from edkrepo.common.progress_handler import GitProgressHandler
from project_utils.project_utils_strings import CACHE_ADD_REMOTE, CACHE_ADDING_REPO, CACHE_CHECK_ROOT_DIR
from project_utils.project_utils_strings import CACHE_FAILED_TO_CLOSE, CACHE_FAILED_TO_OPEN, CACHE_FETCH_REMOTE
from project_utils.project_utils_strings import CACHE_REMOTE_EXISTS, CACHE_REMOVE_REPO, CACHE_REPO_EXISTS

CacheInfo = namedtuple('CacheInfo', ['path', 'remote', 'url'])


class RepoCache(object):
    """
    Provides basic management of a cache repo.
    """
    def __init__(self, path):
        self._cache_root_path = path
        self._repos = {}

    def _create_name(self, url_or_name):
        """
        Used to create consistent repo and remote names
        """
        dir_name = url_or_name.split('/')[-1]
        if not dir_name.endswith('.git'):
            dir_name += '.git'
        return dir_name

    def _get_repo_path(self, dir_name):
        return os.path.join(self._cache_root_path, dir_name)

    def _get_repo(self, dir_name):
        """
        Returns the git repo object for the cache repo.

        Raises FileNotFoundError if the cache directory does not exist.
        Raises IOError if the repo cannot be opened
        """
        repo_path = self._get_repo_path(dir_name)
        if not os.path.isdir(repo_path):
            raise FileNotFoundError
        try:
            repo = Repo(repo_path)
        except Exception:
            raise IOError
        return repo

    def _get_cache_dirs(self):
        if not os.path.isdir(self._cache_root_path):
            raise FileNotFoundError
        return [x for x in os.listdir(self._cache_root_path) if os.path.isdir(self._get_repo_path(x))]

    def _add_and_fetch_remote(self, repo, remote_name, url, verbose=False):
        ui_functions.print_info_msg(CACHE_ADD_REMOTE.format(remote_name, url), extra={'verbose': verbose})
        repo.create_remote(remote_name, url)
        ui_functions.print_info_msg(CACHE_FETCH_REMOTE.format(remote_name, url), extra={'verbose': verbose})
        repo.remotes[remote_name].fetch(progress=GitProgressHandler())

    def open(self, verbose=False):
        """
        Opens all cache repos.

        Raises FileNotFoundError if the cache directory does not exist.
        """
        if not self._repos:
            if not os.path.isdir(self._cache_root_path):
                ui_functions.print_info_msg(CACHE_CHECK_ROOT_DIR.format(self._cache_root_path), extra={'verbose': verbose})
                os.makedirs(self._cache_root_path)

            for dir_name in self._get_cache_dirs():
                try:
                    self._repos[dir_name] = self._get_repo(dir_name)
                except Exception:
                    ui_functions.print_error_msg(CACHE_FAILED_TO_OPEN.format(dir_name), extra={'verbose': verbose})

    def close(self, verbose=False):
        """
        Closes all cache repos.
        """
        for dir_name in self._repos:
            try:
                self._repos[dir_name].close()
            except Exception:
                ui_functions.print_error_msg(CACHE_FAILED_TO_CLOSE.format(dir_name), extra={'verbose': verbose})
        self._repos = {}

    def get_cache_path(self, url_or_name):
        dir_name = self._create_name(url_or_name)
        if dir_name not in self._repos:
            return None
        return self._get_repo_path(dir_name)

    def get_cache_info(self, verbose=False):
        """
        Returns a list of remotes currently configured in the cache.

        Raises FileNotFoundError if the cache repo is not open.
        """
        ret_val = []
        for dir_name in self._repos:
            for remote in self._repos[dir_name].remotes:
                ret_val.append(CacheInfo(self._get_repo_path(dir_name), remote.name, remote.url))
        return ret_val

    def delete_cache_root(self, verbose=False):
        """
        Deletes the cache root directory and all caches.
        """
        if os.path.isdir(self._cache_root_path):
            if self._repos:
                self.close()
            shutil.rmtree(self._cache_root_path, ignore_errors=True)

    def add_repo(self, url=None, name=None, verbose=False):
        """
        Adds a repo to the cache if it does not already exist.

        """
        remote_name = None
        if url is None and name is None:
            raise ValueError
        elif name is not None:
            dir_name = self._create_name(name)
        else:
            dir_name = self._create_name(url)
        if url is not None:
            remote_name = self._create_name(url)
        repo_path = self._get_repo_path(dir_name)

        if dir_name in self._repos:
            ui_functions.print_info_msg(CACHE_REPO_EXISTS.format(dir_name), extra={'verbose': verbose})
        else:
            ui_functions.print_info_msg(CACHE_ADDING_REPO.format(dir_name), extra={'verbose': verbose})
            os.makedirs(repo_path)
            self._repos[dir_name] = Repo.init(repo_path, bare=True)

        if remote_name is not None and remote_name not in self._repos[dir_name].remotes:
            self._add_and_fetch_remote(self._get_repo(dir_name), remote_name, url)
        return dir_name

    def remove_repo(self, url=None, name=None, verbose=False):
        """
        Removes a remote from the cache repo if it exists

        Raises FileNotFoundError if the cache repo is not open.
        """
        if url is None and name is None:
            raise ValueError
        elif name is not None:
            dir_name = self._create_name(name)
        else:
            dir_name = self._create_name(url)
        if dir_name not in self._repos:
            return
        ui_functions.print_info_msg(CACHE_REMOVE_REPO.format(dir_name), extra={'verbose': verbose})
        self._repos.pop(dir_name).close()
        shutil.rmtree(os.path.join(self._cache_root_path, dir_name), ignore_errors=True)

    def add_remote(self, url, name, verbose=False):
        remote_name = self._create_name(url)
        dir_name = self._create_name(name)
        if dir_name not in self._repos:
            raise ValueError
        repo = self._get_repo(dir_name)
        if remote_name in repo.remotes:
            ui_functions.print_info_msg(CACHE_REMOTE_EXISTS.format(remote_name), extra={'verbose': verbose})
            return
        self._add_and_fetch_remote(repo, remote_name, url, verbose)

    def remove_remote(self, url, name, verbose=False):
        remote_name = self._create_name(url)
        dir_name = self._create_name(name)
        if dir_name not in self._repos:
            raise ValueError
        repo = self._get_repo(dir_name)
        if remote_name not in repo.remotes:
            raise IndexError
        repo.remove_remote(repo.remotes[remote_name])

    def update_cache(self, url_or_name=None, verbose=False):
        if not self._repos:
            raise FileNotFoundError
        repo_dirs = self._repos.keys()

        if url_or_name is not None:
            dir_name = self._create_name(url_or_name)
            if dir_name in self._repos:
                repo_dirs = [dir_name]
            else:
                return

        for dir_name in repo_dirs:
            try:
                repo = self._get_repo(dir_name)
            except Exception:
                ui_functions.print_error_msg(CACHE_FAILED_TO_OPEN.format(dir_name))
                continue
            for remote in repo.remotes:
                ui_functions.print_error_msg(CACHE_FETCH_REMOTE.format(dir_name, remote.url), extra={'verbose': verbose})
                remote.fetch(progress=GitProgressHandler())

    def clean_cache(self, verbose=False):
        raise NotImplementedError
