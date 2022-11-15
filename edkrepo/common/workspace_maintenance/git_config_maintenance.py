#!/usr/bin/env python3
#
## @file
# git_config_maintenance.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import re
import sys

import git

from edkrepo.common.pathfix import expanduser
from edkrepo.common.common_repo_functions import find_git_version
from edkrepo.common.git_version import GitVersion

def clean_git_globalconfig():
    global_gitconfig_path = os.path.normpath(expanduser("~/.gitconfig"))
    prefix_required = find_git_version() >= GitVersion('2.34.0')
    with git.GitConfigParser(global_gitconfig_path, read_only=False) as git_globalconfig:
        if prefix_required:
            includeif_regex = re.compile('^includeIf "gitdir:%\(prefix\)(/.+)/"$')
            includeif_regex_old = re.compile('^includeIf "gitdir:(/.+)/"$')
        else:
            includeif_regex_old = re.compile('^includeIf "gitdir:%\(prefix\)(/.+)/"$')
            includeif_regex = re.compile('^includeIf "gitdir:(/.+)/"$')
        for section in git_globalconfig.sections():
            data = includeif_regex.match(section)
            if data:
                gitconfig_path = git_globalconfig.get(section, 'path')
                if _path_is_new_style(gitconfig_path):
                    gitconfig_path = _remove_new_style_prefix(gitconfig_path)
                if sys.platform == "win32":
                    gitconfig_path = gitconfig_path[1:]
                gitconfig_path = os.path.normpath(gitconfig_path)
                if not os.path.isfile(gitconfig_path):
                    git_globalconfig.remove_section(section)
            data_old = includeif_regex_old.match(section)
            if data_old:
                git_globalconfig.remove_section(section)

def set_long_path_support():
    global_git_config_path = os.path.normpath(expanduser("~/.gitconfig"))
    with git.GitConfigParser(global_git_config_path, read_only=False) as git_globalconfig:
        if 'core' not in git_globalconfig.sections():
            git_globalconfig.add_section('core')
        git_globalconfig.set('core', 'longpaths', 'true')

def _path_is_new_style(path):
    return path.startswith('%(prefix)')

def _remove_new_style_prefix(path):
    return path.split('%(prefix)')[1]
