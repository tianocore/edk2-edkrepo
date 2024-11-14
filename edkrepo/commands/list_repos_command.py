#!/usr/bin/env python3
#
## @file
# list_repos_command.py
#
# Copyright (c) 2019 - 2023, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import collections
from itertools import zip_longest
import json
import os
import sys

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.list_repos_args as arguments
import edkrepo.commands.humble.list_repos_humble as humble
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoManifestInvalidException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import pull_all_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.config.tool_config import CI_INDEX_FILE_NAME
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml

class ListReposCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()
        self.repo_names = None

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'list-repos'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name': 'repos',
                     'positional': False,
                     'required': False,
                     'action': 'store',
                     'nargs': '+',
                     'help-text': arguments.REPOS_HELP})
        args.append({'name': 'archived',
                     'short-name': 'a',
                     'positional': False,
                     'required': False,
                     'help-text': arguments.ARCHIVED_HELP})
        args.append({'name': 'format',
                     'positional': False,
                     'required': False,
                     'action': 'store',
                     'nargs': 1,
                     'help-text': arguments.FORMAT_HELP})
        return metadata

    def run_command(self, args, config):
        json_output = False
        if args.format is not None:
            if args.format[0] not in ['text', 'json']:
                raise EdkrepoInvalidParametersException(humble.FORMAT_TYPE_INVALID)
            if args.format[0] == 'json':
                json_output = True
        stdout_backup = None

        #If the user selected json output than suppress all debug messages
        #coming from the manifest parser so that the output from edkrepo will
        #be a machine parsable json string
        if json_output:
            devnull = open(os.devnull, 'w')
            sys.stdout.flush()
            stdout_backup = sys.stdout
            sys.stdout = devnull
        try:
            print()
            pull_all_manifest_repos(config['cfg_file'], config['user_cfg_file'])
            print()

            cfg_manifest_repos, user_config_manifest_repos, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfg_file'])

            found_manifests = {}
            manifests = {}
            repo_urls = set()
            config_manifest_repos_project_list = []
            user_config_manifest_repos_project_list = []
            repos_list = []

            for manifest_repo in cfg_manifest_repos:
                # Get path to global manifest file
                global_manifest_directory = config['cfg_file'].manifest_repo_abs_path(manifest_repo)
                if args.verbose:
                    print(humble.MANIFEST_DIRECTORY)
                    print(global_manifest_directory)
                    print()
                #Create a dictionary containing all the manifests listed in the CiIndex.xml file
                index_path = os.path.join(global_manifest_directory, CI_INDEX_FILE_NAME)
                ci_index_xml = CiIndexXml(index_path)
                config_manifest_repos_project_list = ci_index_xml.project_list
                if args.archived:
                    config_manifest_repos_project_list.extend(ci_index_xml.archived_project_list)
                for project in config_manifest_repos_project_list:
                    xml_file = ci_index_xml.get_project_xml(project)
                    manifest = ManifestXml(os.path.normpath(os.path.join(global_manifest_directory, xml_file)))
                    found_manifests['{}:{}'.format(manifest_repo, project)] = manifest
                    combo_list = [c.name for c in manifest.combinations]
                    if args.archived:
                        combo_list.extend([c.name for c in manifest.archived_combinations])
                    for combo in combo_list:
                        sources = manifest.get_repo_sources(combo)
                        for source in sources:
                            repo_urls.add(self.get_repo_url(source.remote_url))
            for manifest_repo in user_config_manifest_repos:
                # Get path to global manifest file
                global_manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(manifest_repo)
                if args.verbose:
                    print(humble.MANIFEST_DIRECTORY)
                    print(global_manifest_directory)
                    print()
                #Create a dictionary containing all the manifests listed in the CiIndex.xml file
                index_path = os.path.join(global_manifest_directory, CI_INDEX_FILE_NAME)
                ci_index_xml = CiIndexXml(index_path)
                user_config_manifest_repos_project_list = ci_index_xml.project_list
                if args.archived:
                    user_config_manifest_repos_project_list.extend(ci_index_xml.archived_project_list)
                for project in user_config_manifest_repos_project_list:
                    xml_file = ci_index_xml.get_project_xml(project)
                    manifest = ManifestXml(os.path.normpath(os.path.join(global_manifest_directory, xml_file)))
                    found_manifests['{}:{}'.format(manifest_repo, project)] = manifest
                    combo_list = [c.name for c in manifest.combinations]
                    if args.archived:
                        combo_list.extend([c.name for c in manifest.archived_combinations])
                    for combo in combo_list:
                        sources = manifest.get_repo_sources(combo)
                        for source in sources:
                            repo_urls.add(self.get_repo_url(source.remote_url))

            #The possibility exists for two (or more) manifest repositories to contain manifest
            #files with the same project name. This is unlikely however. If a project name is
            #unique (no duplicate names in any of the other manifest repositories), then the
            #identifier for the manifest repository can be removed from dictionary key string.
            key_list = list(found_manifests)
            for entry in key_list:
                new_key = entry.split(':')[1]
                value = found_manifests.pop(entry)
                for found_manifest in list(found_manifests):
                    if found_manifest.split(':')[1] == new_key:
                        new_key = 'Manifest Repository: {} Project: {}'.format(entry.split(':')[0], entry.split(':')[1])
                        break
                if new_key in manifests.keys():
                    new_key = 'Manifest Repository: {} Project: {}'.format(entry.split(':'[0]), entry.split(':')[1])
                manifests[new_key] = value

            #Sort the manifests so projects will be displayed alphabetically
            manifests = collections.OrderedDict(sorted(manifests.items()))
        finally:
            if json_output:
                sys.stdout = stdout_backup
                devnull.close()

        #Determine the names of the repositories
        self.generate_repo_names(repo_urls, manifests, args.archived)

        #If the user provided a list of repositories to view, check to make sure
        #at least one repository will be shown, if not provide an error
        if args.repos and len([x for x in self.repo_names if x in args.repos]) <= 0:
            raise EdkrepoInvalidParametersException(humble.REPO_NOT_FOUND_IN_MANIFEST.format(','.join(args.repos)))

        #For each each git repository...
        for repo_name in self.repo_names:
            if args.repos and repo_name not in args.repos:
                continue
            repo = self.repo_names[repo_name][0]
            repo_data = { 'name': repo_name, 'url': repo, 'branches': [], 'commits': [], 'tags': [] }

            #Determine the list of branches that used by any branch combination in any manifest
            branches = set()
            commits = set()
            tags = set()
            for project_name in manifests:
                combo_list = [c.name for c in manifests[project_name].combinations]
                if args.archived:
                    combo_list.extend([c.name for c in manifests[project_name].archived_combinations])
                for combo in combo_list:
                    sources = manifests[project_name].get_repo_sources(combo)
                    for source in sources:
                        if self.get_repo_url(source.remote_url) == repo:
                            if source.branch:
                                branches.add(source.branch)
                            if source.tag:
                                tags.add(source.tag)
                            if source.commit:
                                commits.add(source.commit)

            #Sort the branch names so they will be displayed alphabetically
            #with the exception of branches named "main" or "master".
            #
            # 1. If a branch named "main" exists, then it will be displayed first.
            # 2. If a branch named "master" exists and a branch named "main" does
            #    NOT exist, then "master" will be displayed first.
            # 3. If both "main" and "master" exist, then "main" will be shown
            #    first and "master" will be shown second.
            branches = sorted(branches, key=str.casefold)
            tags = sorted(tags, key=str.casefold)
            commits = sorted(commits, key=str.casefold)

            if 'master' in branches:
                branches.remove('master')
                branches.insert(0, 'master')
            if 'main' in branches:
                branches.remove('main')
                branches.insert(0, 'main')

            #For each interesting branch in the current git repository...
            for ref_type in zip_longest(branches, commits, tags):
                add_branch = False
                add_commit = False
                add_tag = False
                add_combo = False

                if ref_type[0]:
                    branch_data = { 'name': ref_type[0], 'projects': [] }
                else: 
                    branch_data = None
                if ref_type[1]:
                    commit_data = { 'name': ref_type[1], 'projects': [] }
                else:
                    commit_data = None
                if ref_type[2]:
                    tag_data = { 'name': ref_type[2], 'projects': [] }
                else:
                    tag_data = None

                #Determine the branch combinations that use that branch
                for project_name in manifests:
                    branch_combos = []
                    commit_combos = []
                    tag_combos = []
                    combo_list = [c.name for c in manifests[project_name].combinations]
                    if args.archived:
                        combo_list.extend([c.name for c in manifests[project_name].archived_combinations])
                    for combo in combo_list:
                        sources = manifests[project_name].get_repo_sources(combo)
                        for source in sources:
                            if self.get_repo_url(source.remote_url) == repo:
                                # Track if multiple source types are used so only the one preferred by EdkRepo
                                # will be displayed as the default
                                # order of precedence for clone / checkout (1)commit (2) tag (3) branch
                                default_ref_type = ''
                                if source.commit:
                                    default_ref_type = 'commit'
                                elif source.tag and not source.commit:
                                    default_ref_type = 'tag'
                                elif source.branch and (not source.commit and not source.tag):
                                    default_ref_type = 'branch'
                                if ref_type[0]:
                                    if ref_type[0] == source.branch:
                                        branch_combos.append(combo)
                                        add_branch = True
                                if ref_type[1]:
                                    if ref_type[1] == source.commit:
                                        commit_combos.append(combo)
                                        add_commit = True
                                if ref_type[2]:
                                    if ref_type[2] == source.tag:
                                        tag_combos.append(combo)
                                        add_tag = True
                                break
                    if len(branch_combos) > 0 or len(commit_combos) > 0 or len(tag_combos) > 0:
                        #Sort the branch combinations so they will be displayed alphabetically
                        #with the exception that the default branch combination for the manifest
                        #file will be displayed first
                        default_combo = manifests[project_name].general_config.default_combo
                        if len(branch_combos) > 0:
                          branch_combos = sorted(branch_combos, key=str.casefold)
                          if default_combo in branch_combos:
                              branch_combos.remove(default_combo)
                              branch_combos.insert(0, default_combo)
                        if len(commit_combos) > 0:
                            commit_combos = sorted(commit_combos, key=str.casefold)
                            if default_combo in commit_combos:
                                commit_combos.remove(default_combo)
                                commit_combos.insert(0, default_combo)
                        if len(tag_combos) > 0:
                            tag_combos = sorted(tag_combos, key=str.casefold)
                            if default_combo in tag_combos:
                                tag_combos.remove(default_combo)
                                tag_combos.insert(0, default_combo)

                        project_data = { 'name': project_name, 'branch_combinations': [], 'commit_combinations': [], 'tag_combinations':[], 'default_ref_type': default_ref_type }
                        for combo in branch_combos:
                            project_data['branch_combinations'].append(
                                { 'name': combo,
                                'project_default_combination': default_combo == combo })
                        for combo in commit_combos:
                            project_data['commit_combinations'].append(
                                { 'name': combo,
                                'project_default_combination': default_combo == combo })
                        for combo in tag_combos:
                            project_data['tag_combinations'].append(
                                { 'name': combo,
                                'project_default_combination': default_combo == combo })
                        if add_branch:
                            branch_data['projects'].append(project_data)
                        if add_commit:
                            commit_data['projects'].append(project_data)
                        if add_tag:
                            tag_data['projects'].append(project_data)
                if add_branch:
                    repo_data['branches'].append(branch_data)
                if add_commit:
                    repo_data['commits'].append(commit_data)
                if add_tag:
                    repo_data['tags'].append(tag_data)
            repos_list.append(repo_data)

        if json_output:
            sys.stdout.flush()
            sys.stdout.write(json.dumps(repos_list, separators=(',', ':')))
            sys.stdout.flush()
        else:
            project_names = set()
            for repo_data in repos_list:
                for branch_data in repo_data['branches']:
                    for project_data in branch_data['projects']:
                        project_names.add(project_data['name'])
                for commit_data in repo_data['commits']:
                    for project_data in commit_data['projects']:
                        project_names.add(project_data['name'])
                for tag_data in repo_data['tags']:
                    project_names.add(project_data['name'])
            project_justify = len(max(project_names, key=len))
            print(humble.REPOSITORIES)
            for repo_data in repos_list:
                print(humble.REPO_NAME_AND_URL.format(repo_data['name'], repo_data['url']))
                if len(repo_data['branches']) > 0:
                    print(humble.BRANCHES)
                for branch_data in repo_data['branches']:
                    print(humble.BRANCH_FORMAT_STRING.format(branch_data['name']))
                    for project_data in branch_data['projects']:
                        first_combo = True
                        for combo_data in project_data['branch_combinations']:
                            #Print the project name
                            if first_combo:
                                project_name_print = humble.PROJECT_NAME_FORMAT_STRING.format(project_data['name'].ljust(project_justify))
                                first_combo = False
                            else:
                                project_name_print = '{} '.format((' ' * len(project_data['name'])).ljust(project_justify))
                            #Print the branch combination name, if this is the default branch combination,
                            #then print it in green color with *'s around it
                            if combo_data['project_default_combination'] and project_data['default_ref_type'] == 'branch':
                                print(humble.DEFAULT_COMBO_FORMAT_STRING.format(project_name_print, combo_data['name']))
                            else:
                                print(humble.COMBO_FORMAT_STRING.format(project_name_print, combo_data['name']))
                if len(repo_data['commits']) > 0:
                  print('Commits:')
                  for commit_data in repo_data['commits']:
                      print(humble.BRANCH_FORMAT_STRING.format(commit_data['name']))
                      for project_data in commit_data['projects']:
                          first_combo = True
                          for combo_data in project_data['commit_combinations']:
                              #Print the project name
                              if first_combo:
                                  project_name_print = humble.PROJECT_NAME_FORMAT_STRING.format(project_data['name'].ljust(project_justify))
                                  first_combo = False
                              else:
                                  project_name_print = '{} '.format((' ' * len(project_data['name'])).ljust(project_justify))
                              #Print the branch combination name, if this is the default branch combination,
                              #then print it in green color with *'s around it
                              if combo_data['project_default_combination'] and project_data['default_ref_type'] == 'commit':
                                  print(humble.DEFAULT_COMBO_FORMAT_STRING.format(project_name_print, combo_data['name']))
                              else:
                                  print(humble.COMBO_FORMAT_STRING.format(project_name_print, combo_data['name']))
                if len(repo_data['tags']) > 0:
                  print('Tags:')
                  for tag_data in repo_data['tags']:
                      print(humble.BRANCH_FORMAT_STRING.format(tag_data['name']))
                      for project_data in tag_data['projects']:
                          first_combo = True
                          for combo_data in project_data['tag_combinations']:
                              #Print the project name
                              if first_combo:
                                  project_name_print = humble.PROJECT_NAME_FORMAT_STRING.format(project_data['name'].ljust(project_justify))
                                  first_combo = False
                              else:
                                  project_name_print = '{} '.format((' ' * len(project_data['name'])).ljust(project_justify))
                              #Print the branch combination name, if this is the default branch combination,
                              #then print it in green color with *'s around it
                              if combo_data['project_default_combination'] and project_data['default_ref_type'] == 'tag':
                                  print(humble.DEFAULT_COMBO_FORMAT_STRING.format(project_name_print, combo_data['name']))
                              else:
                                  print(humble.COMBO_FORMAT_STRING.format(project_name_print, combo_data['name']))

    def get_repo_url(self, repo_url):
        if repo_url[-4:].lower() == '.git':
            return repo_url[:-4]
        return repo_url

    def get_repo_name(self, repo_url, manifests):
        for name in self.repo_names:
            if self.repo_names[name][0] == repo_url:
                return name
        raise EdkrepoInvalidParametersException(humble.REPO_NAME_NOT_FOUND)

    def generate_repo_names(self, repo_urls, manifests, archived=False):
        #Determine the names of the repositories
        self.repo_names = collections.OrderedDict()
        for repo_url in repo_urls:
            self.__repo_name_worker(repo_url, manifests, archived)

        #Sort the git repositories so they will be displayed alphabetically
        self.repo_names = collections.OrderedDict(sorted(self.repo_names.items()))
        names_to_move = []
        for repo_name in self.repo_names:
            if repo_name.lower().find('edk2') == 0:
                names_to_move.append(repo_name)
        names_to_move = sorted(names_to_move, reverse=True)
        for name_to_move in names_to_move:
            self.repo_names.move_to_end(name_to_move, False)
        names_to_move = []
        for repo_name in self.repo_names:
            if repo_name.lower().find('intel') == 0:
                names_to_move.append(repo_name)
        names_to_move = sorted(names_to_move, reverse=True)
        for name_to_move in names_to_move:
            self.repo_names.move_to_end(name_to_move, False)

    def __repo_name_worker(self, repo_url, manifests, archived=False):
        #This is a heuristic that guesses the "name" of a repository by looking
        #at the name given to it by the most manifest files.
        names = collections.defaultdict(int)
        for project_name in manifests:
            combo_list = [c.name for c in manifests[project_name].combinations]
            if archived:
                combo_list.extend([c.name for c in manifests[project_name].archived_combinations])
            for combo in combo_list:
                sources = manifests[project_name].get_repo_sources(combo)
                for source in sources:
                    if self.get_repo_url(source.remote_url) == repo_url:
                        names[source.root] += 1
        found_unique_name = False
        original_best_name = None
        original_best_name_frequency = 0
        while not found_unique_name:
            best_name = None
            best_name_frequency = 0
            if len(names) <= 0:
                if original_best_name_frequency == 1:
                    #If only 1 project uses this name, then append the project
                    #name to the directory name to create the repo name
                    for project_name in manifests:
                        combo_list = [c.name for c in manifests[project_name].combinations]
                        if archived:
                            combo_list.extend([c.name for c in manifests[project_name].archived_combinations])
                        for combo in combo_list:
                            sources = manifests[project_name].get_repo_sources(combo)
                            for source in sources:
                                if self.get_repo_url(source.remote_url) == repo_url and source.root == original_best_name:
                                    best_name = "{}-{}".format(original_best_name, project_name)
                                    best_name_frequency = original_best_name_frequency
                else:
                    best_name = repo_url
                    best_name_frequency = 0
                break
            for name in names:
                if names[name] > best_name_frequency:
                    best_name = name
                    best_name_frequency = names[name]
            if best_name is None:
                raise EdkrepoManifestInvalidException(humble.REPO_NOT_FOUND_IN_MANIFEST.format(repo_url))
            if original_best_name is None:
                original_best_name = best_name
                original_best_name_frequency = best_name_frequency
            if best_name in self.repo_names:
                if self.repo_names[best_name][0] == repo_url:
                    found_unique_name = True
                else:
                    #If there is a name collision, then which repo has the most
                    #Usage of the name owns the name
                    if best_name_frequency > self.repo_names[best_name][1]:
                        old_repo_url = self.repo_names[best_name][0]
                        del self.repo_names[best_name]
                        found_unique_name = True
                        self.repo_names[best_name] = (repo_url, best_name_frequency)
                        self.__repo_name_worker(old_repo_url, manifests, archived)
                    else:
                        #Use the name given by the second most manifest files
                        del names[best_name]
            else:
                found_unique_name = True
        self.repo_names[best_name] = (repo_url, best_name_frequency)