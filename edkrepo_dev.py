#!/usr/bin/env python3
#
## @file
# edkrepo_dev.py
#
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import traceback
if sys.version_info >= (3, 8):
    from importlib.metadata import version
else:
    import pkg_resources
from edkrepo.config.config_factory import GlobalConfig
from edkrepo.common.edkrepo_exception import EdkrepoGlobalConfigNotFoundException
from edkrepo import edkrepo_cli

if __name__ == '__main__':
    # Run the edkrepo command line interface without building and running the edkrepo installer.
    # Minimum Python version and Git version in README.md
    # Additional Python requirements in edkrepo_dev_requirements_windows.txt
    # EdkRepo 'git bash' features support require the installer to use.
    try:
        # If a global config file was not installed, do not continue further.
        GlobalConfig()
    except EdkrepoGlobalConfigNotFoundException as e:
        traceback.print_exc()
        print()
        print("Create a global edkrepo.cfg file before running edkrepo_dev.py.")
        print("example global config file: edk2-edkrepo/edkrepo_installer/Vendor/edkrepo.cfg")
        sys.exit(102)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

    try:
        # If system has edkrepo installed, exit
        if sys.version_info >= (3, 8):
            edkrepo_version = version("edkrepo")
        else:
            edkrepo_version = pkg_resources.get_distribution("edkrepo").version
        print("Edkrepo is found installed on the system. Edkrepo version: ", edkrepo_version)
        print("Run the edkrepo uninstaller before using 'edkrepo_dev.py'.")
        sys.exit(1)
    except:
        print("edkrepo running from development source.")

    try:
        sys.exit(edkrepo_cli.main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
