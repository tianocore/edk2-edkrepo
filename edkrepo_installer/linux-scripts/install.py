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
import stat
import shutil
import subprocess
import sys
import traceback
import xml.etree.ElementTree as et

tool_sign_on = 'Installer for edkrepo version {}\nCopyright(c) Intel Corporation, 2019'

# Data here should be maintained in a configuration file
cfg_dir = '.edkrepo'
directories_with_executables = ['git_automation']
cfg_src_dir = os.path.abspath('config')
whl_src_dir = os.path.abspath('wheels')
def_python = 'python3'

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
    parser.add_argument('-l', '--local', action='store_true', default=False, help='Install edkrepo to the user directory instead of system wide')
    parser.add_argument('-p', '--py', action='store', default=None, help='Specify the python command to use when installing')
    parser.add_argument('-u', '--user', action='store', default=None, help='Specify user account to install edkrepo support on')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Enables verbose output')
    return parser.parse_args()

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

def get_site_packages_directory():
    res = default_run([def_python, '-c', 'import site; print(site.getsitepackages()[0])'])
    return res.stdout.strip()

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
    if not args.local:
        try:
            res = default_run(['id', '-u'])
        except:
            log.info('- Failed to determine user ID')
            return 1
        if res.stdout.strip() != '0':
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
        res = default_run(['getent', 'passwd', username])
        user_home_dir = res.stdout.strip().split(':')[5]
    except:
        log.info('- Unable to determine users home directory')
        return 1
    default_cfg_dir = os.path.join(user_home_dir, cfg_dir)
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
            for whl_name in ['smmap2', 'gitdb2']:
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
                install_cmd = [def_python, '-m', 'pip', 'install']
                if args.local:
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
