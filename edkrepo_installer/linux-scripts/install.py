#!/usr/bin/env python3
#
## @file
# install.py
#
# Copyright (c) 2018 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from argparse import ArgumentParser
import collections
import configparser
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

tool_sign_on = 'Installer for edkrepo version {}\nCopyright(c) Intel Corporation, 2020'

# Data here should be maintained in a configuration file
cfg_dir = '.edkrepo'
directories_with_executables = ['git_automation']
cfg_src_dir = os.path.abspath('config')
whl_src_dir = os.path.abspath('wheels')
def_python = 'python3'
nfs_home_directory_data = re.compile(r"NFSHomeDirectory:\s*(\S+)")

# ZSH Configuration options
prompt_regex = re.compile(r"#\s+[Aa][Dd][Dd]\s+[Ee][Dd][Kk][Rr][Ee][Pp][Oo]\s+&\s+[Gg][Ii][Tt]\s+[Tt][Oo]\s+[Tt][Hh][Ee]\s+[Pp][Rr][Oo][Mm][Pp][Tt]")
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

def default_run(cmd):
    return subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

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
    parser.add_argument('-p', '--py', action='store', default=None, help='Specify the python command to use when installing')
    parser.add_argument('-u', '--user', action='store', default=None, help='Specify user account to install edkrepo support on')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Enables verbose output')
    parser.add_argument('--no-prompt', action='store_true', default=False, help='Do NOT add EdkRepo combo and git branch to the shell prompt')
    parser.add_argument('--prompt', action='store_true', default=False, help='Add EdkRepo combo and git branch to the shell prompt')
    return parser.parse_args()

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
    #Check if the prompt customization has already been installed
    if is_prompt_customization_installed(user_home_dir):
        __add_prompt_customization = False
        return False
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
    #Show the user an advertisement to see if they want the prompt customization
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
    print('\nEdkRepo can show the checked out \033[32mcombo\033[00m and \033[36mbranch\033[00m as part of the command prompt')
    print('For example, instead of:\n')
    print('\033[01;32muser@machine\033[00m:\033[01;34mEdk2\033[00m$ ')
    print('\nThe command prompt would look like:\n')
    print('\033[01;32muser@machine\033[00m:\033[01;34mEdk2\033[00m \033[32m[Edk2Master]\033[36m (master)\033[00m$ ')
    print('')
    while True:
        print('Would you like the combo and branch shown on the command prompt? [y/N] ')
        key = get_key(120)
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
            print('No response after 2min... assuming no.')
            __add_prompt_customization = False
            return False

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
        installed_packages[name] = version
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

def is_current_user_root():
    res = default_run(['id', '-u'])
    if res.stdout.strip() == '0':
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

bash_prompt_customization = r'''
# Add EdkRepo & git to the prompt
ps1len="${#PS1}"
let "pos3 = ps1len - 3"
let "pos2 = ps1len - 2"
if [ "${PS1:pos3}" == "\\$ " ]; then
  newps1="${PS1:0:pos3}"
  prompt_suffix="\\$ "
elif [ "${PS1:pos3}" == " $ " ]; then
  newps1="${PS1:0:pos3}"
  prompt_suffix=" $ "
elif [ "${PS1:pos2}" == "$ " ]; then
  newps1="${PS1:0:pos2}"
  prompt_suffix="$ "
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
    if [[ "$BASH_COMMAND" == *"edkrepo"* ]] && [[ "$BASH_COMMAND" != *"_edkrepo"* ]]; then
      if [[ "$BASH_COMMAND" != *"edkrepo_"* ]]; then
        do_combo_check="1"
      fi
    fi
  }
  trap 'edkrepo_check_last_command' DEBUG
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
    if [[ "$1" = *"edkrepo"* ]] && [[ "$1" != *"_edkrepo"* ]]; then
      if [[ "$1" != *"edkrepo_"* ]]; then
        do_combo_check="1"
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

'''

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

