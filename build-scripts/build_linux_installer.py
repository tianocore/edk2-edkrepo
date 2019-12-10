#!/usr/bin/env python3
#
## @file
# build_linux_installer.py
#
# Copyright (c) 2018 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from argparse import ArgumentParser
import fnmatch, os, shutil, subprocess, sys
import set_version_and_build_wheels as build_edkrepo
import traceback

def main():
    parser = ArgumentParser()
    parser.add_argument('-b', '--build', action='store', default=None, help='Specifies the build number to use for the installer package.')
    args = parser.parse_args()

    # Step 0: Initialize environment variables as needed for build scripts
    if args.build:
        os.environ['BUILD_NUMBER'] = args.build

    # Step 1: Create required directory structure
    dist_root = os.path.abspath(os.path.join('..', 'dist', 'self_extract'))
    if not os.path.isdir(os.path.join(dist_root, 'wheels')):
        os.makedirs(os.path.join(dist_root, 'wheels'))
    if not os.path.isdir(os.path.join(dist_root, 'config')):
        os.makedirs(os.path.join(dist_root, 'config'))

    # Step 2: Build edkrepo
    try:
        build_edkrepo.main()
    except:
        traceback.print_exc()
        print('Failed to build edkrepo wheel')
        return 1

    # Step 3: Copy required files
    inst_root = os.path.abspath(os.path.join('..', 'edkrepo_installer'))
    ven_root = os.path.join(inst_root, 'Vendor')
    linux_root = os.path.join(inst_root, 'linux-scripts')
    try:
        for f in os.listdir(ven_root):
            if fnmatch.fnmatch(f, '*.whl'):
                shutil.copyfile(os.path.join(ven_root, f), os.path.join(dist_root, 'wheels', f))
            elif fnmatch.fnmatch(f, '*.cfg'):
                shutil.copyfile(os.path.join(ven_root, f), os.path.join(dist_root, 'config', f))
        shutil.copyfile(os.path.join(inst_root, 'EdkRepoInstallerConfig.xml'), os.path.join(dist_root, 'config', 'EdkRepoInstallerConfig.xml'))
        shutil.copyfile(os.path.join(inst_root, 'sha_data.cfg'), os.path.join(dist_root, 'config', 'sha_data.cfg'))
        shutil.copyfile(os.path.join(linux_root, 'install.cfg'), os.path.join(dist_root, 'config', 'install.cfg'))
        shutil.copyfile(os.path.join(linux_root, 'install.py'), os.path.join(dist_root, 'install.py'))
        os.chmod(os.path.join(dist_root, 'install.py'), 0o755)
    except:
        print('Failed to copy files')
        return 1

    # Step 4: Package installer files
    try:
        subprocess.run(os.path.join('.', 'final_copy.py'), check=True)
    except:
        print('Failed to generate installer package')
        return 1

    # Step 5: Clean up temporary files
    try:
        shutil.rmtree(dist_root, ignore_errors=True)
    except:
        print('Failed to remove temporary files')
    os.unlink('final_copy.py')

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('Unhandled Exception: {}'.format(e))
        sys.exit(255)
