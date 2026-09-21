#!/usr/bin/env python3
#
## @file
# test_command_factory.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import contextlib
import importlib
import os
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.composite_command import CompositeCommand
from edkrepo.commands.edkrepo_command import EdkrepoCommand


MODULE_COMMAND_FACTORY = 'edkrepo.commands.command_factory'
PKG_BASE = 'edkrepo.fake.base'
PKG_PREF = 'edkrepo.fake.pref'


class TestCommandFactory:

    class _SampleCommand(EdkrepoCommand):
        """A real EdkrepoCommand subclass; _is_command must recognize it as a command."""
        pass

    class _PlainClass:
        """An unrelated class with no command interface; _is_command must reject it."""
        pass

    class _DuckCommand:
        """A non-EdkrepoCommand class that duck-types the command interface; _is_command must accept it."""
        def get_metadata(self):
            return {}

        def run_command(self, args, config):
            pass

    @staticmethod
    def _patch_command_discovery(stack, import_map, listdir_map, members_map):
        """Patch os.listdir/inspect/importlib internals so get_commands can run against fake packages."""
        stack.enter_context(patch('{}.os.listdir'.format(MODULE_COMMAND_FACTORY),
                                  side_effect=lambda path: listdir_map[path]))
        stack.enter_context(patch('{}.inspect.getfile'.format(MODULE_COMMAND_FACTORY), return_value='/same'))
        stack.enter_context(patch('{}.inspect.getmembers'.format(MODULE_COMMAND_FACTORY),
                                  side_effect=lambda mod, predicate=None: members_map[mod]))
        stack.enter_context(patch('{}._is_command'.format(MODULE_COMMAND_FACTORY), return_value=True))
        stack.enter_context(patch('{}.importlib.import_module'.format(MODULE_COMMAND_FACTORY),
                                  side_effect=lambda name: import_map[name]))

    def test_get_commands_skips_dunder_init_and_non_python_files(self):
        """get_commands must scan only .py modules, ignoring __init__.py and non-Python files."""
        cfg = MagicMock()
        cfg.command_packages_list = [PKG_BASE]
        cfg.pref_pkg = PKG_PREF
        base_pkg = MagicMock(__file__='/base/__init__.py')
        alpha_mod = MagicMock()
        alpha_cls = type('AlphaCommand', (), {})
        import_map = {PKG_BASE: base_pkg, '{}.alpha_command'.format(PKG_BASE): alpha_mod}
        listdir_map = {os.path.dirname('/base/__init__.py'): ['__init__.py', 'readme.md', 'alpha_command.py']}
        members_map = {alpha_mod: [('AlphaCommand', alpha_cls)]}
        command_factory = importlib.import_module(MODULE_COMMAND_FACTORY)

        with contextlib.ExitStack() as stack, \
             patch('{}.GlobalConfig'.format(MODULE_COMMAND_FACTORY), return_value=cfg):
            self._patch_command_discovery(stack, import_map, listdir_map, members_map)
            result = command_factory.get_commands()

        assert result == [alpha_cls]

    def test_get_commands_preferred_package_overrides_duplicates_and_appends_last(self):
        """A command in both a normal and the preferred package must appear once, sourced from the preferred package, ordered after non-preferred commands."""
        cfg = MagicMock()
        cfg.command_packages_list = [PKG_BASE, PKG_PREF]
        cfg.pref_pkg = PKG_PREF
        base_pkg = MagicMock(__file__='/base/__init__.py')
        pref_pkg = MagicMock(__file__='/pref/__init__.py')
        base_bravo, base_shared = MagicMock(), MagicMock()
        pref_shared, pref_pref = MagicMock(), MagicMock()
        bravo_cls = type('BravoCommand', (), {})
        shared_base_cls = type('SharedCommand', (), {})
        shared_pref_cls = type('SharedCommand', (), {})
        pref_cls = type('PrefCommand', (), {})
        import_map = {
            PKG_BASE: base_pkg, PKG_PREF: pref_pkg,
            '{}.bravo_command'.format(PKG_BASE): base_bravo,
            '{}.shared_command'.format(PKG_BASE): base_shared,
            '{}.shared_command'.format(PKG_PREF): pref_shared,
            '{}.pref_command'.format(PKG_PREF): pref_pref,
        }
        listdir_map = {'/base': ['bravo_command.py', 'shared_command.py'],
                       '/pref': ['shared_command.py', 'pref_command.py']}
        members_map = {base_bravo: [('BravoCommand', bravo_cls)],
                       base_shared: [('SharedCommand', shared_base_cls)],
                       pref_shared: [('SharedCommand', shared_pref_cls)],
                       pref_pref: [('PrefCommand', pref_cls)]}
        command_factory = importlib.import_module(MODULE_COMMAND_FACTORY)

        with contextlib.ExitStack() as stack, \
             patch('{}.GlobalConfig'.format(MODULE_COMMAND_FACTORY), return_value=cfg):
            self._patch_command_discovery(stack, import_map, listdir_map, members_map)
            result = command_factory.get_commands()

        assert result == [bravo_cls, shared_pref_cls, pref_cls]

    @pytest.mark.parametrize('n', [
        pytest.param(1, id='single_command'),
        pytest.param(2, id='two_commands'),
    ])
    def test_create_composite_command(self, n):
        """create_composite_command must return a CompositeCommand with exactly n command instances."""
        cmds = [MagicMock() for _ in range(n)]
        with patch('edkrepo.commands.command_factory.get_commands', return_value=cmds):
            command_factory = importlib.import_module(MODULE_COMMAND_FACTORY)
            result = command_factory.create_composite_command()

        assert isinstance(result, CompositeCommand)
        assert len(result._commands) == n

    @pytest.mark.parametrize('cls, expected', [
        pytest.param(EdkrepoCommand, False, id='base_class_returns_false'),
        pytest.param(_SampleCommand, True, id='edkrepo_subclass_returns_true'),
        pytest.param(_PlainClass, False, id='plain_class_returns_false'),
        pytest.param(_DuckCommand, True, id='duck_typed_returns_true'),
    ])
    def test_is_command(self, cls, expected):
        """_is_command must correctly identify whether a class implements the edkrepo command interface."""
        command_factory = importlib.import_module(MODULE_COMMAND_FACTORY)

        assert command_factory._is_command(cls) is expected
