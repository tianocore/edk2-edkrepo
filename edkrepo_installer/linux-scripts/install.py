#!/usr/bin/env python3
#
## @file
# install.py
#
# Copyright (c) 2018 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from argparse import ArgumentParser
import base64
import collections
import configparser
import getpass
import gzip
import hashlib
import importlib.util
import logging
import os
import platform
import re
import stat
import shutil
import subprocess
import sys
import traceback
import xml.etree.ElementTree as et

#
# Environment detection
#
MAC = "mac"
LINUX = "linux"
if sys.platform == "darwin":
    ostype = MAC
elif sys.platform.startswith("linux"):
    ostype = LINUX
elif os.name == "posix":
    print("Warning: Unrecognized UNIX OS... treating as Linux")
    ostype = LINUX
else:
    raise EnvironmentError("Unsupported OS")

tool_sign_on = 'Installer for {} version {}\nCopyright(c) {}, {}'
_default_product_name = 'edkrepo'
_default_publisher_name = 'The TianoCore Contributors'
_copyright_year = '2026'  # patched at build time by build_linux_installer.py

#
# Vendor customizer support
#
# Vendors that extend this installer may place a file named
# `vendor_customizer.py` alongside install.py. That file must define a
# class named `VendorCustomizer` which may implement any subset of the
# following methods. Unimplemented methods are skipped.
#
# class VendorCustomizer:
#     def configure_install_args(self, args, ostype):
#         '''
#         Called immediately after the installer's command line arguments are
#         parsed, before argument validation and before any interactive
#         prompts. Receives the argparse.Namespace produced by the installer's
#         argument parser and returns an argparse.Namespace, either the same
#         object mutated in place, or a replacement.
#
#         Setting a field on `args` (Ex: args.local, args.system, args.user,
#         args.py, args.prompt, args.no_prompt, etc.) has the same effect as
#         if the corresponding command line flag had been passed directly, so
#         this hook can pre-empt any of the installer's interactive prompts.
#         '''
#
#     def pre_install(self, context):
#         '''
#         Called after system information is collected and all dependencies
#         are verified, but BEFORE configuration files are copied or any
#         wheels are installed.
#         '''
#
#     def get_wheels(self, context, base_wheels):
#         '''
#         Called just before the wheel install loop. Receives "base_wheels",
#         an OrderedDict that get_required_wheels() produces. The base_wheels
#         dict is keyed by package name; values are dicts with the following
#         keys: wheel, uninstall, version, install. Must return an OrderedDict
#         in the same format. The return value replaces the wheel list.
#         '''
#
#     def get_product_name(self):
#         '''
#         Returns the product name used in the sign-on message.
#         '''
#
#     def get_publisher(self):
#         '''
#         Returns the publisher name used in the sign-on message.
#         '''
#
#     def configure_command_completion(self, context):
#         '''
#         Called right before the installer generates shell command completion
#         scripts. Returning a truthy value skips command completion setup. Use
#         this when the vendor customizer sets up command completion itself
#         using a different mechanism.  Returning a falsy value (or not
#         implementing this method) leaves the installer's default behavior
#         unchanged.
#         '''
#
#     def post_install(self, context):
#         '''
#         Called after all wheels are installed and shell integration is
#         configured, immediately before the installer exits with success.
#         '''
#
#     def pre_uninstall(self, context):
#         '''
#         Called at the start of an uninstall, before any files are removed or
#         packages are uninstalled.
#         '''
#
#     def get_uninstall_packages(self, context, base_packages):
#         '''
#         Called just before the uninstaller removes EdkRepo's pip packages.
#         Receives "base_packages", a tuple of pip package names that the
#         generic installer uninstalls (Ex: ('edkrepo',)). Must return an
#         iterable of package names; the return value replaces the package
#         list. Use this to have additional vendor-specific pip packages
#         (Ex: an internal companion package) removed alongside edkrepo.
#         '''
#
#     def post_uninstall(self, context):
#         '''
#         Called at the end of an uninstall, after the generic uninstall
#         logic has completed. Use this to reverse any vendor-specific
#         customizations made in pre_install()/post_install().
#         '''
class InstallerContext:
    '''
    Provides the install environment to the vendor customizer plugin.
    All attributes are read-only from the plugin's perspective.
    '''
    def __init__(self, ostype, python, install_to_local, log,
                 whl_src_dir, username, user_home_dir, scope=None):
        self.ostype = ostype                     # MAC or LINUX
        self.python = python                     # Python executable
        self.install_to_local = install_to_local # True for --user and --user-setup, False for --system
        self.log = log                           # standard logging.Logger
        self.whl_src_dir = whl_src_dir           # absolute path to wheels/ directory
        self.username = username                 # target user name (None for --system)
        self.user_home_dir = user_home_dir       # absolute path to target user's home directory (None for --system)
        self.scope = scope                       # 'local', 'system', or 'user-setup'
        self.run = run_with_externally_managed_check  # pip helper (handles --break-system-packages)
        self.get_pyenv_version_name = get_pyenv_version_name    # macOS: get Python version
        self.make_pyenv_launcher = write_pyenv_pinned_launcher  # macOS: write a pyenv launcher shim