def add_command_completions_to_shell(command_completion_script, args, username, user_home_dir):
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
    add_command_comment_to_startup_script(bash_rc_file, regex, new_source_line, comment, username)
    if get_add_prompt_customization(args, username, user_home_dir):
        add_command_to_startup_script(bash_rc_file, prompt_regex, bash_prompt_customization, username)
    zsh_rc_file = os.path.join(user_home_dir, '.zshrc')
    add_command_to_startup_script(zsh_rc_file, zsh_autoload_compinit_regex, zsh_autoload_compinit, username)
    add_command_to_startup_script(zsh_rc_file, zsh_autoload_bashcompinit_regex, zsh_autoload_bashcompinit, username)
    add_command_to_startup_script(zsh_rc_file, zsh_autoload_colors_regex, zsh_autoload_colors, username)
    add_command_to_startup_script(zsh_rc_file, zsh_colors_regex, zsh_colors, username)
    add_command_to_startup_script(zsh_rc_file, zsh_compinit_regex, zsh_compinit, username)
    add_command_to_startup_script(zsh_rc_file, zsh_bashcompinit_regex, zsh_bashcompinit, username)
    add_command_comment_to_startup_script(zsh_rc_file, regex, new_source_line, comment, username)
    if get_add_prompt_customization(args, username, user_home_dir):
        add_command_to_startup_script(zsh_rc_file, prompt_regex, zsh_prompt_customization, username)

