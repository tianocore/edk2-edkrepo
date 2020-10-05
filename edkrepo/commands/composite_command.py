#!/usr/bin/env python3
#
## @file
# composite_command.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo.commands.edkrepo_command import VerboseArgument, PerformanceArgument


class CompositeCommand(object):
    def __init__(self):
        self._commands = []

    def add(self, command):
        self._commands.append(command)

    def get_metadata(self, command_name):
        for command in self._commands:
            if command.get_metadata()['name'] == command_name:
                metadata = command.get_metadata()
                args = metadata['arguments']
                args.append(PerformanceArgument)
                args.append(VerboseArgument)
                metadata['arguments'] = args
                return metadata

    def run_command(self, command_name, args, config):
        for command in self._commands:
            if command.get_metadata()['name'] == command_name:
                return command.run_command(args, config)
            elif 'alias' in command.get_metadata() and command.get_metadata()['alias'] == command_name:
                return command.run_command(args, config)

    def command_list(self):
        command_names = []
        for command in self._commands:
            command_names.append(command.get_metadata()['name'])
        return sorted(command_names)
