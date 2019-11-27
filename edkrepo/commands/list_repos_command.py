#!/usr/bin/env python3
#
## @file
# list_repos_command.py
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import collections
import os

#from git import Repo
from colorama import Fore, Style

# Our modules
from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.edkrepo_command import ColorArgument
import edkrepo.commands.arguments.list_repos_args as arguments
import edkrepo.commands.humble.list_repos_humble as humble
from edkrepo.common.common_repo_functions import pull_latest_manifest_repo
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoManifestInvalidException
from edkrepo.common.ui_functions import init_color_console
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
        args.append(ColorArgument)
        return metadata

    def run_command(self, args, config):
        print()
        init_color_console(args.color)

        # Get path to global manifest file
        global_manifest_directory = config['cfg_file'].manifest_repo_abs_local_path
        if args.verbose:
            print(humble.MANIFEST_DIRECTORY)
            print(global_manifest_directory)
            print()
        index_path = os.path.join(global_manifest_directory, 'CiIndex.xml')

        pull_latest_manifest_repo(args, config)
        print()

        #Create a dictionary containing all the manifests listed in the CiIndex.xml file
        ci_index_xml = CiIndexXml(index_path)
        manifests = {}
        repo_urls = set()
        project_list = list(ci_index_xml.project_list)
        if args.archived:
            project_list.extend(ci_index_xml.archived_project_list)
        for project in project_list:
            xml_file = ci_index_xml.get_project_xml(project)
            manifest = ManifestXml(os.path.normpath(os.path.join(global_manifest_directory, xml_file)))
            manifests[project] = manifest
            for combo in [c.name for c in manifest.combinations]:
                sources = manifest.get_repo_sources(combo)
                for source in sources:
                    repo_urls.add(self.get_repo_url(source.remote_url))

        #Sort the manifests so projects will be displayed alphabetically
        manifests = collections.OrderedDict(sorted(manifests.items()))
        project_justify = len(max(manifests.keys(), key=len))

        #Determine the names of the repositories
        self.generate_repo_names(repo_urls, manifests)
        print(humble.REPOSITORIES)

        #If the user provided a list of repositories to view, check to make sure
        #at least one repository will be shown, if not provide an error
        if args.repos and len([x for x in self.repo_names if x in args.repos]) <= 0:
            raise EdkrepoInvalidParametersException(humble.REPO_NOT_FOUND_IN_MANIFEST.format(','.join(args.repos)))

        #For each each git repository...
        for repo_name in self.repo_names:
            if args.repos and repo_name not in args.repos:
                continue
            repo = self.repo_names[repo_name][0]
            print(humble.REPO_NAME_AND_URL.format(repo_name, repo))
            print(humble.BRANCHES)

            #Determine the list of branches that used by any branch combination in any manifest
            branches = set()
            for project_name in manifests:
                for combo in [c.name for c in manifests[project_name].combinations]:
                    sources = manifests[project_name].get_repo_sources(combo)
                    for source in sources:
                        if self.get_repo_url(source.remote_url) == repo:
                            branches.add(source.branch)

            #Sort the branch names so they will be displayed alphabetically
            #with the exception that if a branch named "master" exists, then it
            #will be displayed first
            branches = sorted(branches, key=str.casefold)
            if 'master' in branches:
                branches.remove('master')
                branches.insert(0, 'master')

            #For each interesting branch in the current git repository...
            for branch in branches:
                print(humble.BRANCH_FORMAT_STRING.format(branch))

                #Determine the branch combinations that use that branch
                for project_name in manifests:
                    combos = []
                    for combo in [c.name for c in manifests[project_name].combinations]:
                        sources = manifests[project_name].get_repo_sources(combo)
                        for source in sources:
                            if self.get_repo_url(source.remote_url) == repo and source.branch == branch:
                                combos.append(combo)
                                break
                    if len(combos) > 0:
                        #Sort the branch combinations so they will be displayed alphabetically
                        #with the exception that the default branch combination for the manifest
                        #file will be displayed first
                        combos = sorted(combos, key=str.casefold)
                        default_combo = manifests[project_name].general_config.default_combo
                        if default_combo in combos:
                            combos.remove(default_combo)
                            combos.insert(0, default_combo)
                        first_combo = True
                        for combo in combos:
                            #Print the project name
                            if first_combo:
                                project_name_print = humble.PROJECT_NAME_FORMAT_STRING.format(project_name.ljust(project_justify))
                                first_combo = False
                            else:
                                project_name_print = '{} '.format((' ' * len(project_name)).ljust(project_justify))
                            #Print the branch combination name, if this is the default branch combination,
                            #then print it in green color with *'s around it
                            if default_combo == combo:
                                print(humble.DEFAULT_COMBO_FORMAT_STRING.format(project_name_print, combo))
                            else:
                                print(humble.COMBO_FORMAT_STRING.format(project_name_print, combo))

    def get_repo_url(self, repo_url):
        if repo_url[-4:].lower() == '.git':
            return repo_url[:-4]
        return repo_url

    def get_repo_name(self, repo_url, manifests):
        for name in self.repo_names:
            if self.repo_names[name][0] == repo_url:
                return name
        raise EdkrepoInvalidParametersException(humble.REPO_NAME_NOT_FOUND)

    def generate_repo_names(self, repo_urls, manifests):
        #Determine the names of the repositories
        self.repo_names = collections.OrderedDict()
        for repo_url in repo_urls:
            self.__repo_name_worker(repo_url, manifests)

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

    def __repo_name_worker(self, repo_url, manifests):
        #This is a heuristic that guesses the "name" of a repository by looking
        #at the name given to it by the most manifest files.
        names = collections.defaultdict(int)
        for project_name in manifests:
            for combo in [c.name for c in manifests[project_name].combinations]:
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
                        for combo in [c.name for c in manifests[project_name].combinations]:
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
                        old_repo_url = self.repo_names[name][0]
                        del self.repo_names[best_name]
                        found_unique_name = True
                        self.repo_names[best_name] = (repo_url, best_name_frequency)
                        self.__repo_name_worker(old_repo_url, manifests)
                    else:
                        #Use the name given by the second most manifest files
                        del names[best_name]
            else:
                found_unique_name = True
        self.repo_names[best_name] = (repo_url, best_name_frequency)
