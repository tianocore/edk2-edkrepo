#!/usr/bin/env python3
#
## @file
# log_command.py
#
# Copyright (c) 2017 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import subprocess
import sys
from datetime import datetime

from colorama import Fore

from edkrepo.commands.edkrepo_command import EdkrepoCommand
import edkrepo.commands.arguments.log_args as arguments
from edkrepo.common.common_repo_functions import sort_commits, find_less
import edkrepo.common.ui_functions as ui_functions
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest

class LogCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'log'
        metadata['help-text'] = arguments.LOG_COMMAND_DESCRIPTION
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'number',
                     'short-name': 'n',
                     'action': 'store',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.NUMBER_HELP})
        args.append({'name' : 'oneline',
                     'short-name': 'o',
                     'positional' : False,
                     'required' : False,
                     'help-text' : arguments.ONELINE_HELP})
        return metadata

    def run_command(self, args, config):
        if args.number:
            try:
                args.number = int(args.number)
            except ValueError:
                print("Error: \'{}\' is not an integer".format(args.number))
                return

        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()

        sorted_commit_list = sort_commits(manifest, workspace_path, args.number)

        less_path, use_less = find_less()

        if use_less:
            output_string = ''
            separator = '\n'

        for commit in sorted_commit_list:
            if args.oneline:
                oneline = "{}{:.9s}{} {:15.15s}{} {:.80s}".format(Fore.YELLOW,
                                                                  commit.hexsha,
                                                                  Fore.CYAN,
                                                                  os.path.basename(commit.repo.working_dir),
                                                                  Fore.RESET,
                                                                  ui_functions.safe_str(commit.summary))
                if use_less:
                    output_string = separator.join((output_string, oneline))

                else:
                    print(oneline)
            else:
                time_string = datetime.utcfromtimestamp(commit.authored_date - commit.author_tz_offset).strftime("%c")
                time_zone_string = "{}{:04.0f}".format("-" if commit.author_tz_offset > 0 else "+",
                                                       abs(commit.author_tz_offset/36))
                hexsha_string = "{}commit {}{} ({}){}".format(Fore.YELLOW,
                                                              commit.hexsha,
                                                              Fore.CYAN,
                                                              os.path.basename(commit.repo.working_dir),
                                                              Fore.RESET)
                author_string = "Author: {} <{}>".format(commit.author.name, commit.author.email)
                date_string = "Date:   {} {}".format(time_string, time_zone_string)
                if use_less:
                    output_string = separator.join((output_string, hexsha_string, ui_functions.safe_str(author_string), date_string))

                    commit_string = ""
                    for line in commit.message.splitlines():
                        commit_string = separator.join((commit_string, ui_functions.safe_str("    {}".format(line))))

                    output_string = separator.join((output_string, commit_string, separator))
                else:
                    print(hexsha_string)
                    ui_functions.print_safe(author_string)
                    print(date_string)
                    print("")
                    for line in commit.message.splitlines():
                        ui_functions.print_safe("    {}".format(line))
                    print("")
        if less_path:
            less_output = subprocess.Popen([str(less_path), '-F', '-R', '-S', '-X', '-K'], stdin=subprocess.PIPE, stdout=sys.stdout, universal_newlines=True)
            less_output.communicate(input=output_string)