def _load_vendor_customizer():
    '''
    Discovers and loads vendor_customizer.py.
    Returns an instance of VendorCustomizer, or None if the file is absent.
    '''
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor_customizer.py')
    if not os.path.isfile(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location('vendor_customizer', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cls = getattr(mod, 'VendorCustomizer', None)
        return cls() if cls is not None else None
    except Exception:
        return None

# Data here should be maintained in a configuration file
cfg_dir = '.edkrepo'
directories_with_executables = ['git_automation']
cfg_src_dir = os.path.abspath('config')
whl_src_dir = os.path.abspath('wheels')
def_python = 'python3'
nfs_home_directory_data = re.compile(r"NFSHomeDirectory:\s*(\S+)")

# ZSH Configuration options
prompt_regex = re.compile(r"#\s+[Aa][Dd][Dd]\s+[Ee][Dd][Kk][Rr][Ee][Pp][Oo]\s+&\s+[Gg][Ii][Tt]\s+[Tt][Oo]\s+[Tt][Hh][Ee]\s+[Pp][Rr][Oo][Mm][Pp][Tt]")
# Marks the end of the prompt customization block written to ~/.bashrc &
# ~/.zshrc. Having an explicit end marker lets uninstall reliably remove the
# block even if it was written by an older/newer version of install.py whose
# block content differs.
prompt_end_regex = re.compile(r"#\s+[Ee][Nn][Dd]\s+[Ee][Dd][Kk][Rr][Ee][Pp][Oo]\s+[Pp][Rr][Oo][Mm][Pp][Tt]\s+[Cc][Uu][Ss][Tt][Oo][Mm][Ii][Zz][Aa][Tt][Ii][Oo][Nn]")
zsh_autoload_compinit_regex = re.compile(r"autoload\s+-U\s+compinit")
zsh_autoload_bashcompinit_regex = re.compile(r"autoload\s+-U\s+bashcompinit")
zsh_autoload_colors_regex = re.compile(r"autoload\s+-U\s+colors")
zsh_colors_regex = re.compile(r"\n\s*colors\n")
zsh_compinit_regex = re.compile(r"compinit\s+-u")
zsh_bashcompinit_regex = re.compile(r"\n\s*bashcompinit\n")
zsh_autoload_compinit = 'autoload -U compinit'
zsh_autoload_bashcompinit = 'autoload -U bashcompinit'
zsh_autoload_colors = 'autoload -U colors'
zsh_colors = 'colors'
zsh_compinit = 'compinit -u'
zsh_bashcompinit = 'bashcompinit'

# TCSH Configuration options
tcsh_completion_regex = re.compile(r"if\s*\(\s*\$\?tcsh\s*&&\s*-r\s+\"\S*edkrepo_completions\.csh\"\s*\)\s*source\s+\"\S*edkrepo_completions\.csh\"")

# macOS pyenv launcher PATH customization (see add_pyenv_launcher_dir_to_path())
mac_local_bin_path_regex = re.compile(r"#\s+[Aa][Dd][Dd]\s+[Ee][Dd][Kk][Rr][Ee][Pp][Oo]\s+[Ll][Aa][Uu][Nn][Cc][Hh][Ee][Rr]\s+[Dd][Ii][Rr][Ee][Cc][Tt][Oo][Rr][Yy]\s+[Tt][Oo]\s+[Tt][Hh][Ee]\s+[Pp][Aa][Tt][Hh]")
mac_local_bin_path_end_regex = re.compile(r"#\s+[Ee][Nn][Dd]\s+[Ee][Dd][Kk][Rr][Ee][Pp][Oo]\s+[Ll][Aa][Uu][Nn][Cc][Hh][Ee][Rr]\s+[Pp][Aa][Tt][Hh]\s+[Cc][Uu][Ss][Tt][Oo][Mm][Ii][Zz][Aa][Tt][Ii][Oo][Nn]")
mac_local_bin_path_block = r'''
# Add EdkRepo launcher directory to the PATH
# This must be after the "eval $(pyenv init -)" block added by
# setup_git_pyenv_mac.sh, so that ~/.local/bin/edkrepo is found before
# ~/.pyenv/shims/edkrepo. The pyenv shim uses the currently active Python
# interpreter, which could potentially not be the one EdkRepo is installed in.
if [ -d "$HOME/.local/bin" ]; then
  export PATH="$HOME/.local/bin:$PATH"
fi
# End EdkRepo launcher PATH customization
'''

def default_run(cmd):
    return subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

def is_python_module_installed(python_command, module):
    '''
    True if "module" is importable in the given python interpreter, False
    otherwise.
    '''
    try:
        default_run([python_command, '-c', 'import {}'.format(module)])
        return True
    except Exception:
        return False

def run_with_externally_managed_check(cmd):
    res = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode:
        if ostype != MAC and res.stdout.find('externally-managed-environment') != -1:
            cmd.append('--break-system-packages')
            return default_run(cmd)
        else:
            raise subprocess.CalledProcessError(res.returncode, res.args, output=res.stdout, stderr=res.stderr)
    return res

def init_logger(verbose):
    logging.PRINT = 100
    logger = logging.getLogger('edkrepo_installer')
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger

def get_args():
    parser = ArgumentParser()
    if ostype != MAC:
        parser.add_argument('-l', '--local', action='store_true', default=False, help='Install edkrepo to the user directory instead of system wide')
        parser.add_argument('-s', '--system', action='store_true', default=False,
                            help='Install edkrepo system wide. Does not modify $HOME; each user must run "edkrepo setup" afterward')
        parser.add_argument('--user-setup', action='store_true', default=False,
                            help='Configure the invoking user\'s $HOME using an existing --system install. This is what "edkrepo setup" runs')
    parser.add_argument('-p', '--py', action='store', default=None, help='Specify the python command to use when installing')
    parser.add_argument('-u', '--user', action='store', default=None, help='Specify user account to install edkrepo support on')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Enables verbose output')
    parser.add_argument('--no-prompt', action='store_true', default=False, help='Do NOT add EdkRepo combo and git branch to the shell prompt')
    parser.add_argument('--prompt', action='store_true', default=False, help='Add EdkRepo combo and git branch to the shell prompt')
    parser.add_argument('--uninstall', action='store_true', default=False,
                        help='Uninstall EdkRepo instead of installing it. Requires --local, --system, or --user-setup')
    parser.add_argument('-y', '--yes', action='store_true', default=False, help='Do not prompt for confirmation before uninstalling')
    return parser.parse_args()

def check_args(args):
    check_prompt = False
    check_local = False
    user_setup = getattr(args, 'user_setup', False)
    if ostype != MAC:
        scope_flags = [args.local, args.system, user_setup]
        if sum(1 for f in scope_flags if f) > 1:
            return 'ERROR: --local, --system, and --user-setup are mutually exclusive.'
        if args.uninstall and sum(1 for f in scope_flags if f) != 1:
            return 'ERROR: --uninstall requires exactly one of --local, --system, or --user-setup.'
        if args.system and (args.prompt or args.no_prompt):
            return 'ERROR: --prompt & --no-prompt do not apply to --system installs; run "edkrepo setup" as each user instead.'
        if not args.uninstall:
            if args.local or user_setup:
                check_prompt = True
            if args.prompt or args.no_prompt:
                check_local = True
            if check_prompt and not check_local:
                return 'ERROR: --prompt or --no-prompt must be specified.'
            if check_local and not (args.local or user_setup):
                return 'ERROR: --local or --user-setup must be specified.'
    if args.prompt and args.no_prompt:
        return 'ERROR: --prompt and --no-prompt are mutually exclusive.'
    return None

def is_prompt_customization_installed(user_home_dir):
    script_files = [os.path.join(user_home_dir, '.bashrc'), os.path.join(user_home_dir, '.zshrc')]
    customization_installed = True
    for script_file in script_files:
        data = None
        if os.path.isfile(script_file):
            with open(script_file, 'r') as f:
                script = f.read().strip()
                data = prompt_regex.search(script)
        if not data:
            customization_installed = False
            break
    return customization_installed

__install_to_local = None
def get_install_to_local(args):
    global __install_to_local
    if ostype == MAC:
        raise EnvironmentError()    #This never gets used on Mac, only local install is supported on that platform
    if __install_to_local is not None:
        return __install_to_local
    if args.local:
        __install_to_local = True
        return True
    elif args.system:
        __install_to_local = False
        return False

    #If there is an existing installation of EdkRepo, install using the same mode
    edkrepo_path = shutil.which('edkrepo')
    if edkrepo_path is not None:
        if os.path.commonprefix([edkrepo_path, '/home']) == '/home':
            __install_to_local = True
            return True
        else:
            __install_to_local = False
            return False

    #Note: These imports are here because we don't want to execute these imports on Mac
    from select import select
    import termios
    import tty
    def get_key(timeout=-1):
        key = None
        old_settings = termios.tcgetattr(sys.stdin.fileno())
        try:
            tty.setraw(sys.stdin.fileno())
            if timeout != -1:
                rlist, _, _ = select([sys.stdin], [], [], timeout)
                if rlist:
                    key = sys.stdin.read(1)
            else:
                key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        return key

    #Ask the user interactively to see if they want a local or system install
    try:
        print('\n\u2554' + ('\u2550' * 22) + '\u2557')
    except UnicodeEncodeError:
        print('\n+' + ('-' * 22) + '+')
    try:
        print('\u2551 Installation Options \u2551')
    except UnicodeEncodeError:
        print('| Installation Options |')
    try:
        print('\u255a' + ('\u2550' * 22) + '\u255d')
    except UnicodeEncodeError:
        print('+' + ('-' * 22) + '+')
    print('\nSelect installation mode:\n')
    print('    1. Local Installation \033[01;36m(Recommended)\033[00m - EdkRepo is installed inside your home')
    print('                                          directory. Root access is not required')
    print('                                          and no system wide changes are made.')
    print('')
    print('    2. System Installation              - EdkRepo is installed at the system')
    print('                                          level. Root access required, but saves')
    print('                                          disk space on multi-user systems.')
    print('')
    while True:
        print('Which installation mode (1 or 2)? ')
        key = get_key()
        if key:
            if key == '1':
                print('1')
                __install_to_local = True
                return True
            if key == '2':
                print('2')
                __install_to_local = False
                return False
            else:
                print('Invalid Input')

__add_prompt_customization = None
def get_add_prompt_customization(args, username, user_home_dir):
    global __add_prompt_customization
    if __add_prompt_customization is not None:
        return __add_prompt_customization
    if args.no_prompt:
        __add_prompt_customization = False
        return False
    elif args.prompt:
        __add_prompt_customization = True
        return True
    #If the prompt customization has already been installed, upgrade it to the
    #latest version.
    if is_prompt_customization_installed(user_home_dir):
        __add_prompt_customization = True
        return True
    #If the prompt has not been installed and EdkRepo >= 2.0.0 is installed, then don't install the prompt customization
    if shutil.which('edkrepo') is not None:
        try:
            if is_current_user_root():
                res = subprocess.run("echo 'edkrepo --version; exit' | su - {}".format(username), shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
            else:
                res = default_run(['edkrepo', '--version'])
            if _check_version(res.stdout.replace('edkrepo ', '').strip(), '2.0.0') >= 0:
                __add_prompt_customization = False
                return False
        except:
            pass

    #Note: These imports are here because we don't want to execute these imports on Mac
    from select import select
    import termios
    import tty
    def get_key(timeout=-1):
        key = None
        old_settings = termios.tcgetattr(sys.stdin.fileno())
        try:
            tty.setraw(sys.stdin.fileno())
            if timeout != -1:
                rlist, _, _ = select([sys.stdin], [], [], timeout)
                if rlist:
                    key = sys.stdin.read(1)
            else:
                key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        return key

    #Ask the user interactively to see if they want the prompt customization
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
    while True:
        print('Would you like the combo and branch shown on the command prompt? [y/n] ')
        key = get_key()
        if key:
            if key == 'y' or key == 'Y':
                print('Y')
                __add_prompt_customization = True
                return True
            if key == 'n' or key == 'N':
                print('N')
                __add_prompt_customization = False
                return False
            else:
                print('Invalid Input')

def get_installed_packages(python_command):
    pip_cmd = [def_python, '-m', 'pip', 'list', '--legacy']
    try:
        res = default_run(pip_cmd)
    except:
        pip_cmd.pop(-1)
        try:
            res = default_run(pip_cmd)
        except:
            return ret_val
    installed_packages = {}
    for pip_mod in res.stdout.split('\n'):
        try:
            name, version = pip_mod.split()
            version = version.strip().strip('()')
        except:
            continue
        installed_packages[name.replace('_', '-')] = version
    return installed_packages

def get_required_wheels():
    ret_val = collections.OrderedDict()
    if platform.machine() == 'x86_64':
        python_arch = 'X64'
    else:
        python_arch = 'IA32'
    tree = et.parse(os.path.join(cfg_src_dir, 'EdkRepoInstallerConfig.xml'))
    root = tree.getroot()
    gen_py = root.find('SubstitutablePythons')
    if gen_py is not None:
        for py_type in gen_py.findall('Python'):
            if py_type.attrib['Architecture'] == python_arch:
                for wheel in py_type.findall('Wheel'):
                    ret_val[wheel.attrib['Name']] = {'wheel':wheel.attrib['Path'],
                                                    'uninstall':wheel.attrib['UninstallAllOtherCopies'].lower() == 'true',
                                                    'version':wheel.attrib['Version'],
                                                    'install':True}
                break
    for py_type in root.findall('Python'):
        if 'Architecture' not in py_type.attrib or py_type.attrib['Architecture'] == python_arch:
            for wheel in py_type.findall('Wheel'):
                ret_val[wheel.attrib['Name']] = {'wheel':wheel.attrib['Path'],
                                                 'uninstall':wheel.attrib['UninstallAllOtherCopies'].lower() == 'true',
                                                 'version':wheel.attrib['Version'],
                                                 'install':True}
            break
    installed_packages = get_installed_packages(def_python)
    for name in ret_val:
        #pip doesn't understand the difference between '_' and '-'
        if name.replace('_','-') in installed_packages:
            version = installed_packages[name.replace('_','-')]
            if _check_version(version, ret_val[name]['version']) >= 0 and not ret_val[name]['uninstall']:
                ret_val[name]['install'] = False
            else:
                ret_val[name]['uninstall'] = True
        else:
            ret_val[name]['uninstall'] = False

    return ret_val

def _check_version(current, expected):
    if current.count('.') != expected.count('.'):
        return False
    cur_s = current.split('.')
    exp_s = expected.split('.')
    for i in range(current.count('.') + 1):
        if int(cur_s[i]) < int(exp_s[i]):
            return -1
        elif int(cur_s[i]) > int(exp_s[i]):
            return 1
    return 0

def get_user_home_directory(username):
    if ostype == MAC:
        res = default_run(['dscl', '.', '-read', '/Users/{}'.format(username), 'NFSHomeDirectory'])
        data = nfs_home_directory_data.match(res.stdout.strip())
        if data:
            return data.group(1)
        else:
            raise ValueError("home directory not found")
    else:
        res = default_run(['getent', 'passwd', username])
        return res.stdout.strip().split(':')[5]

def get_site_packages_directory():
    res = default_run([def_python, '-c', 'import site; print(site.getsitepackages()[0])'])
    return res.stdout.strip()

def get_python_executable_path():
    res = default_run([def_python, '-c', 'import sys; print(sys.executable)'])
    return res.stdout.strip()

def get_python_version(python_command):
    '''
    Returns the version of the given python interpreter.
    '''
    res = default_run([python_command, '-c', 'import platform; print(platform.python_version())'])
    return res.stdout.strip()

#
# pyenv launcher support
#
# On macOS, EdkRepo uses a Python interpreter installed by pyenv. It is unlikely
# that EdkRepo is installed into every pyenv interpreter, so without help,
# EdkRepo would stop working the moment "pyenv shell" or "pyenv local" selects a
# different version. To mitigate this, shim launchers are created that
# explicitly invoke the interpreter EdkRepo is installed in.
#
_pyenv_version_from_interpreter_regex = re.compile(r"^.*/versions/([^/]+)/bin/[^/]+$")

def get_pyenv_version_name(interpreter_path):
    '''
    Returns the pyenv version name for the given interpreter. Returns None if
    not a pyenv-managed interpreter (Ex: the Apple-bundled system Python).
    '''
    if interpreter_path is None:
        return None
    match = _pyenv_version_from_interpreter_regex.match(interpreter_path.replace(os.sep, '/'))
    return match.group(1) if match else None

_pyenv_launcher_template = '''#!/bin/sh
# @file {script_name}
#  Launcher that runs "{script_name}" using the Python interpreter EdkRepo was
#  installed on (currently {pinned_version}).
#
# Automatically generated please DO NOT modify !!!
#
pyenv_root="${{PYENV_ROOT:-$HOME/.pyenv}}"
pinned="{pinned_version}"
target="$pyenv_root/versions/$pinned/bin/{script_name}"
if [ -x "$target" ]; then
    exec "$target" "$@"
fi

#
# The preferred Python version is no longer installed. Attempt to find an
# alternate Python interpreter that has "{script_name}" installed, so EdkRepo
# keeps working. If more than one Python interpreter has "{script_name}",
# choose the newest Python interpreter that matches.
#
best="$(
    for dir in "$pyenv_root"/versions/*/; do
        v=$(basename "$dir")
        candidate="$pyenv_root/versions/$v/bin/{script_name}"
        [ -x "$candidate" ] || continue
        key=$(printf '%s' "$v" | awk -F. '{{ printf "%05d%05d%05d\\n", ($1+0), ($2+0), ($3+0) }}')
        printf '%s %s\\n' "$key" "$candidate"
    done | sort | tail -n 1 | cut -d' ' -f2-
)"
if [ -n "$best" ]; then
    exec "$best" "$@"
fi

echo "error: could not find a Python interpreter with \\"{script_name}\\"" >&2
echo "Please run the EdkRepo installer again." >&2
exit 1
'''

def write_pyenv_pinned_launcher(shim_path, target_script_name, pinned_version, username, log):
    '''
    Writes a launcher shim that executes target_script_name using
    the Python interpreter that EdkRepo is installed in.
    '''
    with open(shim_path, 'w') as f:
        f.write(_pyenv_launcher_template.format(
            script_name=target_script_name, pinned_version=pinned_version).replace('\r\n', '\n'))
    shutil.chown(shim_path, user=username)
    stat_data = os.stat(shim_path)
    os.chmod(shim_path, stat_data.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return shim_path

edkrepo_python_shim_name = 'edkrepo_python'
edkrepo_python_shim_template = '''#!/bin/sh
# @file edkrepo_python
#  Launcher that runs the Python interpreter EdkRepo is installed on, so that
#  Python git hooks can "import edkrepo".
#
# Automatically generated please DO NOT modify !!!
#
exec "{interpreter}" "$@"
'''

def generate_edkrepo_python_shim(default_cfg_dir, interpreter_path, username, log):
    shim_path = os.path.join(default_cfg_dir, edkrepo_python_shim_name)
    pinned_version = get_pyenv_version_name(interpreter_path) if ostype == MAC else None
    if pinned_version is not None:
        return write_pyenv_pinned_launcher(shim_path, 'python3', pinned_version, username, log)
    with open(shim_path, 'w') as f:
        f.write(edkrepo_python_shim_template.format(interpreter=interpreter_path).replace('\r\n', '\n'))
    shutil.chown(shim_path, user=username)
    stat_data = os.stat(shim_path)
    os.chmod(shim_path, stat_data.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return shim_path

def is_current_user_root():
    if os.geteuid() == 0:
        return True
    return False

def set_execute_permissions():
    site_packages = get_site_packages_directory()
    config = configparser.ConfigParser(allow_no_value=True, delimiters='=')
    config.read(os.path.join(cfg_src_dir, 'edkrepo.cfg'))
    command_packages = [x.strip() for x in config['command-packages']['packages'].split('|')]
    for command_package in command_packages:
        package_dir = os.path.join(site_packages, command_package.split('.')[0])
        for directory in directories_with_executables:
            full_path = os.path.join(package_dir, directory)
            if os.path.isdir(full_path):
                for py_file in os.listdir(full_path):
                    if py_file == '__init__.py' or os.path.splitext(py_file)[1] != '.py':
                        continue
                    py_file = os.path.join(full_path, py_file)
                    stat_data = os.stat(py_file)
                    os.chmod(py_file, stat_data.st_mode | stat.S_IEXEC)

raspberry_pi_bashrc_workaround = r'''
# Workaround for ~/.bashrc running before ~/.profile on Raspbian
if [ -d "$HOME/.local/bin" ]; then
  export PATH="$PATH:$HOME/.local/bin"
fi
'''

bash_prompt_customization = r'''
# Add EdkRepo & git to the prompt
ps1len="${#PS1}"
let "pos3 = ps1len - 3"
let "pos2 = ps1len - 2"
let "pos16 = ps1len - 16"
if [ "${PS1:pos3}" == "\\$ " ]; then
  newps1="${PS1:0:pos3}"
  prompt_suffix="\\$ "
elif [ "${PS1:pos3}" == " $ " ]; then
  newps1="${PS1:0:pos3}"
  prompt_suffix=" $ "
elif [ "${PS1:pos2}" == "$ " ]; then
  newps1="${PS1:0:pos2}"
  prompt_suffix="$ "
elif [ "${PS1:pos16}" == " \\$\[\033[00m\] " ]; then
  newps1="${PS1:0:pos16}"
  prompt_suffix=" \[\033[01;34m\]$\[\033[00m\] "
else
  newps1="$PS1"
  prompt_suffix=""
fi

# EdkRepo combo in prompt.
if [ -x "$(command -v edkrepo)" ] && [ -x "$(command -v command_completion_edkrepo)" ]; then
  newps1="$newps1\[\033[32m\]\$current_edkrepo_combo"
  current_edkrepo_combo=$(command_completion_edkrepo current-combo)

  # Determining the current Edkrepo combo requires invoking Python and parsing
  # manifest XML, which is a relatively expensive operation to do every time
  # the user presses <Enter>.
  # As a performance optimization, only do this if the present working directory
  # changed or if the last command executed was edkrepo
  do_combo_check="0"
  edkrepo_check_last_command() {
    if [[ "$BASH_COMMAND" == *"edkrepo"* ]] && [[ "$BASH_COMMAND" != *"command_completion_edkrepo"* ]]; then
      if [[ "$BASH_COMMAND" != *"edkrepo_check_last_command"* ]]; then
        if [[ "$BASH_COMMAND" != *"edkrepo_combo_chpwd"* ]]; then
          if [[ "$BASH_COMMAND" != *"add_edkrepo_combo_to_prompt"* ]]; then
            if [[ "$BASH_COMMAND" != *"preexec_edkrepo"* ]]; then
              if [[ "$BASH_COMMAND" != *"edkrepo_debug_trap"* ]]; then
                do_combo_check="1"
              fi
            fi
          fi
        fi
      fi
    fi
  }

  # Integrate with bash-preexec if available, otherwise use direct trap
  if declare -f __bp_preexec_invoke_cmd &>/dev/null; then
    # bash-preexec is available - use its hook system
    preexec_edkrepo() {
      # Call our check with the command that's about to execute
      local cmd="$1"
      if [[ "$cmd" == *"edkrepo"* ]] && [[ "$cmd" != *"command_completion_edkrepo"* ]]; then
        if [[ "$cmd" != *"edkrepo_check_last_command"* ]]; then
          if [[ "$cmd" != *"edkrepo_combo_chpwd"* ]]; then
            if [[ "$cmd" != *"add_edkrepo_combo_to_prompt"* ]]; then
              if [[ "$cmd" != *"preexec_edkrepo"* ]]; then
                if [[ "$cmd" != *"edkrepo_debug_trap"* ]]; then
                  do_combo_check="1"
                fi
              fi
            fi
          fi
        fi
      fi
    }
    # Register with bash-preexec's hook array
    if [[ ! " ${preexec_functions[*]} " =~ " preexec_edkrepo " ]]; then
      preexec_functions+=(preexec_edkrepo)
    fi
  else
    # bash-preexec not available - preserve existing trap and add ours
    existing_debug_trap=$(trap -p DEBUG | sed -e "s/^trap -- '\\(.*\\)' DEBUG$/\\1/" -e "s/^trap -- \\\"\\(.*\\)\\\" DEBUG$/\\1/")
    edkrepo_debug_trap() {
      # Execute existing trap first if it exists
      if [[ -n "$existing_debug_trap" ]] && [[ "$existing_debug_trap" != "edkrepo_debug_trap" ]]; then
        eval "$existing_debug_trap"
      fi
      # Then execute our logic
      edkrepo_check_last_command
    }
    trap 'edkrepo_debug_trap' DEBUG
  fi
  if [[ ! -z ${PROMPT_COMMAND+x} ]] && [[ "$PROMPT_COMMAND" != "edkrepo_combo_chpwd" ]]; then
    old_prompt_command=$PROMPT_COMMAND
  fi
  old_pwd=$(pwd)
  edkrepo_combo_chpwd() {
      if [[ "$(pwd)" != "$old_pwd" ]]; then
        old_pwd=$(pwd)
        current_edkrepo_combo=$(command_completion_edkrepo current-combo)
        do_combo_check="0"
      elif [ "$do_combo_check" == "1" ]; then
        current_edkrepo_combo=$(command_completion_edkrepo current-combo)
        do_combo_check="0"
      fi
      if [[ ! -z ${PROMPT_COMMAND+x} ]]; then
        eval $old_prompt_command
      fi
  }
  PROMPT_COMMAND=edkrepo_combo_chpwd
fi

# Git branch in prompt.
parse_git_branch() {
  git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

PS1="$newps1\[\033[36m\]\$(parse_git_branch)\[\033[00m\]$prompt_suffix"
# End EdkRepo prompt customization
'''

zsh_prompt_customization = r'''
# Add EdkRepo & git to the prompt
prompt_length="${#PROMPT}"
let "pos4 = prompt_length - 3"
let "pos3 = prompt_length - 2"
if [ "${PROMPT[$pos4,$prompt_length]}" = ' %# ' ]; then
  new_prompt="${PROMPT[1,$pos4-1]}"
  prompt_suffix=" %# "
elif [ "${PROMPT[$pos3,$prompt_length]}" = "%# " ]; then
  new_prompt="${PROMPT[1,$pos3-1]}"
  prompt_suffix="%# "
else
  new_prompt="$PROMPT"
  prompt_suffix=""
fi

# EdkRepo combo in prompt.
if [ -x "$(command -v edkrepo)" ] && [ -x "$(command -v command_completion_edkrepo)" ]; then
  new_prompt="$new_prompt%{$fg[green]%}\$current_edkrepo_combo%{$reset_color%}"
  current_edkrepo_combo=$(command_completion_edkrepo current-combo)

  # Determining the current Edkrepo combo requires invoking Python and parsing
  # manifest XML, which is a relatively expensive operation to do every time
  # the user presses <Enter>.
  # As a performance optimization, only do this if the present working directory
  # changed or if the last command executed was edkrepo
  do_combo_check="0"
  function edkrepo_combo_chpwd() {
    current_edkrepo_combo=$(command_completion_edkrepo current-combo)
    do_combo_check="0"
  }
  chpwd_functions=(${chpwd_functions[@]} "edkrepo_combo_chpwd")
  function edkrepo_combo_preexec() {
    if [[ "$1" = *"edkrepo"* ]] && [[ "$1" != *"command_completion_edkrepo"* ]]; then
      if [[ "$1" != *"edkrepo_combo_preexec"* ]]; then
        if [[ "$1" != *"edkrepo_combo_chpwd"* ]]; then
          if [[ "$1" != *"edkrepo_combo_precmd"* ]]; then
            do_combo_check="1"
          fi
        fi
      fi
    fi
  }
  preexec_functions=(${preexec_functions[@]} "edkrepo_combo_preexec")
  function edkrepo_combo_precmd() {
    if [ "$do_combo_check" = "1" ]; then
      current_edkrepo_combo=$(command_completion_edkrepo current-combo)
      do_combo_check="0"
    fi
  }
  precmd_functions=(${precmd_functions[@]} "edkrepo_combo_precmd")
fi

# Load version control information
autoload -Uz vcs_info
git_precmd() { vcs_info }
precmd_functions=(${precmd_functions[@]} "git_precmd")

# Format the vcs_info_msg_0_ variable
zstyle ':vcs_info:git:*' formats " %{$fg[cyan]%}(%b)%{$reset_color%}"

# Set up the prompt (with git branch name)
setopt PROMPT_SUBST
eval "PROMPT='$new_prompt\${vcs_info_msg_0_}\$prompt_suffix'"
# End EdkRepo prompt customization
'''

#
# Legacy prompt customization blocks
#
# These are earlier versions of bash_prompt_customization and
# zsh_prompt_customization from prior versions of install.py. They are used to
# detect and remove older versions of the prompt customizations.
#
# They are stored gzip-compressed and base64-encoded, to discourage accidental
# modification.
def _decode_legacy_block(encoded):
    '''
    Decodes a gzip-compressed, base64-encoded string.
    '''
    return gzip.decompress(base64.b64decode(encoded)).decode('utf-8')

# EdkRepo: Add command completion setup to install.py (original) (9cb41d8877)
bash_prompt_customization_v1 = _decode_legacy_block('''
H4sIAAAAAAACA6VU207bQBB9368YnAhiSnAuUh/aGgkV1JemINqHSnGwjD2JVzi77q5zg+bfO7t2
yAW3lVqkkM3OmTNnbssacJkkcJ083mEu4RgmvIBCQpEi5EpO84Llupuh8J3mc+P2a3ftsAwLcHKp
++BDaYQ29Lf3vd37nsP4GIZA7uT9zritHfB9cIKgCQ6M3ptYggEIXJCXXwE7FZQMpY5Qz8ZjvvRL
P4bZb2jh31ihlrRXkf6Vs1fHWVJq3HUhjxqkw8acscZLH2I5fZDARYU7L2vYXpKSFtmmkUigPQdM
HhXBXRIHx8d1iOoY0ndO/eFShDtOrzMqD8Ew6PT7w35vGoyCZjxTCkWxcQytOJNErcF/iV8TdOPS
tlCXEUkDrrBANeWCi4mduwpjiqG2xVD4Y8YVaqrKXD4a7O2qSKUAk2keKU1Xlo5C8zHqAr4PPp/B
IuVxClxDRAxZVPA5ZivAZY5C0xlkjioyEs3UJxJwjmoFBZ+iJTN6ZhoVNQK1pugfrgWpvTi31ktD
SwRjqShqbNjIkz9ZwjOQgkIlZpkoPnWwXCrUJrmFVDaJhHKKC6lWljBOIzHBhM6m4UM4gvYT0Jjd
3Qxuv4UfbwaDyy9Xb5ZrGJUNN7O6b3TgiOZ1ryNhnOaLhNq97TeAzJKwGsKqXf4BE8FoKCvkgswt
+u/SRQ15y4VnS7sR7pToUk2zojiQ8CJjl7z8+//JKnlsAltVfyjngS6cRxk0Xxdpl3dNn30qv6Y0
1WZ/onf1QdGQpLtrbeYWQ3pzw9JW1XGyBfcuwEtw7olZlsFP0EhrjXDi3Q/vT0decmJ/ae8Ugtb5
aeB60Aq6rnfC1ozRU/Nqo9/ajW4dxnUre6dD9ube4+SwX/o1f60kBgAA
''')

# EdkRepo: Update combo displayed in shell after checkout (3a67aad9ac)
bash_prompt_customization_v2 = _decode_legacy_block('''
H4sIAAAAAAACA71V227aQBB936+YGBQuDeEm9aGtI5EmSh9KEyWtVAkTy7EHsDBed9fckvLvnbXX
YGJQq1YqEtjsnDkzs2d2lpWg53lw7U3vMeJwCmM/hphDPEGIBJ9FMYtkO8DQNMovpbuH9sZgAcZg
RFx2wYTUCA3o7tY7+fWOwfwRDIDcyfudctsYYJpgWFYZDBi+V7FCBhDikrxMDWxpKBnSPGw5H438
lZn6MQyO0MLfscJB0o4m/S1n5xBnSikx70IeB5AGG/mMlbY6uHz2xMEPNe483cPGijKpkm3mhB40
FoDeVBC8RsnB6ekhhH616RmRPj4P7ZxTsaL0xRpYrW530O3MrKFVdudCYBhnjnaSnCrioMHcxj8Q
NHNpJNAaI5ISXGGMYuaHfjhO+k5j1GaI3WYI/DH3BUralQWfKuzdOp7wEFSlkSMkLSV0FNofoYzh
e//zGSwnvjsBX4JDDIET+wsM1oCrCENJ78AjFI5KUXW9xwEXKNYQ+zNMyFQ+c4mChEApKfqH65Cy
vThPrD1FSwQjLiiqq9jI039OCM+AhxTKU4eJ4pOC6aFCqYpbcpEU4VFNbszFOiF0J044Rg+4yPCB
Q5VkguIK3XlM9qUjM/HJz9Nbb7sTdKem0VLibEVRa7aisTVNtQYvBAAVYqC6/bL38Mn+eNvv975c
Jf1eN7S3UYdh2lpF3InC2Xngtp2Ok5/kyO2iU7GW5LSoDx2Q7WND31g4EVSOV1mBq+vLbzcsy+QE
Gs9AJ/b+tn/3NUvozWqTL3DfmGRr7DU3xYmWnrGfNg88W59nHdt8xcR03glySeYq/dbyIu3It+rs
tjBBp9mUNYVR3LkCefr590N6TJpWJs12bO4j0tHZzs+Z/5aS7pY/EP9VbrhwAigXJc3zqvbbpzIP
CKlH+g1dqE+CpsMkP8/VwEKbLls7tWnVxztw5wKaHi6a4TwI4CdIOvUNhErzcfBYHzapvdU/2ayD
VT2vW7UmVK12rVlhG8bojimM8rfJKK++jlvT9laL7OW9W8lgvwBJ8KWzHQgAAA==
''')

# EdkRepo: Linux Installer Improvements (6235c33540)
bash_prompt_customization_v3 = _decode_legacy_block('''
H4sIAAAAAAACA72WbW/aQAyAv9+vcAMqLyuFwMSHdalE16r7MNaq3aRJhEZpckBEyGV34a0d/32+
5AKBBHXapEWChLP92D6fHUgJeq4LN+70gYYMTmHsRRAxiCYUQs5mYURCofs0MLTya+n+Ud9oxKcR
aCETHTAgEUIDOrv1dna9vVvXu1mB3tWIN4IBIBi5HyRwo4FhgGaaZdBgeCGjCAhAQJdoZijFllJF
QRKhJeajkbcyEjtC/SNY+DsqFELbCvoms13ELETq3TRQTMQcmK1OZ9BqzczhWy6kYUHcKUK/6LxH
ygES/Qua5SGugKKRkUdIaXtCHDZ7ZuAFSu88qWFjhXlUUTazAxcaC6DulKN6DSOH09MiDfVo4T3E
E+KxwMoY5dNNHlQOnTbmYJadOec0iFJDKw5OJlEoMLb+C5ymJo1YtUYQUoJrGlE+8wIvGMcdoXTk
ZvDdZnD6c+5xKnBXFmwqde/X0YQFIDMNbS5wKcaha29ERQQ/+l/OYDnxnAl4Amwk+HbkLai/BroK
aSDwGVhIuS1DlP3oMqALytcQeTMaw2Q8c0E5FoIKgd4/3gQY7eV5LO1JLAJGjKNXR9LQ0nuJgWfA
AnTlyjZH/1jBpN2pkMktGY+TcDEnJ2J8HQOdiR2MqQuMp/q+jZmkBaUr6swjlC9tkRYf7Vy19ZYz
oc7U0FqyONuiyDVLYiyFqdbgFRVAuhjI1rjqPX62Pt31+72v13Fv1DVlrdVhmBytvN6J1LOyitvj
dBx+koFbeaN8LnG3yAsbZHvb4CfidgiV41lW4Prm6vstSSM5gcYLYDs/3PXvv6UBvVttsgnuC+No
tb3DjX7Cpavth81811L9rHwbBySi4o41lyiu4nctW6QdfFud3RbG2kk0ZYXQ8juXgyfXvzfpsdK0
0tJsZ+y+RjJm9eyc+W8hqdPyB8U/iI0ubB/K+ZJmufL47aOMgkKqkX6Lr/pnjtNhkp3ncmBRC/8G
WIlMVX28U25fQtOli2Yw9334BQK7vkGh0nwaPNWHTTze8pdo1sGsntfNWhOqpl5rVsiGEHzH5EZ5
Nx7l1UO/tezrqrz3VtLIb46MR++3CAAA
''')

# EdkRepo: Fix Corner Case in EdkRepo Prompt Customization (a76ab9061e)
bash_prompt_customization_v4 = _decode_legacy_block('''
H4sIAAAAAAACA72WbW/aMBCAv/tXXAMqLyuFwMSHdanE1qr7MNaq3aRJhEZpYiAixJkT3trx33d2
HAgkrNMmDQlifHfP3fnOdkgJeq4L1+70noYMTmHsxRAziCcUQs5mYUzCSPdpYGjll9Ldg77RiE9j
0EIWdcCARAgN6Ozm29n59m5e72YFelcj3ggGgGDkvhPAjQaGAZpplkGD4YWIIiAAAV2imaEUW0oV
BUmEVjQfjbyVkdgR6h/Bwt9RoRDaVtBXme0iZiFS76aBYiLmwGx1OoNWa2YOX3MhDAviThH6Rect
Ug6Q6D+iWR7iCigaGXmElLYd4rDZEwMvUHrnSQ0bK8yjirKZHbjQWAB1pxzVaxg5nJ4Waaihhc8Q
O8RjgZUxyqebDFQOnTbmYJadOec0iFNDSwYnkigUGFv/BU5Tk4ZUrRGElOCKxpTPvMALxnJHKB2x
GHy3GJz+mHucRrgqCzYVunfreMICEJmGNo9wSuLQtTeiUQzf+5/PYDnxnAl4EdhI8O3YW1B/DXQV
0iDCMbCQcluEKPajy4AuKF9D7M2ohIl45hHlWAgaRej9/XWA0V6eS2lPYBEwYhy9OoKGlt6zBJ4B
C9CVK7Y5+scKJtudRiK5JeMyCRdzcmLG1xLoTOxgTF1gPNX3bcwkLShdUWceo3xpR2nx0c5VS285
E+pMDa0lirMtipizBMZSmGoNXlABhIuB2Bofeg+frI+3/X7vy5XcG3VNWWt1GCatldc7EXrHSy1N
tw123N1Jxl1BsHnMn4HUeoTLQsJvGbbr7re0FTMr2YjFrHwF5B5PP7i1c0M1kI8NfmNuh1A5vgwV
uLr+8O2GpIGfQOMZ8HC6v+3ffU3jf7PaZMu1L5TJFa7PfkrMd1WyqW/jgERU3FJzieIq/tayLbeD
b3ttt+JSO4mmrBBaflVz8OTz70fOsZK10pJtb4x9jeTS0LOn5n8Lads2rxb/IDa6sH0o50ua5Yr2
20cZBYVUF9QNvrg8cTzrJtnbSRy/1MKXGiuRqaqPd8rtS2i6dNEM5r4PPyHCM6xBodJ8HDzWh01s
b/EvatbBrJ7XzVoTqqZea1bIhhC8MXMXU1deTNVDv7Xs5Vveu2M18gv0JS7fhQkAAA==
''')

# EdkRepo: Remove Installation of Shell Trap Signal (4e3dfd0dad)
bash_prompt_customization_v5 = _decode_legacy_block('''
H4sIAAAAAAACA71XbW/bNhD+rl9xkY34pXX8NuTDOgVI26AbsKxB2gEDrESQJdoiIosqKb818377
jhRl681JmgEzkFjW3T13x7vnSBoNuPR9uPIfbknM4BTmNIGEQRIQiDlbxIkRi2FIIstsPjZuvgx3
phGSBMyYiTFYkAqhB+PD+1H+/ejwfnieFwzPTYPOYAIIjLg/S8CdCZYFpm03wYS7dzKKyACIyBrN
LK040KooSCN0xHI2oxsrtTNIeAQWXocKtaAjDfos5qgOsxZyeJ4FionYE3swHk8Gg4V995wLaVgT
dwYxfDf+CVFKkOhfkDwewtWgmMaMGkZj3yEeW0wZ0EjrnaU17G0wjzbKFm7kQ28FxH/gqN7ByOH0
tE5DPzr4HWOHUBY5OaNquumDzmE8whzsprfknERJZuio4GQStQJr77/GaWbSU6odA0Ea8JEkhC9o
RKO5YoTWkYvBD4vBybcl5UTgqqzYg9S92SYBi0BmGrtc4CsFh67pjIgE/rr+/S2sA+oFQAW4iBC6
CV2RcAtkE5NI4DOwmHBXhij56DMgK8K3kNAFUWAynqUgHAtBhEDvv1xFGO3FmZJeSlgEmDGOXj2J
hpb0uwJ8CyxCV76kOfrHCqZ0J0Imt2ZcJeFjTl7C+FYBeoEbzYkPjGf6oYuZZAUlG+ItE5SvXZEV
H+18vfSOFxDvwTIHsjj7osh3joRxNEy7A4+oANLFRFLj/eWXX50Pn6+vL//4qLjRNbW12YW7tLWq
eidS73iplem+wY67O8m5qwm2CvMyIL0e8boW4UkM1/eLLe0kzEmJWI/1JBoWXJbt+LL8QFY+mS7n
TsLd+DhMtR3UwMl/cNYc/Zn7sX/UD+prh3+qVX9DHsyROgTWNAlg6oqgp3OVqbgrl4buNCRIA4yS
r6lQTNINDzIJQyXtEy90OYHeDBxnGjvZgimeE8db+HB60ffJqh8twzCXc6PkVByc4s4nfdFEQMDY
A4itSMhCWZXqsSeDxPvghiGwJQe1cmliaiJp/iWBm7TQzZQt1f6t+ajtQ+a5IWC8OEf3a55VFV8/
RS0l/mFGleBfQaUnEZ7jUJ3xK8hTB/Ni1jyVwMvo8gLCVCjzag7tdOfekjnFluRV8rR0y7qcu9vc
mD6RR6vHbF1my8iTvSEm3bsdSqx/8F9p0eSBpph0xfqN1S4ZdQ5U10eXCtEilhSYprY0jnsp2WBO
ahfHJVf7MnaD5JNQMJk4Vxc8LCjdXgwfr97/+Qn+BoHbW4+AKfr3qagHLdtun3Vtu9NKtZp92x72
zbKabdtmpimfC8ppXtXOKPD/KuVzKZEZ5bgHYxXw0K4kosDtXoTNV5Obmed3rRybta5Xq61KVjhY
6kGMUp814CtaZpNJDbOQzamnxcenQ649VdatamR6+Q3tLuvL3ndszJvbz9c3X7N9681ml8++KCwm
np8yxcxZ6OvJkcVolZCySJTmGsVt/N/JH34O4LlCZxNDaafRNDVEzeJXwNPPfz/8Hhs/g6yo+7tL
USO9vgzz5/f/LaR9nz1b/LoWblZLmseV3VeEsmoKqa9Kn5CNU46n7iB/T5IXAeLg9dpJZbrq84Py
6AL2h4nDuGn17yf33bu+31K/RL8LapJ0+tC2h51+y9gZBt7dKlekc3VFapf9dvLXwGbhtmca/wJ1
rk59DxAAAA==
''')

# EdkRepo: Add command completion setup to install.py (original) (9cb41d8877)
zsh_prompt_customization_v1 = _decode_legacy_block('''
H4sIAAAAAAACA61Uy27bMBC88ysWshzbhR00dU9pVTRF01OCBHkABRxDkKWVREQiVZKS4xj+9y4p
O45TFeihFz3I2ZnhLndZD86SBM6TxxusJBxBxg0YCSZHqJQsK8PaV1igyEweeP66d31zdXl9t/FY
gQa8SuqPEMABDCYw3W9PO7Y/eIynMAPia+lmviUa+wfA+caj2AH0e/SYf7K2BAMQuAxbXLCPPxk7
hskJBRFmy6PrNOVPgWcpPIZFh+i0U9SzAf+mOf2L5lZS49vwNrojwmMpZ6z3Uo9YlgsJXGxxx23O
Jk90giHtlZFIYNIAJo+K4CPyC0dHXYjtZ0jvisrCpQhfBXUfcv/TX/tpNssUopj3Nw9+XCuFwuwo
QmeTQAo1GvorpOq7hHQCgxdnHXZ2IRMHHTEi6cF3NKhKLrjI3M3cYmya1D5NCn/VnCxQvhr5aLHX
K5NLATYHVaQ0LTk6kuYpagM/Ly/GsMx5nAPXEBFDERneYLECfKpQaPoGWaGKrEXbF4kEbFCtwPAS
HZn1U2tUVCLUmtQ/nwty++XY7Z5ZWiJIpSLV2LJRJH92hGOQgqQS226kT7Vt246ySIdbSuUOkdCZ
YiPVyhHGeSQyTOg7rUXsbB0kN4zzapkMR7AmyP8oAMDGFtKyhjtJHQz99Zul2df5BrwOL95oe6kv
ZJQAJU9b07EURsmCauVSYylYVBu6OgSa3D9DE+vQbtL8wbh0J3pZI0vE98MFupztNsJSZ+H7EJpI
8WhRIHvWZlUgDE53iFMacKfvBtCqamrx9nLHq8je7WF/MfrzIpPYLc2yuno1F2G45DTJ7LxcKCpt
DiIqccQokGoMbYuHt/ffbu8YNlEBXrsUDF411oO/fmOduutgJgw89hudFwYfpAUAAA==
''')

# EdkRepo: Update combo displayed in shell after checkout (3a67aad9ac)
zsh_prompt_customization_v2 = _decode_legacy_block('''
H4sIAAAAAAACA61VTW/aQBC9+1dMDASIIAqlp7RUTdX0lKhRPqRKBFnGHmCF2XV313wE8d87u7YB
g1FzyAXjnTdv3sx4Zp0K3IQh3IbTR4wFnMOYadAC9AQhlmIWayd9eBHysZ703Oq68vD4+/7heeM6
EWpwY6E+Qw8KMGhDd2fulpg/uQ4bQR+IL6XrVw1Rq1oADjYu+dahVqGfwRcjizsAHBdeiuvt/Dst
y9DukBNhMh6VjEZs2XMNhetgVBK0WxrUNQ7vi9k9ETMLqfDQPfUu8XCdEXOcyrYfgZgNBTCe4S7T
mrWXlEGDbDOfh9CeA4ZTSfAm6YXz8zJE9tejZ0xtYYJ7e07lSe5eauvqaNwfS0Q+qG1eq0EiJXKd
U3hWJoEkKtT0FglZswUpBfa2ykrk5C5tC206RFKBn6hRzhhnfGy/zAxjyiR3ZZL4N2Ekgeo1F1OD
fVjpieBgahD7UtGRpaPQbIRKw5/7uxYsJiyYAFPgE0PkazbHaAW4jJEr+g8iRukbiWYuQgE4R7kC
zWZoyYyeRKGkFqFSFP3rLSe13y6t9cbQEsFISIoaGDbyZG+WsAWCU6jQjBvFp96mY0dVpOQWQtok
Qsop0EKuLGEw8fkYQxAyx0c+ZZK3GpcYJJrsC1/lnwX5hVnpvWCCwbTnXpnmjBIe2LwK3SFIvAgb
TVgT5CM6aFhK42/MB2KCebkS1WtU1wdH/e+DDbglEt3m6RyohqYS2yzM2Jix75jJvsjZ3AsYpAOT
2c6M0du3bifjgOVsj8Y7Rh5n3HEzEw349rGxG8BKLdbg6LCsChnoP3UIZmGhDKS/qM0uu87+Fvi4
vp/ofDF9UniUfeHsRPKEodzThXkn/BBoMJWpQSC4liKiPWDHznA4fqJpLRGo/fIG80B5xujQbbdX
o+05KXu/rh0HqSEpv2xMO5o5nzdTY+/Kg7kvmT+M0HlTehUh1K9zxDWxXF/UIRWs6OZJd26w8s3K
bdSGzeP9SsGe6IpN4r3rGhoLRhesucaHkjbOBLg/w6ZDjrR6IL15vKeXH0/PDs79CNz0qFff2/ev
1fWBdFr6hauqTtH/AV3+g1Q8CAAA
''')

# EdkRepo: Fix Corner Case in EdkRepo Prompt Customization (a76ab9061e)
zsh_prompt_customization_v3 = _decode_legacy_block('''
H4sIAAAAAAACA61WTW/aQBC9+1dMDQSIIAqlp7RUTdX0lKhRPqRKBFnGHmCF2XV313wE8d87u7YB
g2lzyAWb3Tdv3szsztipwHUYwk04fcBYwBmMmQYtQE8QYilmsXbShxchH+tJz62uK/cPv+7unzau
E6EGNxbqE/SgAIM2dHfb3ZLtj67DRtAH4kvp+lVD1KoWgIONS7Z1qFXoZ/DZyOIOAMeFl+J6O/tO
yzK0O2REmIxHJaMRW/ZcQ+E6GJU47ZY6dY3B23x2T/jMXCo8NE+tSyxcZ8Qcp7KtRyBmQwGMZ7iL
NGftJUXQoL2Zz0NozwHDqSR4k/TC2VkZInv16BlTWZjg3p5ReZC7P7V1dTTujyUiH9Q2L9UgkRK5
zik8K5NAEhVq+hcJWbMJKQX2tspK5OQmbQttOkRSgR+oUc4YZ3xsT2aGMWmSuzRJ/JMwkkD5moup
wd6v9ERwMDmIfaloydKRazZCpeH33W0LFhMWTIAp8Ikh8jWbY7QCXMbIFb2DiFH6RqK5F6EAnKNc
gWYztGRGT6JQUolQKfL+5YaT2q8Xdvfa0BLBSEjyGhg2smSvlrAFgpOr0Fw38k+1Ta8dZZGCWwhp
gwgppkALubKEwcTnYwxByBwf+RRJXmpcYpBo2l/4Kj8WZBdmqfeCCQbTnntpijNKeGDjKlSHIPEi
bDRhTZD3qKBhKfW/MQfEOPNyJarXqK4PlvrfBhtwSyS6zdMxUA5NJrZRmGtjrn3H3OzznM09h0F6
YbK9D2bzdGQWv70rB7wf9oiLKo7N/meYxldi9gaPweyE5XEVOu7eNjWeo9fsxT42tlvZgIr1Olos
q1iein/XjLQXSkZxFjXbxtzZ71jvd0ZPnNJi+KTwKPrC2ongTVWaWXO/FX4I1ESUyUEguJYiop5l
W4ThcPxEUwslUPv5FeaB8symQ5N5L0fbdVL2dl07DlJDUn5an7aN5HzeTI29Sw/mvmT+MELnVelV
hFC/yhFXxHJ1XodUsKIpmc6HYOWb8dCoDZvHs4CcPdLnQBLvfVpAY8HoY8B8cgwldccJcH+GTYcM
qU1COiW9x+fvj08Ozv0I3HSpV9+bTS/V9YF0GlCFsVon738B/yGFw+gIAAA=
''')

# Tried, in order, newest first.
bash_prompt_customization_legacy_blocks = (
    bash_prompt_customization_v5,
    bash_prompt_customization_v4,
    bash_prompt_customization_v3,
    bash_prompt_customization_v2,
    bash_prompt_customization_v1,
)
zsh_prompt_customization_legacy_blocks = (
    zsh_prompt_customization_v3,
    zsh_prompt_customization_v2,
    zsh_prompt_customization_v1,
)

def get_command_completion_script_path(default_cfg_dir, user_home_dir, install_to_local):
    bash_completion_path = None
    if ostype != MAC:
        if shutil.which('pkg-config') is not None:
            try:
                res = default_run(['pkg-config', '--variable=completionsdir', 'bash-completion'])
                candidate_path = res.stdout.strip()
                if os.path.isdir(candidate_path):
                    bash_completion_path = candidate_path
            except:
                pass
        #pkg-config is broken on Ubuntu and derivatives; these heuristics make those OSes work.
        if bash_completion_path is None:
            if os.path.isfile(os.path.join('/', 'usr', 'share', 'bash-completion', 'bash_completion')):
                candidate_path = os.path.join('/', 'usr', 'share', 'bash-completion', 'completions')
                if os.path.isdir(candidate_path):
                    bash_completion_path = candidate_path

        #On local installs use the home directory
        if install_to_local and bash_completion_path is not None:
            bash_completion_path = os.path.join(user_home_dir, '.local', 'share', 'bash-completion', 'completions')
            if not os.path.isdir(bash_completion_path):
                os.makedirs(bash_completion_path)

        #If bash-completion is available, use it
        if bash_completion_path is not None:
            return (os.path.join(bash_completion_path, 'edkrepo'), False)

    #Provide a fallback for systems that do not have bash-completion
    if install_to_local or ostype == MAC:
        return (os.path.join(default_cfg_dir, 'edkrepo_completions.sh'), True)
    else:
        return (os.path.join('/', 'etc', 'profile.d', 'edkrepo_completions.sh'), True)

def get_tcsh_command_completion_script_path(default_cfg_dir):
    # Unlike bash-completion, there is no widely adopted convention for a
    # system-wide tcsh completions directory, so the script always lives
    # alongside EdkRepo's other configuration files.
    return os.path.join(default_cfg_dir, 'edkrepo_completions.csh')

def get_tcsh_startup_file(user_home_dir):
    # tcsh reads ~/.tcshrc in preference to ~/.cshrc if it exists; fall back
    # to ~/.cshrc otherwise, which will be created if neither file exists
    tcshrc_file = os.path.join(user_home_dir, '.tcshrc')
    if os.path.isfile(tcshrc_file):
        return tcshrc_file
    return os.path.join(user_home_dir, '.cshrc')

def add_command_to_startup_script(script_file, regex, command, username):
    script = ''
    if os.path.isfile(script_file):
        with open(script_file, 'r') as f:
            script = f.read().strip()
    data = regex.search(script)
    if not data:
        if script == '':
            script = command
        else:
            script = '{}\n{}'.format(script, command)
        with open(script_file, 'w') as f:
            f.write(script)

def add_command_comment_to_startup_script(script_file, regex, command, comment, username):
    script = ''
    if os.path.isfile(script_file):
        with open(script_file, 'r') as f:
            script = f.read().strip()
    (new_script, subs) = re.subn(regex, command, script)
    if subs == 0:
        command = '\n{1}\n{0}\n'.format(command, comment)
        if script == '':
            new_script = command
        else:
            new_script = '{}\n{}'.format(script, command)
    if new_script != script:
        with open(script_file, 'w') as f:
            f.write(new_script)
        shutil.chown(script_file, user=username)
        os.chmod(script_file, 0o644)

def add_command_completions_to_shell(command_completion_script, args, username, user_home_dir, source_command_completion, log):
    if ostype == MAC:
        # Add "source ~/.bashrc" to ~/.bash_profile if it does not have it already
        bash_profile_file = os.path.join(user_home_dir, '.bash_profile')
        bash_profile = ''
        if os.path.isfile(bash_profile_file):
            with open(bash_profile_file, 'r') as f:
                bash_profile = f.read().strip()
        profile_source_regex = re.compile(r"source\s+~/\.bashrc")
        profile_source_regex2 = re.compile(r".\s+~/\.bashrc")
        data = profile_source_regex.search(bash_profile)
        if not data:
            data = profile_source_regex2.search(bash_profile)
            if not data:
                if bash_profile == '':
                    bash_profile = 'source ~/.bashrc\n'
                else:
                    bash_profile = '{}\nsource ~/.bashrc\n'.format(bash_profile)
                with open(bash_profile_file, 'w') as f:
                    f.write(bash_profile)
                shutil.chown(bash_profile_file, user=username)
                os.chmod(bash_profile_file, 0o644)

    # Add edkrepo command completion to ~/.bashrc if it does not have it already
    regex = r"\[\[\s+-r\s+\"\S*edkrepo_completions.sh\"\s+\]\]\s+&&\s+.\s+\"\S*edkrepo_completions.sh\""
    new_source_line = '[[ -r "{0}" ]] && . "{0}"'.format(command_completion_script)
    comment = '\n# Add EdkRepo command completions'
    bash_rc_file = os.path.join(user_home_dir, '.bashrc')
    if source_command_completion:
        add_command_comment_to_startup_script(bash_rc_file, regex, new_source_line, comment, username)
    if get_add_prompt_customization(args, username, user_home_dir):
        # Workaround for ~/.bashrc running before ~/.profile on Raspbian
        # Note: 32-bit Raspberry Pi OS == Raspbian
        #       64-bit Raspberry Pi OS == Debian
        # This is only broken on Raspbian/32-bit Raspberry Pi OS
        if shutil.which('lsb_release') is not None:
            res = default_run(['lsb_release', '-i'])
            distributor = res.stdout.strip()
            if distributor == "Distributor ID:	Raspbian":
                add_command_to_startup_script(bash_rc_file, prompt_regex, raspberry_pi_bashrc_workaround, username)
        # Remove any existing prompt customizations before writing the new version.
        remove_marked_block_from_startup_script(
            bash_rc_file, prompt_regex, prompt_end_regex,
            (bash_prompt_customization,) + bash_prompt_customization_legacy_blocks, username, log)
        add_command_to_startup_script(bash_rc_file, prompt_regex, bash_prompt_customization, username)

    # Add edkrepo command completion to ~/.zshrc if it does not have it already and zsh is installed
    if shutil.which('zsh') is not None or ostype == MAC:
        zsh_rc_file = os.path.join(user_home_dir, '.zshrc')
        add_command_to_startup_script(zsh_rc_file, zsh_autoload_compinit_regex, zsh_autoload_compinit, username)
        add_command_to_startup_script(zsh_rc_file, zsh_autoload_bashcompinit_regex, zsh_autoload_bashcompinit, username)
        add_command_to_startup_script(zsh_rc_file, zsh_autoload_colors_regex, zsh_autoload_colors, username)
        add_command_to_startup_script(zsh_rc_file, zsh_colors_regex, zsh_colors, username)
        add_command_to_startup_script(zsh_rc_file, zsh_compinit_regex, zsh_compinit, username)
        add_command_to_startup_script(zsh_rc_file, zsh_bashcompinit_regex, zsh_bashcompinit, username)
        if source_command_completion:
            add_command_comment_to_startup_script(zsh_rc_file, regex, new_source_line, comment, username)
        if get_add_prompt_customization(args, username, user_home_dir):
            # Remove any existing prompt customizations before writing the new version.
            remove_marked_block_from_startup_script(
                zsh_rc_file, prompt_regex, prompt_end_regex,
                (zsh_prompt_customization,) + zsh_prompt_customization_legacy_blocks, username, log)
            add_command_to_startup_script(zsh_rc_file, prompt_regex, zsh_prompt_customization, username)

def add_tcsh_completion_to_shell(command_completion_csh_script, username, user_home_dir):
    # tcsh is configured independently of bash/zsh. It has different syntax for
    # command completions, so a different command completion script must be
    # generated for it.
    if shutil.which('tcsh') is None and shutil.which('csh') is None:
        return
    tcsh_rc_file = get_tcsh_startup_file(user_home_dir)
    new_source_line = 'if ($?tcsh && -r "{0}") source "{0}"'.format(command_completion_csh_script)
    comment = '\n# Add EdkRepo command completions'
    add_command_comment_to_startup_script(tcsh_rc_file, tcsh_completion_regex, new_source_line, comment, username)

def add_pyenv_launcher_dir_to_path(username, user_home_dir):
    '''
    macOS only: Adds a script block to ~/.bashrc and ~/.zshrc that inserts
    ~/.local/bin into the PATH.
    '''
    bash_rc_file = os.path.join(user_home_dir, '.bashrc')
    add_command_to_startup_script(bash_rc_file, mac_local_bin_path_regex, mac_local_bin_path_block, username)
    zsh_rc_file = os.path.join(user_home_dir, '.zshrc')
    add_command_to_startup_script(zsh_rc_file, mac_local_bin_path_regex, mac_local_bin_path_block, username)

#
# System-level install/uninstall support.
#
# A --system install does not modify $HOME. Instead, install.py and a copy of
# its configuration files are persisted so that "edkrepo setup" and "edkrepo
# uninstall --system" can be run later without needing the original installer
# package.
#
system_dir = os.path.join('/', 'usr', 'local', 'share', 'edkrepo')
_persisted_installer_files = ['install.py', 'vendor_customizer.py']

def system_installer_dir():
    return os.path.join(system_dir, 'installer')

def get_system_config_dir():
    return os.path.join(system_dir, 'config')

def persist_installer(dest_dir, username):
    '''
    Copies install.py and vendor_customizer.py (if present) into dest_dir so
    that "edkrepo setup" & "edkrepo uninstall" can run install.py later without
    needing the original installer package.
    '''
    src_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(dest_dir, exist_ok=True)
    for name in _persisted_installer_files:
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dest_dir, name)
        shutil.copyfile(src, dst)
        os.chmod(dst, 0o755 if name == 'install.py' else 0o644)
        if username is not None:
            try:
                shutil.chown(dst, user=username)
            except Exception:
                pass

def persist_config_dir(src_dir, dest_dir):
    '''
    Recursively copies the contents of src_dir into dest_dir, so that install.py
    can locate its configuration later.

    Unlike shutil.copytree(), this only copies file data and does not try to
    preserve file metadata (permissions, timestamps, ownership, etc). Preserving
    metadata can fail on some networked filesystems (Ex: NFS), even when the
    user has write access.
    '''
    os.makedirs(dest_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)
        dst = os.path.join(dest_dir, name)
        if os.path.isdir(src):
            persist_config_dir(src, dst)
        elif os.path.isfile(src):
            shutil.copyfile(src, dst)

def prepare_user_config_dir(default_cfg_dir, username, log):
    if not os.path.exists(default_cfg_dir):
        log.info('\nCreating configuration directory structure:')
        try:
            os.makedirs(default_cfg_dir)
        except:
            log.info('- Failed to create configuration directory {}'.format(default_cfg_dir))
            return False
        # Need to change the group on the directory
        try:
            shutil.chown(default_cfg_dir, user=username)
        except:
            log.info('- Unable to update owner {0}:{0} on {1}'.format(username, default_cfg_dir))
            return False
        log.info('+ Created configuration directory: {}'.format(default_cfg_dir))
    return True

def copy_config_files(cfg, sha_data, cfg_source_dir, default_cfg_dir, username, log):
    log.info('\nCopy configuration files:')
    if not os.path.isdir(cfg_source_dir):
        log.info('- Missing configuration file directory')
        return False
    for cfg_file in cfg['config_files']:
        dst_cfg_file = os.path.join(default_cfg_dir, cfg_file)
        if cfg['config_files'][cfg_file].lower() == 'true' and os.path.isfile(dst_cfg_file):
            with open(dst_cfg_file, 'rb') as f:
                current_sha_obj = hashlib.sha256(f.read())
            with open(os.path.join(cfg_source_dir, cfg_file), 'rb') as f:
                new_sha_obj = hashlib.sha256(f.read())
            if current_sha_obj.hexdigest() != new_sha_obj.hexdigest():
                if current_sha_obj.hexdigest() not in sha_data['previous_cfg_sha256']:
                    file_inc = 0
                    back_file = '{}.old{}'.format(dst_cfg_file, file_inc)
                    while os.path.isfile(back_file):
                        file_inc += 1
                        back_file = '{}.old{}'.format(dst_cfg_file, file_inc)
                    log.debug('+ Copy {} to {}'.format(dst_cfg_file, back_file))
                    try:
                        shutil.copyfile(dst_cfg_file, back_file)
                        shutil.chown(back_file, user=username)
                        os.chmod(back_file, 0o644)
                    except:
                        log.info('- Failed to create backup copy of configuration file')
                        return False
        try:
            shutil.copyfile(os.path.join(cfg_source_dir, cfg_file), dst_cfg_file)
            shutil.chown(dst_cfg_file, user=username)
            os.chmod(dst_cfg_file, 0o644)
        except:
            log.info('- Failed to copy {} to {}'.format(cfg_file, default_cfg_dir))
            return False
        log.debug('+ Copied {} to {}'.format(cfg_file, default_cfg_dir))
    log.info('+ Configuration files copy complete')
    return True

def install_wheels(args, log, whl_src_dir, install_to_local, _customizer, _context):
    '''
    Determines which wheels need to be installed (or upgraded) and installs them.
    Returns True on success.
    '''
    log.info('\nDetermining python modules to install/upgrade:')
    try:
        wheels_to_install = get_required_wheels()
    except:
        log.info('- Failed to determine installed python modules and versions')
        return False

    # Vendor customizer get_wheels() can change the wheel list.
    if _customizer is not None and hasattr(_customizer, 'get_wheels'):
        try:
            wheels_to_install = _customizer.get_wheels(_context, wheels_to_install)
        except Exception as e:
            log.info('- Vendor get_wheels failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()
            return False
    if wheels_to_install:
        log.info('+ Complete')
    else:
        log.info('+ Complete - Nothing to install')

    # Install python wheels
    if wheels_to_install:
        log.info('\nInstalling python modules:')
        if not os.path.isdir(whl_src_dir):
            log.info('- Missing wheel file directory')
            return False

        #Uninstall wheels with the UninstallAllOtherCopies attribute set
        updating_edkrepo = False
        for whl_name in wheels_to_install:
            uninstall_whl = wheels_to_install[whl_name]['uninstall']
            whl_name = whl_name.replace('_','-')  #pip doesn't understand the difference between '_' and '-'
            if uninstall_whl:
                updating_edkrepo = True
                try:
                    run_with_externally_managed_check([def_python, '-m', 'pip', 'uninstall', '--yes', whl_name])
                except:
                    log.info('- Failed to uninstall {}'.format(whl_name))
                    return False
                log.info('+ Uninstalled {}'.format(whl_name))

        #Delete obsolete dependencies
        if updating_edkrepo:
            installed_packages = get_installed_packages(def_python)
            for whl_name in ['smmap2', 'gitdb2']:
                if whl_name in installed_packages:
                    try:
                        run_with_externally_managed_check([def_python, '-m', 'pip', 'uninstall', '--yes', whl_name])
                    except:
                        log.info('- Failed to uninstall {}'.format(whl_name))
                        return False
                    log.info('+ Uninstalled {}'.format(whl_name))

        #Install new wheels
        for whl_name in wheels_to_install:
            whl = wheels_to_install[whl_name]['wheel']
            install_whl = wheels_to_install[whl_name]['install']
            if install_whl:
                install_cmd = [def_python, '-m', 'pip', 'install', '--no-index', '--find-links={}'.format(whl_src_dir)]
                if install_to_local:
                    install_cmd.append('--user')
                install_cmd.append(os.path.join(whl_src_dir, whl))
                try:
                    run_with_externally_managed_check(install_cmd)
                except:
                    log.info('- Failed to install {}'.format(whl_name))
                    return False
                log.info('+ Installed {}'.format(whl_name))

    #Mark scripts as executable
    set_execute_permissions()
    log.info('+ Marked scripts as executable')

    #If pyenv is being used, regenerate the pyenv shims
    if shutil.which('pyenv') is not None:
        try:
            res = default_run(['pyenv', 'rehash'])
            log.info('+ Generated pyenv shims')
        except:
            log.info('- Failed to generate pyenv shim')
    return True

def configure_user_home(args, username, user_home_dir, default_cfg_dir, install_to_local, _customizer, _context, log):
    '''
    Configures the invoking user's $HOME directory. Creates the edkrepo_python
    launcher, shell command completion, and the shell prompt customization.
    '''
    #Create/refresh the edkrepo_python launcher. Regenerated on every install so
    #that the launcher shim remains accurate after a Python interpreter upgrade.
    try:
        generate_edkrepo_python_shim(default_cfg_dir, get_python_executable_path(), username, log)
        log.info('+ Created edkrepo_python launcher')
    except Exception:
        log.info('- Failed to create edkrepo_python launcher')
        if args.verbose:
            traceback.print_exc()

    #Create shim launchers on macOS.
    if ostype == MAC:
        pinned_version = get_pyenv_version_name(_context.python)
        if pinned_version is not None:
            try:
                local_bin_dir = os.path.join(user_home_dir, '.local', 'bin')
                os.makedirs(local_bin_dir, exist_ok=True)
                shutil.chown(local_bin_dir, user=username)
                for script_name in ('edkrepo', 'command_completion_edkrepo'):
                    write_pyenv_pinned_launcher(
                        os.path.join(local_bin_dir, script_name), script_name, pinned_version, username, log)
                add_pyenv_launcher_dir_to_path(username, user_home_dir)
                os.environ['PATH'] = local_bin_dir + os.pathsep + os.environ['PATH']
                log.info('+ Created pyenv shim launchers in ~/.local/bin')
            except Exception:
                log.info('- Failed to create pyenv shim launchers in ~/.local/bin')
                if args.verbose:
                    traceback.print_exc()
        else:
            log.info('- Could not determine the active pyenv version; skipping pyenv shim launchers')

    #There is a possibility that ~/.local/bin is not in the PATH if ~/.local/bin
    #did not exist when the current shell was started
    if shutil.which('edkrepo') is None and install_to_local:
        os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.path.join(user_home_dir, '.local', 'bin')
        if shutil.which('edkrepo') is not None:
            if ostype == MAC:
                log.info('- Note: You may need to restart Terminal to use EdkRepo')
                log.info('        If you don\'t want to restart Terminal right now, run "export PATH=$HOME/.local/bin:$PATH"')
            else:
                log.info('- Note: You may need to reboot to use EdkRepo')
                log.info('        If you don\'t want to reboot right now, run "export PATH=$PATH:~/.local/bin"')

    #Install the command completion script
    completion_configured_by_vendor = False
    if _customizer is not None and hasattr(_customizer, 'configure_command_completion'):
        try:
            completion_configured_by_vendor = bool(_customizer.configure_command_completion(_context))
        except Exception as e:
            log.info('- Vendor configure_command_completion failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()
    if not completion_configured_by_vendor and shutil.which('edkrepo') is not None:
        (command_completion_script, source_command_completion) = \
            get_command_completion_script_path(default_cfg_dir, user_home_dir, install_to_local)
        try:
            user_is_root = False
            try:
                user_is_root = is_current_user_root()
            except:
                pass
            current_home = None
            if 'HOME' in os.environ:
                current_home = os.environ['HOME']
            try:
                if user_is_root and current_home is not None and current_home != user_home_dir:
                    os.environ['HOME'] = user_home_dir
                res = default_run(['edkrepo', 'generate-command-completion-script', command_completion_script])
            finally:
                if current_home is not None and os.environ['HOME'] != current_home:
                    os.environ['HOME'] = current_home
            if install_to_local or ostype == MAC:
                shutil.chown(command_completion_script, user=username)
                os.chmod(command_completion_script, 0o644)
            add_command_completions_to_shell(command_completion_script, args, username, user_home_dir, source_command_completion, log)
            log.info('+ Configured edkrepo command completion')
            if get_add_prompt_customization(args, username, user_home_dir) or source_command_completion:
                if ostype == MAC:
                    log.info('+ Note: You may need to restart Terminal to fully activate shell integration')
                else:
                    log.info('+ Note: You may need to reboot to fully activate shell integration')
        except:
            log.info('- Failed to configure edkrepo command completion')
            if args.verbose:
                traceback.print_exc()

        #If tcsh is installed, create the tcsh command completion script
        try:
            tcsh_completion_script = get_tcsh_command_completion_script_path(default_cfg_dir)
            if shutil.which('tcsh') is not None or shutil.which('csh') is not None:
                current_home = None
                if 'HOME' in os.environ:
                    current_home = os.environ['HOME']
                try:
                    if user_is_root and current_home is not None and current_home != user_home_dir:
                        os.environ['HOME'] = user_home_dir
                    res = default_run(['edkrepo', 'generate-command-completion-script', tcsh_completion_script, '--shell', 'tcsh'])
                finally:
                    if current_home is not None and os.environ['HOME'] != current_home:
                        os.environ['HOME'] = current_home
                if install_to_local or ostype == MAC:
                    shutil.chown(tcsh_completion_script, user=username)
                    os.chmod(tcsh_completion_script, 0o644)
                add_tcsh_completion_to_shell(tcsh_completion_script, username, user_home_dir)
                log.info('+ Configured edkrepo tcsh command completion')
        except:
            log.info('- Failed to configure edkrepo tcsh command completion')
            if args.verbose:
                traceback.print_exc()
    else:
        if not completion_configured_by_vendor:
            log.info('- Failed to configure edkrepo command completion')

#
# Uninstall support.
#
_uninstall_package_names = ('edkrepo',)

def _read_script(path):
    if os.path.isfile(path):
        with open(path, 'r') as f:
            return f.read()
    return None

_backed_up_files = set()

def _write_script_with_backup(path, new_content, username):
    '''
    Writes new_content to path, first backing up the existing file to path.oldN.
    Only the first modification made to a given path during the lifetime of this
    process creates a backup, subsequent modifications to the same path reuse
    that same backup instead of creating additional ones.
    '''
    if path not in _backed_up_files:
        file_inc = 0
        back_file = '{}.old{}'.format(path, file_inc)
        while os.path.isfile(back_file):
            file_inc += 1
            back_file = '{}.old{}'.format(path, file_inc)
        shutil.copyfile(path, back_file)
        try:
            shutil.chown(back_file, user=username)
            os.chmod(back_file, 0o644)
        except Exception:
            pass
        _backed_up_files.add(path)
    with open(path, 'w') as f:
        f.write(new_content)

def remove_regex_block_from_startup_script(script_file, regex, comment, username, log):
    '''
    Removes the line matching regex, plus an immediately preceding comment line
    if present, backing up the original file to script_file.oldN first.
    '''
    script = _read_script(script_file)
    if script is None:
        return
    lines = script.split('\n')
    comment_line = comment.strip()
    out = []
    changed = False
    for line in lines:
        if regex.search(line):
            changed = True
            if out and out[-1].strip() == comment_line:
                out.pop()
            if out and out[-1].strip() == '':
                out.pop()
            continue
        out.append(line)
    if changed:
        new_script = '\n'.join(out).strip()
        if new_script:
            new_script += '\n'
        _write_script_with_backup(script_file, new_script, username)
        log.info('+ Removed EdkRepo integration from {}'.format(script_file))

def remove_literal_block_from_startup_script(script_file, block, username, log):
    '''
    Removes a static block of text from the given file.
    '''
    script = _read_script(script_file)
    if script is None or block not in script:
        return
    new_script = script.replace(block, '')
    new_script = re.sub(r'\n{3,}', '\n\n', new_script).strip()
    if new_script:
        new_script += '\n'
    _write_script_with_backup(script_file, new_script, username)
    log.info('+ Removed EdkRepo integration from {}'.format(script_file))

def remove_marked_block_from_startup_script(script_file, begin_regex, end_regex, legacy_blocks, username, log):
    '''
    Removes an EdkRepo-managed block delimited by a line matching begin_regex
    and a later line matching end_regex.

    Using explicit begin/end markers lets this reliably remove the block even if
    it was written by an older or newer version of install.py whose block
    content differs from the one currently running.

    Installations created before the end marker was introduced won't have one.
    For those, a string-exact match against each block in legacy_blocks is
    attempted as a fallback. If neither approach can locate the block, a warning
    is logged so the user knows to remove it manually.
    '''
    script = _read_script(script_file)
    if script is None:
        return
    lines = script.split('\n')
    begin_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if begin_idx is None and begin_regex.search(line):
            begin_idx = i
            continue
        if begin_idx is not None and end_regex.search(line):
            end_idx = i
            break
    if begin_idx is None:
        return
    if end_idx is not None:
        out = lines[:begin_idx] + lines[end_idx + 1:]
        if begin_idx > 0 and out and out[begin_idx - 1].strip() == '':
            out.pop(begin_idx - 1)
        new_script = '\n'.join(out).strip()
        if new_script:
            new_script += '\n'
        _write_script_with_backup(script_file, new_script, username)
        log.info('+ Removed EdkRepo integration from {}'.format(script_file))
        return
    # No end marker: this is an installation from an older EdkRepo that
    # predates the end marker. Fall back to a string-exact match, attempting
    # each candidate legacy block.
    for legacy_block in legacy_blocks:
        if legacy_block in script:
            new_script = script.replace(legacy_block, '')
            new_script = re.sub(r'\n{3,}', '\n\n', new_script).strip()
            if new_script:
                new_script += '\n'
            _write_script_with_backup(script_file, new_script, username)
            log.info('+ Removed EdkRepo integration from {}'.format(script_file))
            return
    log.info('- Could not automatically remove the EdkRepo shell prompt integration from {}'.format(script_file))
    log.info('  It appears to have been added by an older version of EdkRepo. Please manually')
    log.info('  remove the block starting with the comment "# Add EdkRepo & git to the prompt".')

def teardown_user_home(username, user_home_dir, default_cfg_dir, log):
    '''
    Removes EdkRepo from the invoking user's $HOME directory. ~/.edkrepo is
    intentionally left as it may contain user-modified configuration files.
    '''
    log.info('\nRemoving EdkRepo shell integration:')
    completion_regex = re.compile(r"\[\[\s+-r\s+\"\S*edkrepo_completions.sh\"\s+\]\]\s+&&\s+.\s+\"\S*edkrepo_completions.sh\"")
    completion_comment = '\n# Add EdkRepo command completions'
    bash_rc_file = os.path.join(user_home_dir, '.bashrc')
    remove_regex_block_from_startup_script(bash_rc_file, completion_regex, completion_comment, username, log)
    remove_literal_block_from_startup_script(bash_rc_file, raspberry_pi_bashrc_workaround, username, log)
    remove_marked_block_from_startup_script(
        bash_rc_file, prompt_regex, prompt_end_regex,
        (bash_prompt_customization,) + bash_prompt_customization_legacy_blocks, username, log)
    if ostype == MAC:
        remove_marked_block_from_startup_script(
            bash_rc_file, mac_local_bin_path_regex, mac_local_bin_path_end_regex, (mac_local_bin_path_block,), username, log)

    if shutil.which('zsh') is not None or ostype == MAC:
        zsh_rc_file = os.path.join(user_home_dir, '.zshrc')
        remove_regex_block_from_startup_script(zsh_rc_file, completion_regex, completion_comment, username, log)
        remove_marked_block_from_startup_script(
            zsh_rc_file, prompt_regex, prompt_end_regex,
            (zsh_prompt_customization,) + zsh_prompt_customization_legacy_blocks, username, log)
        if ostype == MAC:
            remove_marked_block_from_startup_script(
                zsh_rc_file, mac_local_bin_path_regex, mac_local_bin_path_end_regex, (mac_local_bin_path_block,), username, log)

    tcsh_rc_file = get_tcsh_startup_file(user_home_dir)
    remove_regex_block_from_startup_script(tcsh_rc_file, tcsh_completion_regex, completion_comment, username, log)

    log.info('\nRemoving EdkRepo configuration files:')
    targets = [
        os.path.join(default_cfg_dir, 'edkrepo.cfg'),
        os.path.join(default_cfg_dir, edkrepo_python_shim_name),
        os.path.join(default_cfg_dir, 'edkrepo_completions.sh'),
        os.path.join(default_cfg_dir, 'edkrepo_completions.csh'),
        os.path.join(default_cfg_dir, 'installer'),
    ]
    if os.path.isdir(default_cfg_dir):
        for name in os.listdir(default_cfg_dir):
            if name.startswith('edkrepo.cfg.old'):
                targets.append(os.path.join(default_cfg_dir, name))
    for path in targets:
        try:
            if os.path.islink(path) or os.path.isfile(path):
                os.remove(path)
                log.info('+ Removed {}'.format(path))
            elif os.path.isdir(path):
                shutil.rmtree(path)
                log.info('+ Removed {}'.format(path))
        except FileNotFoundError:
            pass
        except Exception as e:
            log.info('- Failed to remove {} ({})'.format(path, e))

    bash_completion_path = os.path.join(user_home_dir, '.local', 'share', 'bash-completion', 'completions', 'edkrepo')
    if os.path.isfile(bash_completion_path):
        try:
            os.remove(bash_completion_path)
            log.info('+ Removed {}'.format(bash_completion_path))
        except Exception as e:
            log.info('- Failed to remove {} ({})'.format(bash_completion_path, e))

    if ostype == MAC:
        for script_name in ('edkrepo', 'command_completion_edkrepo'):
            launcher_path = os.path.join(user_home_dir, '.local', 'bin', script_name)
            if os.path.isfile(launcher_path):
                try:
                    os.remove(launcher_path)
                    log.info('+ Removed {}'.format(launcher_path))
                except Exception as e:
                    log.info('- Failed to remove {} ({})'.format(launcher_path, e))

def uninstall_edkrepo_packages(log, _customizer, _context):
    log.info('\nRemoving EdkRepo python packages:')
    package_names = _uninstall_package_names
    if _customizer is not None and hasattr(_customizer, 'get_uninstall_packages'):
        try:
            package_names = tuple(_customizer.get_uninstall_packages(_context, package_names))
        except Exception as e:
            log.info('- Vendor get_uninstall_packages failed: {}'.format(e))
    installed_packages = get_installed_packages(def_python)
    for name in package_names:
        pip_name = name.replace('_', '-')
        if pip_name not in installed_packages:
            continue
        try:
            run_with_externally_managed_check([def_python, '-m', 'pip', 'uninstall', '--yes', pip_name])
            log.info('+ Uninstalled {}'.format(pip_name))
        except Exception as e:
            log.info('- Failed to uninstall {} ({})'.format(pip_name, e))

def teardown_system_install(log):
    log.info('\nRemoving system-level EdkRepo installation:')
    for path in (get_system_config_dir(), system_installer_dir(),
                os.path.join('/', 'etc', 'profile.d', 'edkrepo_completions.sh')):
        try:
            if os.path.islink(path) or os.path.isfile(path):
                os.remove(path)
                log.info('+ Removed {}'.format(path))
            elif os.path.isdir(path):
                shutil.rmtree(path)
                log.info('+ Removed {}'.format(path))
        except FileNotFoundError:
            pass
        except Exception as e:
            log.info('- Failed to remove {} ({})'.format(path, e))
    if os.path.isdir(system_dir) and not os.listdir(system_dir):
        try:
            os.rmdir(system_dir)
        except OSError:
            pass
    log.log(logging.PRINT, '')
    log.log(logging.PRINT, 'Note: any per-user ~/.edkrepo directories created by "edkrepo setup" still exist.')

def do_uninstall(mode, args, log, username, user_home_dir, default_cfg_dir, _context, _customizer):
    if not args.yes:
        log.log(logging.PRINT, '')
        if mode == 'user-setup':
            prompt = 'Removing EdkRepo configuration files. To run EdkRepo after this, run "edkrepo setup" again. Continue? [y/N] '
        elif mode == 'local':
            prompt = 'This will uninstall EdkRepo. Continue? [y/N] '
        elif mode == 'system':
            prompt = 'This will uninstall EdkRepo for all users on this system. Continue? [y/N] '
        else:
            prompt = 'This will uninstall EdkRepo ({} scope). Continue? [y/N] '.format(mode)
        try:
            answer = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = 'n'
        if answer not in ('y', 'yes'):
            log.log(logging.PRINT, 'Uninstall cancelled.')
            return 1

    if _customizer is not None and hasattr(_customizer, 'pre_uninstall'):
        try:
            _customizer.pre_uninstall(_context)
        except Exception as e:
            log.info('- Vendor pre_uninstall failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()

    if mode in ('local', 'user-setup'):
        try:
            teardown_user_home(username, user_home_dir, default_cfg_dir, log)
        except Exception as e:
            log.info('- Failed to fully remove EdkRepo from the user home directory ({})'.format(e))
            if args.verbose:
                traceback.print_exc()

    if mode in ('local', 'system'):
        uninstall_edkrepo_packages(log, _customizer, _context)

    if mode == 'system':
        teardown_system_install(log)

    if _customizer is not None and hasattr(_customizer, 'post_uninstall'):
        try:
            _customizer.post_uninstall(_context)
        except Exception as e:
            log.info('- Vendor post_uninstall failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()

    log.log(logging.PRINT, '\nUninstall complete\n')
    if mode in ('local', 'user-setup'):
        log.log(logging.PRINT, 'Note: Your current shell session may still have EdkRepo shell integration loaded.')
        log.log(logging.PRINT, 'If you see errors like "command_completion_edkrepo: command not found", start a')
        log.log(logging.PRINT, 'new shell session (aka "exec $SHELL") to clear it.\n')
    if mode in ('local', 'user-setup') and default_cfg_dir is not None and os.path.isdir(default_cfg_dir):
        log.log(logging.PRINT, 'Note: {} was preserved in case it contains modified configuration'.format(default_cfg_dir))
        log.log(logging.PRINT, 'files. If you no longer need it, you may delete it:\n')
        log.log(logging.PRINT, '    rm -rf {}\n'.format(default_cfg_dir))
    return 0

def do_install():
    global def_python
    org_python = None

    # Parse command line
    args = get_args()

    # Enable logging output
    log = init_logger(args.verbose)

    _customizer = _load_vendor_customizer()
    if _customizer is not None and hasattr(_customizer, 'configure_install_args'):
        try:
            args = _customizer.configure_install_args(args, ostype)
        except Exception as e:
            log.error('ERROR: Vendor configure_install_args failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()
            return 1
        if args is None:
            log.error('ERROR: Vendor configure_install_args must return the args object, but returned None.')
            return 1

    if args.py is not None:
        org_python = def_python
        def_python = args.py

    arg_check_error = check_args(args)
    if arg_check_error is not None:
        log.error(arg_check_error)
        return 1

    try:
        cfg = configparser.ConfigParser(allow_no_value=True)
        cfg.read(os.path.join(cfg_src_dir, 'install.cfg'))
    except:
        log.error('ERROR: Missing installer configuration file.')
        return 1
    if org_python is not None:
        cfg['req_tools'][def_python] = cfg['req_tools'][org_python]
        cfg['req_tools'].pop(org_python)
    try:
        sha_data = configparser.ConfigParser(allow_no_value=True)
        sha_data.read(os.path.join(cfg_src_dir, 'sha_data.cfg'))
    except:
        log.error('ERROR: Missing installer SHA data file.')
        return 1

    # Display sign on
    product_name = _default_product_name
    if _customizer is not None and hasattr(_customizer, 'get_product_name'):
        try:
            product_name = _customizer.get_product_name()
        except Exception:
            pass
    publisher_name = _default_publisher_name
    if _customizer is not None and hasattr(_customizer, 'get_publisher'):
        try:
            publisher_name = _customizer.get_publisher()
        except Exception:
            pass
    log.log(logging.PRINT, tool_sign_on.format(product_name, cfg['version']['installer_version'], publisher_name, _copyright_year))

    # Determine which mode this run operates in:
    #   local      - Installs Edkrepo wheels to $HOME and configures the
    #                ~/.edkrepo directory.
    #   system     - Installs wheels system-wide. Doesn't create ~/.edkrepo
    #                Each user, including the administrator, must separately run
    #                "edkrepo setup" to configure the ~/.edkrepo directory,
    #                which invokes install.py --user-setup behind the scenes.
    #   user-setup - Configures the ~/.edkrepo direcotry in invoking user's
    #                $HOME using an existing system-level install. Installs no
    #                wheels. This is what "edkrepo setup" runs on Linux systems
    #                with a system install.
    if ostype == MAC:
        mode = 'local'
    elif getattr(args, 'user_setup', False):
        mode = 'user-setup'
    else:
        mode = 'local' if get_install_to_local(args) else 'system'

    install_to_local = (mode != 'system') if ostype != MAC else False

    # Set install flags to default states
    found_deps_issue = False

    username = args.user
    user_home_dir = None
    default_cfg_dir = None
    log.info('\nCollecting system information:')
    if mode == 'system':
        try:
            user_is_root = is_current_user_root()
        except:
            log.info('- Failed to determine user ID')
            return 1
        if not user_is_root:
            log.info('- Installer must be run as root')
            return 1
    else:
        if username is None:
            try:
                try:
                    username = os.getlogin()
                except OSError:
                    if not is_current_user_root():
                        username = getpass.getuser()
                    else:
                        raise
            except Exception:
                log.info('- Unable to determine current user.  Run installer using the --user flag and specify the correct user name.')
                return 1
        try:
            user_home_dir = get_user_home_directory(username)
        except:
            log.info('- Unable to determine users home directory')
            return 1
        try:
            user_is_root = is_current_user_root()
        except:
            log.info('- Failed to determine user ID')
            return 1
        if user_is_root and (args.user != 'root' or ostype == MAC):
            log.info('- Installer must NOT be run as root')
            return 1
        if ostype == MAC:
            if os.path.commonprefix([user_home_dir, sys.executable]) != user_home_dir:
                install_to_local = True
        default_cfg_dir = os.path.join(user_home_dir, cfg_dir)
        if not args.uninstall:
            get_add_prompt_customization(args, username, user_home_dir)
    log.info('+ System information collected')

    # Build the shared context object for the vendor customizer.
    _context = InstallerContext(ostype, def_python, install_to_local, log,
                                whl_src_dir, username, user_home_dir, scope=mode)

    if ostype == MAC:
        try:
            _context.python = get_python_executable_path()
        except Exception:
            pass

    # Display current system information.
    python_version = platform.python_version()
    log.debug('\nSystem Info:')
    log.debug('  System:  {}'.format(platform.platform()))
    log.debug('  Python:  {}'.format(python_version))
    log.debug('  Mode:    {}'.format(mode))
    if username is not None:
        log.debug('  User:    {}'.format(username))
    if user_home_dir is not None:
        log.debug('  Home:    {}'.format(user_home_dir))
    if default_cfg_dir is not None:
        log.debug('  CFG Dir: {}'.format(default_cfg_dir))

    if args.uninstall:
        return do_uninstall(mode, args, log, username, user_home_dir, default_cfg_dir, _context, _customizer)

    log.info('\nVerify Dependencies:')
    if user_home_dir is not None:
        if not os.path.isdir(os.path.dirname(user_home_dir)):
            log.info('- Unable to locate users home directory')
            found_deps_issue = True
        else:
            log.debug('+ Found users home directory')

    if mode != 'user-setup':
        if _check_version(python_version, cfg['version']['py_install']) < 0:
            log.info('- Installing for python {} (requires {})'.format(python_version, cfg['version']['py_install']))
            found_deps_issue = True
        else:
            log.debug('+ Installing for python {}'.format(python_version))

        # Verify that required tools are installed
        for tool in cfg['req_tools']:
            try:
                res = default_run([tool, '--version'])
            except:
                log.info('- Failed to run required tool "{}"'.format(tool))
                found_deps_issue = True
                continue
            tool_version = res.stdout.strip().split()[-1]
            if _check_version(tool_version, cfg['req_tools'][tool]) < 0:
                log.info('- {} {} detected (requires {})'.format(tool, tool_version, cfg['req_tools'][tool]))
                found_deps_issue = True
            else:
                log.debug('+ {} {} detected'.format(tool, tool_version))

        # Verify required python modules are installed
        target_python_version = None
        for module in cfg['req_py_modules']:
            if module == 'setuptools':
                # setuptools is only required to install wheels on Python 3.11
                # and older. Python 3.12 and newer no longer need it. EdkRepo
                # itself only uses pkg_resources on Python 3.7 and older, so
                # this dependency is purely based on the default environment
                # bundling behavior in older versions of Python.
                if target_python_version is None:
                    try:
                        target_python_version = get_python_version(def_python)
                    except:
                        target_python_version = python_version
                if _check_version(target_python_version, '3.12.0') >= 0:
                    log.debug('+ Python module setuptools not required on Python {}'.format(target_python_version))
                    continue
            if not is_python_module_installed(def_python, module):
                log.info('- Python module {} not found'.format(module))
                found_deps_issue = True
            else:
                log.debug('+ Python module {} detected'.format(module))

    # Exit if any dependency issues were found.
    if found_deps_issue:
        log.info('- Exiting installer due to missing dependencies.')
        return 1
    else:
        log.info('+ All dependencies verified')

    # Create required directory structure ($HOME modes only)
    if mode in ('local', 'user-setup'):
        if not prepare_user_config_dir(default_cfg_dir, username, log):
            return 1

    # Vendor customizer pre_install() initialization
    if _customizer is not None and hasattr(_customizer, 'pre_install'):
        try:
            _customizer.pre_install(_context)
        except Exception as e:
            log.info('- Vendor pre_install failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()
            return 1

    if mode == 'local':
        if not copy_config_files(cfg, sha_data, cfg_src_dir, default_cfg_dir, username, log):
            return 1

    if mode == 'user-setup':
        system_cfg_dir = get_system_config_dir()
        if not os.path.isdir(system_cfg_dir):
            log.info('- No system-level EdkRepo install was found at {}.'.format(system_dir))
            log.info('  Ask your system administrator to run the EdkRepo installer with --system.')
            return 1
        if not copy_config_files(cfg, sha_data, system_cfg_dir, default_cfg_dir, username, log):
            return 1

    if mode in ('local', 'system'):
        if not install_wheels(args, log, whl_src_dir, install_to_local, _customizer, _context):
            return 1

    if mode == 'system':
        try:
            persist_installer(system_installer_dir(), None)
            persist_config_dir(cfg_src_dir, get_system_config_dir())
            log.info('+ Persisted installer to {}'.format(system_dir))
        except Exception as e:
            log.info('- Failed to persist installer to {} ({})'.format(system_dir, e))
            if args.verbose:
                traceback.print_exc()
            return 1

    if mode in ('local', 'user-setup'):
        configure_user_home(args, username, user_home_dir, default_cfg_dir, install_to_local,
                            _customizer, _context, log)

    if mode == 'local':
        assert default_cfg_dir is not None
        try:
            installer_dest = os.path.join(default_cfg_dir, 'installer')
            persist_installer(installer_dest, username)
            installer_cfg_dest = os.path.join(installer_dest, 'config')
            persist_config_dir(cfg_src_dir, installer_cfg_dest)
            if username is not None:
                for root, dirs, files in os.walk(installer_cfg_dest):
                    for name in dirs + files:
                        try:
                            shutil.chown(os.path.join(root, name), user=username)
                        except Exception:
                            pass
            log.info('+ Persisted installer to {}'.format(installer_dest))
        except Exception as e:
            log.info('- Failed to persist installer ({})'.format(e))
            if args.verbose:
                traceback.print_exc()

    # Vendor customizer post_install() optional extras after the core install is done.
    if _customizer is not None and hasattr(_customizer, 'post_install'):
        try:
            _customizer.post_install(_context)
        except Exception as e:
            log.info('- Vendor post_install failed: {}'.format(e))
            if args.verbose:
                traceback.print_exc()

    log.log(logging.PRINT, '\nInstallation complete\n')
    if mode == 'system':
        log.log(logging.PRINT, 'IMPORTANT: This was a system-level install. EdkRepo has NOT been')
        log.log(logging.PRINT, 'configured for any individual user, including yourself. Each user')
        log.log(logging.PRINT, 'who wants to use EdkRepo, including you, must first run:\n')
        log.log(logging.PRINT, '    edkrepo setup\n')

    return 0

if __name__ == '__main__':
    ret_val = 255
    try:
        ret_val = do_install()
    except Exception:
        print('Unhandled Exception...')
        traceback.print_exc()

    sys.exit(ret_val)
