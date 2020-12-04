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

def clean_git_globalconfig():
    global_gitconfig_path = os.path.normpath(expanduser("~/.gitconfig"))
    with git.GitConfigParser(global_gitconfig_path, read_only=False) as git_globalconfig:
        includeif_regex = re.compile('^includeIf "gitdir:(/.+)/"$')
        for section in git_globalconfig.sections():
            data = includeif_regex.match(section)
            if data:
                gitrepo_path = data.group(1)
                gitconfig_path = git_globalconfig.get(section, 'path')
                if sys.platform == "win32":
                    gitrepo_path = gitrepo_path[1:]
                    gitconfig_path = gitconfig_path[1:]
                gitrepo_path = os.path.normpath(gitrepo_path)
                gitconfig_path = os.path.normpath(gitconfig_path)
                (repo_manifest_path, _) = os.path.split(gitconfig_path)
                repo_manifest_path = os.path.join(repo_manifest_path, "Manifest.xml")
                if not os.path.isdir(gitrepo_path) and not os.path.isfile(gitconfig_path):
                    if not os.path.isfile(repo_manifest_path):
                        git_globalconfig.remove_section(section)