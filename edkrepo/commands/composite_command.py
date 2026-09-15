#!/usr/bin/env python3
#
## @file
# composite_command.py
#
# Copyright (c) 2017 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from edkrepo.commands.edkrepo_command import ColorArgument, PerformanceArgument, VerboseArgument
import edkrepo.common.ui_functions as ui_functions


class CompositeCommand(object):
    def __init__(self):
        """Initialize the composite command with an empty list of sub-commands."""
        self._commands = []

    def add(self, command):
        """Add a command instance to the composite command."""
        self._commands.append(command)

    def get_metadata(self, command_name):
        """Return the metadata for the named command, augmented with the common arguments, or None if not found."""
        for command in self._commands:
            if command.get_metadata()['name'] == command_name:
                metadata = command.get_metadata()
                args = metadata['arguments']
                args.append(PerformanceArgument)
                args.append(VerboseArgument)
                args.append(ColorArgument)
                metadata['arguments'] = args
                return metadata

    def run_command(self, command_name, args, config):
        """Dispatch execution to the command matching the given name or alias, after configuring color output."""
        strip_color, convert_ansi = ui_functions.init_color_console(args.color)
        args.strip_color = strip_color
        args.convert_ansi = convert_ansi
        for command in self._commands:
            if command.get_metadata()['name'] == command_name:
                return command.run_command(args, config)
            elif 'alias' in command.get_metadata() and command.get_metadata()['alias'] == command_name:
                return command.run_command(args, config)

    def command_list(self):
        """Return the sorted list of registered command names."""
        command_names = []
        for command in self._commands:
            command_names.append(command.get_metadata()['name'])
        return sorted(command_names)
