#!/usr/bin/env python3
#
## @file
# common_cache_functions.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from edkrepo.config.config_factory import get_edkrepo_global_data_directory
from edkrepo.config.tool_config import SUBMODULE_CACHE_REPO_NAME
from project_utils.cache import RepoCache
from edkrepo.common.logger import get_logger

logger = get_logger()

def get_global_cache_directory(config):
    if config['user_cfg_file'].caching_state:
        return os.path.join(get_edkrepo_global_data_directory(), '.cache')
    return None


def get_repo_cache_obj(config):
    cache_obj = None
    cache_directory = get_global_cache_directory(config)
    if cache_directory is not None:
        cache_obj = RepoCache(cache_directory)
        cache_obj.open()
    return cache_obj


def add_missing_cache_repos(cache_obj, manifest, verbose=False):
    logger.info('Adding and fetching new remotes... (this could take a while)')
    for remote in manifest.remotes:
        cache_obj.add_repo(url=remote.url, verbose=verbose)
    alt_submodules = manifest.submodule_alternate_remotes
    if alt_submodules:
        logger.info('Adding and fetching new submodule remotes... (this could also take a while)')
        cache_obj.add_repo(name=SUBMODULE_CACHE_REPO_NAME, verbose=verbose)
        for alt in alt_submodules:
            cache_obj.add_remote(alt.alternate_url, SUBMODULE_CACHE_REPO_NAME, verbose)
