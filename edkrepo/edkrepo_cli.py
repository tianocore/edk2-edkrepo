#!/usr/bin/env python3
#
## @file
# edkrepo_cli.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import argparse
from operator import itemgetter
import sys
import traceback
import pkg_resources
import time
import json
import os
import subprocess
import site
import inspect
import imp
import importlib.util

from git.exc import GitCommandError

#Prefer the site-packages version of edkrepo
sitepackages = site.getsitepackages()
sys.path = sitepackages + sys.path
import edkrepo
edkrepo_site_dir = None
edkrepo_package_path = os.path.dirname(os.path.dirname(edkrepo.__file__))
for directory in sitepackages:
    if edkrepo_package_path == directory:
        edkrepo_site_dir = edkrepo_package_path
        break
else:
    imp.reload(edkrepo)
    edkrepo_package_path = os.path.dirname(os.path.dirname(edkrepo.__file__))
    for directory in sitepackages:
        if edkrepo_package_path == directory:
            edkrepo_site_dir = edkrepo_package_path
            break
if edkrepo_site_dir is None:
    print('Running EdkRepo from local source')

#Determine if this module is being imported by the launcher script
run_via_launcher_script = False
importer = ""
importer_file = ""
f = inspect.currentframe().f_back
while f is not None:
    if f.f_globals.get('__name__').find('importlib') == -1:
        importer = f.f_globals.get('__name__')
        importer_file = f.f_globals.get('__file__')
        if importer_file is None:
            importer_file = ""
        break
    f = f.f_back
if importer == "__main__":
    if os.path.basename(importer_file).lower() == "__main__.py":
        if os.path.basename(os.path.dirname(importer_file)).lower().find('edkrepo') != -1:
            run_via_launcher_script = True
    elif os.path.basename(importer_file).lower().find('edkrepo') != -1:
        run_via_launcher_script = True

if __name__ == "__main__" or run_via_launcher_script:
    #If this module is the entrypoint, we need to make
    #sure that the site-packages version is being executed
    if edkrepo_site_dir is not None and os.path.commonprefix([edkrepo_site_dir, __file__]) != edkrepo_site_dir:
        edkrepo_cli_file_name = os.path.join(edkrepo_site_dir, 'edkrepo', 'edkrepo_cli.py')
        if os.path.isfile(edkrepo_cli_file_name):
                spec = importlib.util.spec_from_file_location('edkrepo.edkrepo_cli', edkrepo_cli_file_name)
                edkrepo_cli = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(edkrepo_cli)
                try:
                    sys.exit(edkrepo_cli.main())
                except Exception as e:
                    traceback.print_exc()
                    sys.exit(1)

from edkrepo.commands import command_factory
from edkrepo.config import config_factory
from edkrepo.common.edkrepo_exception import EdkrepoException, EdkrepoGlobalConfigNotFoundException
from edkrepo.common.edkrepo_exception import EdkrepoWarningException
from edkrepo.common.edkrepo_exception import EdkrepoConfigFileInvalidException
from edkrepo.common.humble import KEYBOARD_INTERRUPT, GIT_CMD_ERROR

