#!/usr/bin/env python3
#
## @file
# edkrepo_cli.py
#
# Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import argparse
from operator import itemgetter
import sys
import traceback
try:
    from importlib.metadata import version
except ImportError:
    import pkg_resources
import time
import json
import os
import subprocess
import site
import inspect
import importlib.util
import datetime as dt

from git.exc import GitCommandError

from edkrepo.commands import command_factory
from edkrepo.config import config_factory
from edkrepo.common.edkrepo_exception import EdkrepoException, EdkrepoGlobalConfigNotFoundException
from edkrepo.common.edkrepo_exception import EdkrepoWarningException
from edkrepo.common.edkrepo_exception import EdkrepoConfigFileInvalidException
from edkrepo.common.humble import KEYBOARD_INTERRUPT, GIT_CMD_ERROR
from edkrepo.common.pathfix import get_actual_path
from edkrepo.common import install_functions

def generate_command_line(command):
    parser = argparse.ArgumentParser(prog='edkrepo')
    subparsers = parser.add_subparsers(dest='subparser_name')
    try:
        current_version = version("edkrepo")
    except NameError:
        try:
            current_version = pkg_resources.get_distribution("edkrepo").version
        except:
            #To prevent errors if edkrepo is being run without being installed (Python 3.7 and earlier)
            current_version = "0.0.0"
    except:
        #To prevent errors if edkrepo is being run without being installed (Python 3.8 and later)
        current_version = "0.0.0"
    parser.add_argument("--version", action="version", version="%(prog)s {0}".format(current_version))
    # "setup" is only relevant on Linux systems with a system-level EdkRepo
    # install; hide it from --help/shell completion everywhere else.
    show_setup_command = sys.platform.startswith('linux') and install_functions.has_system_install()
    for command_name in command.command_list():
        if command_name == 'setup' and not show_setup_command:
            continue
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

command_completion_script_header='''#!/usr/bin/env bash
#
## @file edkrepo_completions.sh
#
# Automatically generated please DO NOT modify !!!
#

'''

tcsh_command_completion_script_header='''#
## @file edkrepo_completions.csh
#
# Automatically generated please DO NOT modify !!!
#

'''

def _get_command_completion_commands(parser):
    import edkrepo.command_completion_edkrepo as completion
    commands = []
    for action in parser._positionals._group_actions:
        if action.choices is not None:
            commands = [c for c in action.choices]
            break
    commands = sorted(commands)
    commands_with_3rd_param_completion = [c for c in completion.command_completions if c in commands]
    commands_with_3rd_param_completion = sorted(commands_with_3rd_param_completion)
    return commands, commands_with_3rd_param_completion

def _write_tcsh_command_completion_script(f, commands, commands_with_3rd_param_completion):
    # Completion rules MUST be single quoted so that the `...` command
    # substitution used for dynamic (3rd parameter) completion is stored
    # literally and evaluated by tcsh at completion (TAB) time.  Double quotes
    # would evaluate it once when the script is sourced, freezing the results.
    f.write(tcsh_command_completion_script_header)
    first_param_rule = "'p/1/({})/'".format(' '.join(commands))
    dynamic_rules = ["'n/{0}/`command_completion_edkrepo {0}`/'".format(command)
                     for command in commands_with_3rd_param_completion]
    f.write('which edkrepo >& /dev/null\n')
    f.write('if ($status == 0) then\n')
    if dynamic_rules:
        # The dynamic rules require command_completion_edkrepo. If it is not
        # available, fall back to first parameter completion only.
        f.write('  which command_completion_edkrepo >& /dev/null\n')
        f.write('  if ($status == 0) then\n')
        f.write('    complete edkrepo {}\n'.format(' '.join([first_param_rule] + dynamic_rules)))
        f.write('  else\n')
        f.write('    complete edkrepo {}\n'.format(first_param_rule))
        f.write('  endif\n')
    else:
        f.write('  complete edkrepo {}\n'.format(first_param_rule))
    f.write('endif\n')

def generate_command_completion_script(script_filename, parser, shell='bash'):
    commands, commands_with_3rd_param_completion = _get_command_completion_commands(parser)
    if shell == 'tcsh':
        with open(script_filename, 'w') as f:
            _write_tcsh_command_completion_script(f, commands, commands_with_3rd_param_completion)
        return
    with open(script_filename, 'w') as f:
        f.write(command_completion_script_header)
        if sys.platform == "win32":
            command_completion_path = os.path.dirname(sys.executable)
            command_completion_path = os.path.join(command_completion_path, 'Scripts', "command_completion_edkrepo.exe")
            if not os.path.isfile(command_completion_path):
                print('command_completion_edkrepo.exe not found')
                return
            command_completion_path = get_actual_path(command_completion_path)
            (drive, path) = os.path.splitdrive(command_completion_path)
            command_completion_path = '/{}{}'.format(drive.replace(':','').lower(), path.replace('\\','/'))
            f.write("export command_completion_edkrepo_file='{}'\n".format(command_completion_path))
            f.write('alias command_completion_edkrepo="$command_completion_edkrepo_file"\n')
        f.write('_edkrepo_completions() {\n    if [ "${#COMP_WORDS[@]}" -eq "2" ]; then\n')
        f.write('        COMPREPLY=($(compgen -W "{}" -- "${{COMP_WORDS[1]}}"))\n'.format(' '.join(commands)))
        if len(commands_with_3rd_param_completion) > 0:
            f.write('    elif [ "${#COMP_WORDS[@]}" -eq "3" ]; then\n')
        first_loop = True
        for command in commands_with_3rd_param_completion:
            if first_loop:
                f.write('        if [ "${{COMP_WORDS[1]}}" == "{}" ]; then\n'.format(command))
                first_loop = False
            else:
                f.write('        elif [ "${{COMP_WORDS[1]}}" == "{}" ]; then\n'.format(command))
            f.write('            COMPREPLY=($(compgen -W "$(command_completion_edkrepo ${COMP_WORDS[1]})" -- "${COMP_WORDS[2]}"))\n')
        if len(commands_with_3rd_param_completion) > 0:
            f.write('        fi\n')
        f.write('    fi\n}\n\n')
        if len(commands_with_3rd_param_completion) > 0:
            if sys.platform == "win32":
                f.write('if [ -x "$(command -v edkrepo)" ] && [ -x "$(command -v $command_completion_edkrepo_file)" ]; then\n')
            else:
                f.write('if [ -x "$(command -v edkrepo)" ] && [ -x "$(command -v command_completion_edkrepo)" ]; then\n')
        else:
            f.write('if [ -x "$(command -v edkrepo)" ]; then\n')
        f.write('    complete -F _edkrepo_completions edkrepo\nfi\n')

def main():
    start_time = dt.datetime.now()
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
    if sys.argv[1] == 'generate-command-completion-script' and len(sys.argv) >= 3:
        rest = sys.argv[2:]
        shell = 'bash'
        if '--shell' in rest:
            i = rest.index('--shell')
            if i + 1 < len(rest):
                shell = rest[i + 1]
                del rest[i:i + 2]
            else:
                del rest[i:i + 1]
        if not rest:
            print('Error: no output path specified for generate-command-completion-script')
            return 1
        if shell not in ('bash', 'tcsh'):
            print("Error: unsupported shell '{}' for generate-command-completion-script (expected 'bash' or 'tcsh')".format(shell))
            return 1
        generate_command_completion_script(rest[0], parser, shell)
        return 0
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
    if parsed_args.performance:
        print('\nExecution Time: {}'.format(dt.datetime.now() - start_time))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
