#!/usr/bin/env python3
#
## @file
# manifest_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.manifest_args as arguments
import edkrepo.commands.humble.manifest_humble as humble
from edkrepo.common.edkrepo_exception import EdkrepoWorkspaceInvalidException, EdkrepoManifestNotFoundException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_all_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_project_in_single_index
from edkrepo.config.config_factory import get_workspace_manifest
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml
import edkrepo_manifest_parser.edk_manifest_validation as manifest_validation


class ManifestCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'manifest'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'archived',
                     'short-name': 'a',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.ARCHIVED_HELP})
        return metadata

    def run_command(self, args, config):
        print()
        cfg_file = config['cfg_file']
        user_cfg = config['user_cfg_file']
        cfg_man_repos, user_cfg_man_repos, conflicts = list_available_manifest_repos(cfg_file, user_cfg)
        man_repos = {}

        pull_all_manifest_repos(cfg_file, user_cfg, False)

        # Get paths to the global manifest dirs and their index files
        for repo in cfg_man_repos:
            global_manifest_directory = cfg_file.manifest_repo_abs_path(repo)
            index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
            man_repos[repo] = (global_manifest_directory, index_path, cfg_file.get_manifest_repo_url(repo), cfg_file.get_manifest_repo_branch(repo))
        for repo in user_cfg_man_repos:
            global_manifest_directory = user_cfg.manifest_repo_abs_path(repo)
            index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')
            man_repos[repo] = (global_manifest_directory, index_path, cfg_file.get_manifest_repo_url(repo), cfg_file.get_manifest_repo_branch(repo))

        try:
            wkspc_manifest = get_workspace_manifest()
            current_project = wkspc_manifest.project_info.codename
            src_man_repo = find_source_manifest_repo(wkspc_manifest, cfg_file, user_cfg, None)
        except EdkrepoWorkspaceInvalidException:
            current_project = None
            src_man_repo = None
        except EdkrepoManifestNotFoundException:
            src_man_repo = None


        for repo in man_repos.keys():
            print()
            print(humble.MANIFEST_REPO.format(repo))
            if args.verbose:
                print(humble.MANIFEST_REPO_PATH.format(man_repos[repo][0]))
                print(humble.MANIFEST_REPO_URL.format(man_repos[repo][2]))
                print(humble.MANIFEST_REPO_BRANCH.format(man_repos[repo][3]))
            print()

            ci_index_xml = CiIndexXml(man_repos[repo][1])

            for project in ci_index_xml.project_list:
                index_entries = []
                index_entries = manifest_validation.ValidateManifest(None).list_entries(project, ci_index_xml.project_list)
                if len(index_entries) > 1:
                    print(humble.DUPLICATE_PROJECTS_DETECTED.format(project))

            print(humble.PROJECTS)
            for project in sorted(ci_index_xml.project_list):
                if (project == current_project and src_man_repo == repo) or (not src_man_repo and project == current_project):
                    print(humble.CURRENT_PROJECT.format(project))
                else:
                    print(humble.SINGLE_PROJECT.format(project))
                try:
                    proj_manifest = ManifestXml(find_project_in_single_index(project, ci_index_xml, man_repos[repo][0])[1])
                    if args.verbose:
                        self.verbose_project_data(project, proj_manifest, ci_index_xml)
                except Exception as e:
                    print(humble.BAD_MANIFEST)
                if args.verbose:
                    self.verbose_project_data(project, proj_manifest, ci_index_xml)

            if args.archived:
                for project in sorted(ci_index_xml.archived_project_list):
                    if project == current_project:
                        print(humble.CURRENT_PROJECT_ARCHIVED.format(project))
                    else:
                        print(humble.ARCHIVED_PROJECT.format(project))
                    try:
                        proj_manifest = ManifestXml(find_project_in_single_index(project, ci_index_xml, man_repos[repo][0])[1])
                        if args.verbose:
                            self.verbose_project_data(project, proj_manifest, ci_index_xml)
                    except Exception as e:
                        print(humble.BAD_MANIFEST)
    
    def verbose_project_data(self, project, proj_manifest, ci_index_xml):
        print(humble.MANIFEST_FILE_PATH.format(ci_index_xml.get_project_xml(project)))
        print(humble.DEV_LEAD.format(' '.join(x for x in proj_manifest.project_info.dev_leads)))
        print(humble.COMBOS.format(' '.join(x.name for x in proj_manifest.combinations)))
