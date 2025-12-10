#!/usr/bin/env python3
#
## @file
# build_linux_installer.py
#
# Copyright (c) 2018 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from argparse import ArgumentParser
import configparser
import fnmatch
import os
import shutil
import sys
import tarfile
import traceback

import set_version_and_build_wheels as build_edkrepo

def get_version_info(build=None):
    build_num = 0
    if build:
        os.environ['BUILD_NUMBER'] = build
    if 'BUILD_NUMBER' in os.environ:
        build_num = os.environ['BUILD_NUMBER']
    ver_cfg = os.path.join(os.path.dirname(__file__), "version_numbers.ini")
    cfg = configparser.ConfigParser()
    cfg.read(ver_cfg)
    return '{}.{}'.format(cfg['edkrepo']['version'], build_num)

def copy_files(dist_root):
    inst_root = os.path.abspath(os.path.join('..', 'edkrepo_installer'))
    ven_root = os.path.join(inst_root, 'Vendor')
    linux_root = os.path.join(inst_root, 'linux-scripts')
    for f in os.listdir(ven_root):
        if fnmatch.fnmatch(f, '*.whl'):
            shutil.copyfile(os.path.join(ven_root, f), os.path.join(dist_root, 'wheels', f))
        elif fnmatch.fnmatch(f, '*.cfg'):
            shutil.copyfile(os.path.join(ven_root, f), os.path.join(dist_root, 'config', f))
    for f in [x for x in os.listdir(dist_root) if fnmatch.fnmatch(x, '*.whl')]:
        shutil.move(os.path.join(dist_root, f), os.path.join(dist_root, 'wheels', f))
    shutil.copyfile(os.path.join(inst_root, 'EdkRepoInstallerConfig.xml'), os.path.join(dist_root, 'config', 'EdkRepoInstallerConfig.xml'))
    shutil.copyfile(os.path.join(inst_root, 'sha_data.cfg'), os.path.join(dist_root, 'config', 'sha_data.cfg'))
    shutil.copyfile(os.path.join(linux_root, 'install.cfg'), os.path.join(dist_root, 'config', 'install.cfg'))
    shutil.copyfile(os.path.join(linux_root, 'install.py'), os.path.join(dist_root, 'install.py'))

def patch_installer_config(dist_root, version):
    install_cfg_path = os.path.join(dist_root, 'config', 'install.cfg')
    install_cfg = configparser.ConfigParser(allow_no_value=True)
    install_cfg.read(install_cfg_path)
    install_cfg['version']['installer_version'] = version
    with open(install_cfg_path, 'w') as f:
        install_cfg.write(f)

def mode_change(tarinfo):
    rwx_files = ['./install.py']
    if tarinfo.name in rwx_files:
        tarinfo.mode = 0o755
    elif tarinfo.isfile():
        tarinfo.mode = 0o644
    else:
        tarinfo.mode = 0o755
    return tarinfo

def create_archive(version):
    cwd = os.getcwd()
    os.chdir(os.path.join('..', 'dist'))
    shutil.move('self_extract', 'edkrepo-{}'.format(version))
    os.makedirs('self_extract')
    shutil.move('edkrepo-{}'.format(version), os.path.join('self_extract', 'edkrepo-{}'.format(version)))
    os.chdir('self_extract')
    with tarfile.open(os.path.join('..', 'edkrepo-{}.tar.gz'.format(version)), 'w:gz') as out_targz:
        out_targz.add('.', filter=mode_change)
    os.chdir(cwd)

def main():
    parser = ArgumentParser()
    parser.add_argument('-b', '--build', action='store', default=None, help='Specifies the build number to use for the installer package.')
    args = parser.parse_args()

    # Initialize environment variables and version information.
    try:
        version = get_version_info(args.build)
        print('Creating Linux installer version {}'.format(version))
    except Exception:
        print('Failed to get version number')

    # Create required directory structure
    dist_root = os.path.abspath(os.path.join('..', 'dist', 'self_extract'))
    if not os.path.isdir(os.path.join(dist_root, 'wheels')):
        os.makedirs(os.path.join(dist_root, 'wheels'))
    if not os.path.isdir(os.path.join(dist_root, 'config')):
        os.makedirs(os.path.join(dist_root, 'config'))

    # Build edkrepo
    try:
        build_edkrepo.build('linux')
    except:
        traceback.print_exc()
        print('Failed to build edkrepo wheel')
        return 1

    # Copy required files
    try:
        copy_files(dist_root)
        print('Files copied successfully')
    except:
        print('Failed to copy files')
        return 1

    # Update installer files
    try:
        patch_installer_config(dist_root, version)
        print('Installer version number updated successfully')
    except Exception:
        print('Failed to update installer version to {}'.format(version))
        return 1

    # Package installer files
    try:
        create_archive(version)
        print('Generated installer archive file successfully')
    except:
        print('Failed to generate installer package')
        return 1

    # Clean up temporary files
    try:
        shutil.rmtree(dist_root, ignore_errors=True)
        print('Removed temporary files successfully')
    except:
        print('Failed to remove temporary files')

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('Unhandled Exception: {}'.format(e))
        sys.exit(255)
