#!/usr/bin/env python3
#
## @file
# command_factory.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import inspect
import os
import sys
from edkrepo.commands.edkrepo_command import EdkrepoCommand
from edkrepo.commands.composite_command import CompositeCommand
from edkrepo.config.config_factory import GlobalConfig

def _is_command(CommandClass):
    if CommandClass == EdkrepoCommand:
        return False
    if CommandClass in EdkrepoCommand.__subclasses__():
        return True
    #Use reflection to see if the class would work as a command anyway
    try:
        cmd = CommandClass()
    except:
        return False
    funcs = inspect.getmembers(cmd, predicate=inspect.ismethod)
    has_get_metadata = False
    has_run_command = False
    for func in funcs:
        if func[0] == 'get_metadata' and len(inspect.getargspec(func[1])[0]) == 1:
            try:
                cmd.get_metadata()
                has_get_metadata = True
            except:
                has_get_metadata = False
        if func[0] == 'run_command':
            arg_spec = inspect.getargspec(func[1])
            if len(arg_spec[0]) == 3 and arg_spec[0][1] == "args" and arg_spec[0][2] == "config":
                has_run_command = True
    if has_get_metadata and has_run_command:
        return True
    else:
        return False

def get_commands():
    cfg_file = GlobalConfig()
    cmd_pkg_list = cfg_file.command_packages_list
    pref_cmd_pkg = cfg_file.pref_pkg
    commands = {}
    pref_commands = {}
    final_cmd_list = []
    cmd_search_dirs = []

    for cmd_pkg in cmd_pkg_list:
        mod = importlib.import_module(cmd_pkg)
        cmd_search_dirs.append((cmd_pkg, os.path.dirname(mod.__file__)))
    for cmd_dir in cmd_search_dirs:
        for module in os.listdir(cmd_dir[1]):
            if module == '__init__.py' or os.path.splitext(module)[1] != '.py':
                continue
            mod = importlib.import_module('{}.{}'.format(cmd_dir[0], os.path.splitext(module)[0]))
            mod_path = os.path.normcase(os.path.normpath(inspect.getfile(mod)))
            classes = inspect.getmembers(mod, predicate=inspect.isclass)
            for cls in classes:
                in_same_module = False
                try:
                    if mod_path == os.path.normcase(os.path.normpath(inspect.getfile(cls[1]))):
                        in_same_module = True
                except TypeError:
                    pass
                if in_same_module and _is_command(cls[1]):
                    if cmd_dir[0] == pref_cmd_pkg:
                        pref_commands.update([(cls[0], cls[1])])
                    else:
                        commands.update([(cls[0], cls[1])])
    for key in commands.keys():
        if key not in pref_commands.keys():
            final_cmd_list.append(commands[key])
    final_cmd_list.extend(pref_commands.values())
    return final_cmd_list

def create_composite_command():
    commands = get_commands()
    command = CompositeCommand()
    for cmd in commands:
        cmd_instance = cmd()
        command.add(cmd_instance)
    return command