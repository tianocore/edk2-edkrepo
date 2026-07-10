#!/usr/bin/env python3
#
## @file
# install_functions.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Locates and invokes install.py on behalf of the "edkrepo setup" and "edkrepo
uninstall" commands.

This module is intentionally self-contained and does not import any other
edkrepo module. It must be safe to run before edkrepo.cfg is known to exist.
'''

import os
import shutil
import subprocess
import sys
import tempfile

SYSTEM_DIR = os.path.join('/', 'usr', 'local', 'share', 'edkrepo')

_KNOWN_PRODUCT_CODES = (
    '{AC6D5513-8A33-4B5F-ADA0-AACF2135B760}',
    '{494DB015-D682-458B-B5F1-3678F0C04D5E}',
)

_SCOPE_FLAGS = ('--local', '-l', '--system', '-s', '--user-setup')


def _user_edkrepo_dir():
    return os.path.join(os.path.expanduser('~'), '.edkrepo')


def _user_installer_dir():
    return os.path.join(_user_edkrepo_dir(), 'installer')


def _system_installer_dir():
    return os.path.join(SYSTEM_DIR, 'installer')


def is_user_configured():
    '''
    True if this user's $HOME has been configured, either by a --local install
    or by "edkrepo setup" after a --system install.
    '''
    return os.path.isfile(os.path.join(_user_edkrepo_dir(), 'edkrepo.cfg'))


def _has_local_installer():
    '''
    True only for a --local install: install.py is persisted under
    ~/.edkrepo/installer. "edkrepo setup" does not place install.py in
    ~/.edkrepo since the system-level install.py is used instead.
    '''
    return os.path.isfile(os.path.join(_user_installer_dir(), 'install.py'))


def has_system_install():
    return os.path.isfile(os.path.join(_system_installer_dir(), 'install.py'))


def _strip_scope_flags(argv):
    return [a for a in argv if a not in _SCOPE_FLAGS]


def _find_windows_uninstaller():
    '''
    Looks up _KNOWN_PRODUCT_CODES under HKEY_LOCAL_MACHINE\\...\\Uninstall, and
    returns the registered UninstallString for the first one found, or None if
    none of the known product codes are registered.
    '''
    import winreg
    key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
    for product_code in _KNOWN_PRODUCT_CODES:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, '{}\\{}'.format(key_path, product_code), 0,
                                 winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as subkey:
                return winreg.QueryValueEx(subkey, 'UninstallString')[0]
        except OSError:
            continue
    return None


def _handle_windows_uninstall(argv):
    '''
    Handles "edkrepo uninstall" on Windows by locating the registered
    uninstaller executable, launching it, and returning immediately without
    waiting for it to finish.

    This process must not be running by the time the uninstaller starts removing
    files. Windows has no exec()-like mechanism to replace a running process
    image, so any executable/DLL this process has loaded (Ex: edkrepo.exe, etc.)
    remains locked on disk until this process fully exits, which would make file
    removal fail. The uninstaller's' "Are you sure?" confirmation dialog
    conveniently blocks it from touching any files until the user responds,
    which gives plenty of time for this process to exit before that happens.
    '''
    uninstall_string = _find_windows_uninstaller()
    if uninstall_string is None:
        print('Nothing to uninstall: no EdkRepo installation was found in the Windows registry.')
        return 0
    if '--yes' in argv or '-y' in argv:
        print('Note: --yes has no effect on Windows.')
    print('Launching the EdkRepo uninstaller...')
    try:
        subprocess.Popen(uninstall_string, close_fds=True)
    except OSError as e:
        print('Error: Failed to launch the EdkRepo uninstaller ({})'.format(e))
        return 1
    return 0


def _run_installer(installer_dir, extra_args):
    '''
    Copies install.py to a temporary directory and executes it from there. This
    is done so the installer can safely remove/replace the directory it was
    originally invoked from (Ex: "edkrepo uninstall" removes
    ~/.edkrepo/installer, which is where install.py itself would otherwise be
    running from).

    A local-install places "config" at ~/.edkrepo/installer/config, while a
    system-install places it at /usr/local/share/edkrepo/config. Both layouts
    are checked here so this works for either.

    Returns the installer's exit code, or None if no installer was found.
    '''
    install_py = os.path.join(installer_dir, 'install.py')
    if not os.path.isfile(install_py):
        return None
    nested_config_dir = os.path.join(installer_dir, 'config')
    sibling_config_dir = os.path.join(os.path.dirname(installer_dir), 'config')
    config_dir = nested_config_dir if os.path.isdir(nested_config_dir) else sibling_config_dir
    tmp_dir = tempfile.mkdtemp(prefix='edkrepo_installer_')
    try:
        for name in os.listdir(installer_dir):
            src = os.path.join(installer_dir, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(tmp_dir, name))
        if os.path.isdir(config_dir):
            shutil.copytree(config_dir, os.path.join(tmp_dir, 'config'))
        tmp_install_py = os.path.join(tmp_dir, 'install.py')
        os.chmod(tmp_install_py, 0o755)
        result = subprocess.run([sys.executable, tmp_install_py] + extra_args, cwd=tmp_dir)
        return result.returncode
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def ask_prompt_customization():
    '''
    Interactively asks the user whether they want EdkRepo to add the checked
    out combo and branch to their command prompt.
    '''
    try:
        print('\n\u2554' + ('\u2550' * 19) + '\u2557')
    except UnicodeEncodeError:
        print('\n+' + ('-' * 19) + '+')
    try:
        print('\u2551 Shell Integration \u2551')
    except UnicodeEncodeError:
        print('| Shell Integration |')
    try:
        print('\u255a' + ('\u2550' * 19) + '\u255d')
    except UnicodeEncodeError:
        print('+' + ('-' * 19) + '+')
    print('\nEdkRepo can show the checked out \033[32mcombo\033[00m and \033[36mbranch\033[00m as part of the command prompt')
    print('For example, instead of:\n')
    try:
        print('\u250c' + ('\u2500' * 38) + '\u2510')
    except UnicodeEncodeError:
        print('+' + ('-' * 38) + '+')
    try:
        print('\u2502 \033[01;32muser@machine\033[00m:\033[01;34msrc\033[00m $                   \u2502')
    except UnicodeEncodeError:
        print('| \033[01;32muser@machine\033[00m:\033[01;34msrc\033[00m $                   |')
    try:
        print('\u2514' + ('\u2500' * 38) + '\u2518')
    except UnicodeEncodeError:
        print('+' + ('-' * 38) + '+')
    print('\nThe command prompt would look like:\n')
    try:
        print('\u250c' + ('\u2500' * 38) + '\u2510')
    except UnicodeEncodeError:
        print('+' + ('-' * 38) + '+')
    try:
        print('\u2502 \033[01;32muser@machine\033[00m:\033[01;34msrc\033[00m \033[32m[Edk2Main]\033[36m (main)\033[00m $ \u2502')
    except UnicodeEncodeError:
        print('| \033[01;32muser@machine\033[00m:\033[01;34msrc\033[00m \033[32m[Edk2Main]\033[36m (main)\033[00m $ |')
    try:
        print('\u2514' + ('\u2500' * 38) + '\u2518')
    except UnicodeEncodeError:
        print('+' + ('-' * 38) + '+')
    print('')
    try:
        answer = input('Would you like the combo and branch shown on the command prompt? [y/N] ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        print('')
        answer = 'n'
    return answer in ('y', 'yes')


def handle_setup(argv):
    '''
    Handles "edkrepo setup". argv is everything after "setup" on the command
    line (Ex: ['--prompt']). Returns a process exit code.
    '''
    if '-h' in argv or '--help' in argv:
        print('Usage: edkrepo setup [--prompt | --no-prompt]')
        print('')
        print('Configures EdkRepo for your user account after a system-level install.')
        return 0

    if is_user_configured():
        print('EdkRepo is already configured for your user account.')
        print('To reconfigure it, run "edkrepo uninstall" first.')
        return 0

    if not has_system_install():
        print('Error: No system-level EdkRepo install was found at {}.'.format(SYSTEM_DIR))
        print('Ask your system administrator to run the EdkRepo installer with --system,')
        print('or install EdkRepo yourself with --local.')
        return 1

    rc = _run_installer(_system_installer_dir(), ['--user-setup'] + _strip_scope_flags(argv))
    if rc is None:
        print('Error: {} is missing or corrupt.'.format(_system_installer_dir()))
        print('Ask your system administrator to re-run the EdkRepo --system installer.')
        return 1
    return rc


def handle_uninstall(argv):
    '''
    Handles "edkrepo uninstall". argv is everything after "uninstall" on the
    command line (Ex: '--yes', '--system', etc.). Returns a process exit code.
    '''
    if sys.platform == 'win32':
        if '-h' in argv or '--help' in argv:
            print('Usage: edkrepo uninstall')
            print('')
            print('Uninstalls EdkRepo. A confirmation dialog will be shown.')
            return 0
        return _handle_windows_uninstall(argv)

    if '-h' in argv or '--help' in argv:
        print('Usage: edkrepo uninstall [--yes] [--system]')
        print('')
        print('Uninstalls EdkRepo for your user account. Pass --system (as root, or')
        print('via sudo) to remove a system-level install instead.')
        return 0

    want_system = '--system' in argv or '-s' in argv
    passthrough = _strip_scope_flags(argv)

    if want_system:
        if os.geteuid() != 0:
            print('System-level EdkRepo uninstalls require root.')
            extra = ' --yes' if ('--yes' in argv or '-y' in argv) else ''
            print('Run: sudo edkrepo uninstall --system{}'.format(extra))
            return 1
        rc = _run_installer(_system_installer_dir(), ['--uninstall', '--system'] + passthrough)
        if rc is None:
            print('Error: No system-level EdkRepo install was found at {}.'.format(SYSTEM_DIR))
            return 1
        return rc

    is_mac = sys.platform == 'darwin'

    if _has_local_installer() or is_mac:
        scope_args = [] if is_mac else ['--local']
        rc = _run_installer(_user_installer_dir(), ['--uninstall'] + scope_args + passthrough)
    elif is_user_configured():
        # Remove EdkRepo from the user's $HOME
        rc = _run_installer(_system_installer_dir(), ['--uninstall', '--user-setup'] + passthrough)
    else:
        print('Nothing to uninstall: EdkRepo is not configured for your user account.')
        if has_system_install():
            print('However, a system-level EdkRepo install does exist. To remove it, an')
            print('administrator can run: sudo edkrepo uninstall --system')
        return 0
    if rc is None:
        print('Error: install.py could not be found. Please re-run the')
        print('EdkRepo installer package with --uninstall to clean up manually.')
        return 1
    return rc