def do_install():
    global def_python
    org_python = None

    # Parse command line
    args = get_args()
    if args.py is not None:
        org_python = def_python
        def_python = args.py

    # Enable logging output
    log = init_logger(args.verbose)

    # Initialize information based on command line input
    username = args.user
    install_to_local = False
    if ostype != MAC and args.local:
        install_to_local = True

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
    log.log(logging.PRINT, tool_sign_on.format(cfg['version']['installer_version']))

    # Set install flags to default states
    found_deps_issue = False

    # Determine the user running sudo
    log.info('\nCollecting system information:')
    if not install_to_local and ostype != MAC:
        try:
            user_is_root = is_current_user_root()
        except:
            log.info('- Failed to determine user ID')
            return 1
        if not user_is_root:
            log.info('- Installer must be run as root')
            return 1
    if username is None:
        try:
            res = default_run(['logname'])
            username = res.stdout.strip()
        except Exception:
            log.info('- Unable to determine current user.  Run installer using the --user flag and specify the correct user name.')
            return 1
    try:
        user_home_dir = get_user_home_directory(username)
    except:
        log.info('- Unable to determine users home directory')
        return 1
    if ostype == MAC:
        try:
            user_is_root = is_current_user_root()
        except:
            log.info('- Failed to determine user ID')
            return 1
        if user_is_root:
            log.info('- Installer must NOT be run as root')
            return 1
        if os.path.commonprefix([user_home_dir, sys.executable]) != user_home_dir:
            install_to_local = True
    default_cfg_dir = os.path.join(user_home_dir, cfg_dir)
    get_add_prompt_customization(args, username, user_home_dir)
    log.info('+ System information collected')

    # Display current system information.
    python_version = platform.python_version()
    log.debug('\nSystem Info:')
    log.debug('  System:  {}'.format(platform.platform()))
    log.debug('  Python:  {}'.format(python_version))
    log.debug('  User:    {}'.format(username))
    log.debug('  Home:    {}'.format(user_home_dir))
    log.debug('  CFG Dir: {}'.format(default_cfg_dir))

    log.info('\nVerify Dependencies:')
    if not os.path.isdir(os.path.dirname(user_home_dir)):
        log.debug('- Unable to locate users home directory')
        found_deps_issue = True
    else:
        log.debug('+ Found users home directory')

    if _check_version(python_version, cfg['version']['py_install']) < 0:
        log.debug('- Installing for python {} (requires {})'.format(python_version, cfg['version']['py_install']))
        found_deps_issue = True
    else:
        log.debug('+ Installing for python {}'.format(python_version))

    # Verify that required tools are installed
    for tool in cfg['req_tools']:
        try:
            res = default_run([tool, '--version'])
        except:
            log.debug('- Failed to run required tool {}'.format(tool))
        tool_version = res.stdout.strip().split()[-1]
        if _check_version(tool_version, cfg['req_tools'][tool]) < 0:
            log.debug('- {} {} detected (requires {})'.format(tool, tool_version, cfg['req_tools'][tool]))
            found_deps_issue = True
        else:
            log.debug('+ {} {} detected'.format(tool, tool_version))

    # Verify required python modules are installed
    for module in cfg['req_py_modules']:
        if importlib.util.find_spec(module) is None:
            log.debug('- Python module {} not found'.format(module))
            found_deps_issue = True
        else:
            log.debug('+ Python module {} detected'.format(module))

    # Exit if any dependency issues were found.
    if found_deps_issue:
        log.info('- Exiting installer due to missing dependencies.')
        return 1
    else:
        log.info('+ All dependencies verified')

    # Create required directory structure
    if not os.path.exists(default_cfg_dir):
        log.info('\nCreating configuration directory structure:')
        try:
            os.makedirs(default_cfg_dir)
        except:
            log.info('- Failed to create configuration directory {}'.format(default_cfg_dir))
            return 1
        # Need to change the group on the directory
        try:
            shutil.chown(default_cfg_dir, user=username)
        except:
            log.info('- Unable to update owner {0}:{0} on {}'.format(username, default_cfg_dir))
            return 1
        log.info('+ Created configuration directory: {}'.format(default_cfg_dir))

    # Update configuration files
    log.info('\nCopy configuration files:')
    if not os.path.isdir(cfg_src_dir):
        log.info('- Missing configuration file directory')
        return 1
    for cfg_file in cfg['config_files']:
        dst_cfg_file = os.path.join(default_cfg_dir, cfg_file)
        if cfg['config_files'][cfg_file].lower() == 'true' and os.path.isfile(dst_cfg_file):
            with open(dst_cfg_file, 'rb') as f:
                current_sha_obj = hashlib.sha256(f.read())
            with open(os.path.join(cfg_src_dir, cfg_file), 'rb') as f:
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
                        return 1
        try:
            shutil.copyfile(os.path.join(cfg_src_dir, cfg_file), dst_cfg_file)
            shutil.chown(dst_cfg_file, user=username)
            os.chmod(dst_cfg_file, 0o644)
        except:
            log.info('- Failed to copy {} to {}'.format(cfg_file, default_cfg_dir))
            return 1
        log.debug('+ Copied {} to {}'.format(cfg_file, default_cfg_dir))
    log.info('+ Configuration files copy complete')

    # Determining wheels that need to be installed for the current system
    log.info('\nDetermining python modules to install/upgrade:')
    try:
        wheels_to_install = get_required_wheels()
    except:
        log.info('- Failed to determine installed python modules and versions')
        return 1
    if wheels_to_install:
        log.info('+ Complete')
    else:
        log.info('+ Complete - Nothing to install')

    # Install python wheels
    if wheels_to_install:
        log.info('\nInstalling python modules:')
        if not os.path.isdir(whl_src_dir):
            log.info('- Missing wheel file directory')
            return 1
        updating_edkrepo = False
        for whl_name in wheels_to_install:
            uninstall_whl = wheels_to_install[whl_name]['uninstall']
            whl_name = whl_name.replace('_','-')  #pip doesn't understand the difference between '_' and '-'
            if uninstall_whl:
                updating_edkrepo = True
                try:
                    res = default_run([def_python, '-m', 'pip', 'uninstall', '--yes', whl_name])
                except:
                    log.info('- Failed to uninstall {}'.format(whl_name))
                    return 1
                log.info('+ Uninstalled {}'.format(whl_name))

        #Delete obsolete dependencies
        if updating_edkrepo:
            installed_packages = get_installed_packages(def_python)
            for whl_name in ['smmap2', 'gitdb2', 'edkrepo-internal']:
                if whl_name in installed_packages:
                    try:
                        res = default_run([def_python, '-m', 'pip', 'uninstall', '--yes', whl_name])
                    except:
                        log.info('- Failed to uninstall {}'.format(whl_name))
                        return 1
                    log.info('+ Uninstalled {}'.format(whl_name))
        for whl_name in wheels_to_install:
            whl = wheels_to_install[whl_name]['wheel']
            install_whl = wheels_to_install[whl_name]['install']
            if install_whl:
                install_cmd = [def_python, '-m', 'pip', 'install', '--no-index', '--find-links={}'.format(whl_src_dir)]
                if install_to_local:
                    install_cmd.append('--user')
                install_cmd.append(os.path.join(whl_src_dir, whl))
                try:
                    default_run(install_cmd)
                except:
                    log.info('- Failed to install {}'.format(whl_name))
                    return 1
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

    #Install the command completion script
    if shutil.which('edkrepo') is not None:
        if install_to_local or ostype == MAC:
            command_completion_script = os.path.join(default_cfg_dir, 'edkrepo_completions.sh')
        else:
            command_completion_script = os.path.join('/', 'etc', 'profile.d', 'edkrepo_completions.sh')
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
            add_command_completions_to_shell(command_completion_script, args, username, user_home_dir)
            log.info('+ Configured edkrepo command completion')
        except:
            log.info('- Failed to configure edkrepo command completion')
            if args.verbose:
                traceback.print_exc()

    log.log(logging.PRINT, '\nInstallation complete\n')

    return 0

if __name__ == '__main__':
    ret_val = 255
    try:
        ret_val = do_install()
    except Exception:
        print('Unhandled Exception...')
        traceback.print_exc()

    sys.exit(ret_val)
