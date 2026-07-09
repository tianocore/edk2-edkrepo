#!/usr/bin/env python3
#
## @file
# test_repin_hook_shebang.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import stat
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.common.common_repo_functions import _repin_hook_shebang, _edkrepo_hook_interpreter

HOOK_BODY = 'print("hello from hook")\n'

def _write_hook(tmp_path, shebang, name='some-hook'):
    hook_file = tmp_path / name
    hook_file.write_text('{}\n{}'.format(shebang, HOOK_BODY))
    return str(hook_file)

def _read_first_line(hook_file_name):
    with open(hook_file_name, 'r') as f:
        return f.readline()

@pytest.fixture
def edkrepo_shim(tmp_path):
    """Creates ~/.edkrepo/edkrepo_python as a non-executable file."""
    edkrepo_dir = tmp_path / '.edkrepo'
    edkrepo_dir.mkdir()
    shim = edkrepo_dir / 'edkrepo_python'
    shim.write_text('#!/bin/sh\nexec "/usr/bin/python3.13" "$@"\n')
    return edkrepo_dir, shim

class TestEdkrepoHookInterpreter:
    def test_uses_launcher_when_present_and_executable(self, edkrepo_shim):
        edkrepo_dir, shim = edkrepo_shim
        os.chmod(str(shim), os.stat(str(shim)).st_mode | stat.S_IEXEC)
        with patch('edkrepo.common.common_repo_functions.pathfix.expanduser', return_value=str(edkrepo_dir)):
            assert _edkrepo_hook_interpreter() == str(shim)

    def test_falls_back_to_sys_executable_when_launcher_missing(self, tmp_path):
        edkrepo_dir = tmp_path / '.edkrepo'  # deliberately not created
        with patch('edkrepo.common.common_repo_functions.pathfix.expanduser', return_value=str(edkrepo_dir)):
            assert _edkrepo_hook_interpreter() == sys.executable

    def test_falls_back_to_sys_executable_when_launcher_not_executable(self, edkrepo_shim):
        edkrepo_dir, shim = edkrepo_shim
        # no chmod -- deliberately left non-executable
        with patch('edkrepo.common.common_repo_functions.pathfix.expanduser', return_value=str(edkrepo_dir)):
            assert _edkrepo_hook_interpreter() == sys.executable

class TestRepinHookShebangPlatformGuard:
    @pytest.mark.parametrize('platform,expected', [
        ('win32',  '#!/usr/bin/env python3\n'),
        ('linux',  '#!/opt/edkrepo_python\n'),
        ('darwin', '#!/opt/edkrepo_python\n'),
    ])
    def test_platform_guard(self, tmp_path, platform, expected):
        hook_file = _write_hook(tmp_path, '#!/usr/bin/env python3')
        with patch('edkrepo.common.common_repo_functions.sys.platform', platform), \
             patch('edkrepo.common.common_repo_functions._edkrepo_hook_interpreter',
                   return_value='/opt/edkrepo_python'):
            _repin_hook_shebang(hook_file)
        assert _read_first_line(hook_file) == expected

class TestRepinHookShebangGenericMatching:
    @pytest.mark.parametrize('shebang,expected', [
        ('#!/usr/bin/env python3',    '#!/opt/edkrepo_python\n'),   # generic env form  -> rewritten
        ('#!/usr/bin/python3',        '#!/opt/edkrepo_python\n'),   # bare /usr/bin form -> rewritten
        ('#!/usr/bin/env python3 -u', '#!/opt/edkrepo_python -u\n'), # generic form with trailing args -> rewritten, args preserved
        ('#!/usr/bin/python3.12',     '#!/usr/bin/python3.12\n'),   # version-pinned     -> left alone
        ('#!/opt/bin/python3.12.3',   '#!/opt/bin/python3.12.3\n'), # custom-pinned      -> left alone
        ('#!/bin/sh',                 '#!/bin/sh\n'),               # non-python         -> left alone
    ])
    def test_shebang_matching(self, tmp_path, shebang, expected):
        hook_file = _write_hook(tmp_path, shebang)
        with patch('edkrepo.common.common_repo_functions.sys.platform', 'linux'), \
             patch('edkrepo.common.common_repo_functions._edkrepo_hook_interpreter',
                   return_value='/opt/edkrepo_python'):
            _repin_hook_shebang(hook_file)
        assert _read_first_line(hook_file) == expected

    def test_non_shebang_file_is_left_alone(self, tmp_path):        # kept separate -- different shape
        hook_file = tmp_path / 'binary-hook'
        hook_file.write_bytes(b'\x7fELF\x02\x01\x01\x00garbage')
        with patch('edkrepo.common.common_repo_functions.sys.platform', 'linux'), \
             patch('edkrepo.common.common_repo_functions._edkrepo_hook_interpreter',
                   return_value='/opt/edkrepo_python'):
            _repin_hook_shebang(str(hook_file))
        with open(str(hook_file), 'rb') as f:
            assert f.read() == b'\x7fELF\x02\x01\x01\x00garbage'

class TestRepinHookShebangBestEffort:
    def test_missing_file_does_not_raise(self, tmp_path):
        hook_file = str(tmp_path / 'does-not-exist')
        with patch('edkrepo.common.common_repo_functions.sys.platform', 'linux'), \
             patch('edkrepo.common.common_repo_functions._edkrepo_hook_interpreter', return_value='/opt/edkrepo_python'):
            _repin_hook_shebang(hook_file)  # should not raise
