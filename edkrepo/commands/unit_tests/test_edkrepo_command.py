#!/usr/bin/env python3
#
## @file
# test_edkrepo_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib

import pytest


class TestEdkrepoCommand:

    @pytest.mark.parametrize('method, call_args', [
        pytest.param('get_metadata', (), id='get_metadata'),
        pytest.param('run_command', (None, None), id='run_command'),
    ])
    def test_raises_not_implemented(self, method, call_args):
        """Each abstract method must raise NotImplementedError on the base class."""
        command_mod = importlib.import_module('edkrepo.commands.edkrepo_command')
        cmd = command_mod.EdkrepoCommand()
        with pytest.raises(NotImplementedError):
            getattr(cmd, method)(*call_args)
