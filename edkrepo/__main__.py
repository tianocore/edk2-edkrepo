#!/usr/bin/env python3
#
## @file
# __main__.py.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import os
import sys
import site
import traceback

#Prefer the site-packages version of edkrepo
sitepackages = site.getsitepackages()
sys.path = sitepackages + sys.path
import edkrepo
edkrepo_package_path = os.path.dirname(os.path.dirname(edkrepo.__file__))
for directory in sitepackages:
    if edkrepo_package_path == directory:
        edkrepo_site_dir = edkrepo_package_path
        break
else:
    importlib.reload(edkrepo)
import edkrepo.edkrepo_entry_point

if __name__ == '__main__':
    try:
        sys.exit(edkrepo.edkrepo_entry_point.main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
