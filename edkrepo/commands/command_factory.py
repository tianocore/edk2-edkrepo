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

def _is_command(CommandClass):
    if CommandClass == EdkrepoCommand:
        return False
    if CommandClass in EdkrepoCommand.__subclasses__():
        return True
    #Use reflection to see if the class would work as a command anyway
    funcs = inspect.getmembers(CommandClass, predicate=inspect.ismethod)
    has_get_metadata = False
    has_run_command = False
    for func in funcs:
        if func[0] == 'get_metadata' and len(inspect.getargspec(func[1])[0]) == 1:
            has_get_metadata = True
        if func[0] == 'run_command':
            arg_spec = inspect.getargspec(func[1])
            if len(arg_spec[0]) == 3 and arg_spec[0][1] == "args" and arg_spec[0][2] == "config":
                has_run_command = True
    if has_get_metadata and has_run_command:
        return True
    else:
        return False

def get_commands():
    commands = []
    for module in os.listdir(os.path.dirname(__file__)):
        if module == "__init__.py" or os.path.splitext(module)[1] != ".py":
            continue
        mod = importlib.import_module("edkrepo.commands.{}".format(os.path.splitext(module)[0]))
        classes = inspect.getmembers(mod, predicate=inspect.isclass)
        for cls in classes:
            if _is_command(cls[1]):
                commands.append(cls[1])
    return commands

def create_composite_command():
    commands = get_commands()
    command = CompositeCommand()
    for cmd in commands:
        cmd_instance = cmd()
        command.add(cmd_instance)
    return command