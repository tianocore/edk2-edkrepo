#!/usr/bin/env bash
#
## @file setup_git_pyenv_mac.sh
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

IFS='' read -r -d '' python_script <<"EOF"
import os
import re
import subprocess
import sys
import traceback

profile_source_regex = re.compile(r"source\s+~/\.bashrc")
profile_source_regex2 = re.compile(r".\s+~/\.bashrc")

ls_alias_regex = re.compile(r"alias\s+ls='ls\s+-G'")
bash_completion_regex = re.compile(r"\[\[\s+-r\s+\"/usr/local/etc/profile.d/bash_completion.sh\"\s+\]\]\s+&&\s+.\s+\"/usr/local/etc/profile.d/bash_completion.sh\"")
zsh_autoload_compinit_regex = re.compile(r"autoload\s+-U\s+compinit")
zsh_autoload_bashcompinit_regex = re.compile(r"autoload\s+-U\s+bashcompinit")
zsh_autoload_colors_regex = re.compile(r"autoload\s+-U\s+colors")
zsh_colors_regex = re.compile(r"\n\s*colors\n")
zsh_compinit_regex = re.compile(r"compinit\s+-u")
zsh_bashcompinit_regex = re.compile(r"\n\s*bashcompinit\n")
pyenv_init_regex = re.compile(r"eval\s+\"\$\(pyenv\s+init\s+-\)\"")

ls_alias = "alias ls='ls -G'"
bash_completion = '[[ -r "/usr/local/etc/profile.d/bash_completion.sh" ]] && . "/usr/local/etc/profile.d/bash_completion.sh"'

zsh_autoload_compinit = 'autoload -U compinit'
zsh_autoload_bashcompinit = 'autoload -U bashcompinit'
zsh_autoload_colors = 'autoload -U colors'
zsh_colors = 'colors'
zsh_compinit = 'compinit -u'
zsh_bashcompinit = 'bashcompinit'

pyenv_init = '''
# Use the pyenv intalled Python interperter
if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi
'''

def add_command_to_startup_script(script_file, regex, command):
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

def main():
    home_dir = os.path.expanduser('~')

    # Add "source ~/.bashrc" to ~/.bash_profile if it does not have it already
    bash_profile_file = os.path.join(home_dir, '.bash_profile')
    bash_profile = ''
    if os.path.isfile(bash_profile_file):
        with open(bash_profile_file, 'r') as f:
            bash_profile = f.read().strip()
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

    # Add pyenv configuration to ~/.bashrc if it does not have it already
    bash_rc_file = os.path.join(home_dir, '.bashrc')
    add_command_to_startup_script(bash_rc_file, ls_alias_regex, ls_alias)
    add_command_to_startup_script(bash_rc_file, bash_completion_regex, bash_completion)
    add_command_to_startup_script(bash_rc_file, pyenv_init_regex, pyenv_init)
    zsh_rc_file = os.path.join(home_dir, '.zshrc')
    add_command_to_startup_script(zsh_rc_file, ls_alias_regex, ls_alias)
    add_command_to_startup_script(zsh_rc_file, zsh_autoload_compinit_regex, zsh_autoload_compinit)
    add_command_to_startup_script(zsh_rc_file, zsh_autoload_bashcompinit_regex, zsh_autoload_bashcompinit)
    add_command_to_startup_script(zsh_rc_file, zsh_autoload_colors_regex, zsh_autoload_colors)
    add_command_to_startup_script(zsh_rc_file, zsh_colors_regex, zsh_colors)
    add_command_to_startup_script(zsh_rc_file, zsh_compinit_regex, zsh_compinit)
    add_command_to_startup_script(zsh_rc_file, zsh_bashcompinit_regex, zsh_bashcompinit)
    add_command_to_startup_script(zsh_rc_file, bash_completion_regex, bash_completion)
    add_command_to_startup_script(zsh_rc_file, pyenv_init_regex, pyenv_init)

    print('Pyenv configured successfully')
    return 0

if __name__ == '__main__':
    ret_val = 255
    try:
        ret_val = main()
    except Exception:
        print('Unhandled Exception...')
        traceback.print_exc()

    sys.exit(ret_val)
EOF

# On Catalina and later python3 is preferred,
# however it is not packaged by Apple on earlier OSes
if [ -x "$(command -v python3)" ]; then
    python3 -c "$python_script"
    exit $?
else
    python -c "$python_script"
    exit $?
fi