def generate_command_line(command):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser_name')
    try:
        version = pkg_resources.get_distribution("edkrepo").version
        parser.add_argument("--version", action="version", version="%(prog)s {0}".format(version))
    except:
        #To prevent errors if edkrepo is being run without being installed
        parser.add_argument("--version", action="version", version="%(prog)s 0.0.0")
    #command_names = command.command_list()
    for command_name in command.command_list():
        subparser_name = 'parser_' + command_name
        command_name_metadata = command.get_metadata(command_name)
        if 'alias' in command_name_metadata:
            subparser_name = subparsers.add_parser(command_name, aliases=[command_name_metadata['alias']],
                                                   help=command_name_metadata['help-text'],
                                                   description=command_name_metadata['help-text'],
                                                   formatter_class=argparse.RawTextHelpFormatter)
        else:
            subparser_name = subparsers.add_parser(command_name,
                                                   help=command_name_metadata['help-text'],
                                                   description=command_name_metadata['help-text'],
                                                   formatter_class=argparse.RawTextHelpFormatter)
        #break arg list up into positional and non-positional arg lists
        positional_args = []
        non_positional_args = []
        choice_args = []
        for arg in command_name_metadata['arguments']:
            if arg.get('positional'):
                positional_args.append(arg)
            elif arg.get('choice'):
                choice_args.append(arg)
            else:
                non_positional_args.append(arg)
        #if there are more than 1 positional args sort them by position and add to the subparser
        if positional_args != [] and len(positional_args) > 1:
            positional_args = sorted(positional_args, key=itemgetter('position'))
        #add positional args
        for arg in positional_args:
            #check for choices
            if arg.get('choices'):
                choices = []
                help_text = arg.get('help-text')
                for choice in choice_args:
                    if choice.get('parent') == arg.get('name'):
                        choices.append(choice.get('choice'))
                        help_text += '\n' + choice.get('help-text')
                subparser_name.add_argument(arg.get('name'), choices=choices, help=help_text)
            #check if non-required positional
            elif not arg.get('required'):
                subparser_name.add_argument(arg.get('name'), nargs='?', help=arg.get('help-text'))
            else:
                subparser_name.add_argument(arg.get('name'), help=arg.get('help-text'))
        #add non-positional args
        for arg in non_positional_args:
            if 'action' in arg:
                arg_action = arg.get('action')
            else:
                arg_action = 'store_true'
            if 'short-name' in arg:
                short_name = '-' + arg['short-name']
                subparser_name.add_argument(short_name, ('--' + arg.get('name')), action=arg_action, help=arg.get('help-text'))
                if 'nargs' in arg:
                    subparser_name.add_argument(short_name, ('--' + arg.get('name')), action=arg_action, nargs=arg.get('nargs'), help=arg.get('help-text'))
            elif 'nargs' in arg:
                subparser_name.add_argument(('--' + arg.get('name')), action=arg_action, nargs=arg.get('nargs'), help=arg.get('help-text'))
            else:
                subparser_name.add_argument(('--' + arg.get('name')), action=arg_action, help=arg.get('help-text'))
    return parser

def main():
    command = command_factory.create_composite_command()
    config = {}
    try:
        config["cfg_file"] = config_factory.GlobalConfig()
        config["user_cfg_file"] = config_factory.GlobalUserConfig()
    except EdkrepoGlobalConfigNotFoundException as e:
        print("Error: {}".format(str(e)))
        return e.exit_code
    except EdkrepoConfigFileInvalidException as e:
        print("Error: {}".format(str(e)))
        return e.exit_code

    parser = generate_command_line(command)
    if len(sys.argv) <= 1:
        parser.print_help()
        return 1
    parsed_args = parser.parse_args()
    command_name = parsed_args.subparser_name
    try:
        command.run_command(command_name, parsed_args, config)
    except EdkrepoWarningException as e:
        print("Warning: {}".format(str(e)))
        return e.exit_code
    except EdkrepoException as e:
        if parsed_args.verbose:
            traceback.print_exc()
        print("Error: {}".format(str(e)))
        return e.exit_code
    except GitCommandError as e:
        if parsed_args.verbose:
            traceback.print_exc()
        out_str = ''
        out_str = ' '.join(e.command)
        print(GIT_CMD_ERROR.format(out_str))
        print(e.stdout.strip())
        print(e.stderr.strip())
        return e.status
    except KeyboardInterrupt:
        if parsed_args.verbose:
            traceback.print_exc()
        print(KEYBOARD_INTERRUPT)
        return 1
    except Exception as e:
        if parsed_args.verbose:
            traceback.print_exc()
        print("Error: {}".format(str(e)))
        return 1
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
