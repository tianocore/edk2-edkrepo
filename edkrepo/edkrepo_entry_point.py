#!/usr/bin/env python3
#
## @file
# edkrepo_entry_point.py
#
# Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import argparse
import importlib
import importlib.util
import inspect
import json
import os
import site
import subprocess
import sys
import time
import traceback
from operator import itemgetter

from git.exc import GitCommandError

import edkrepo

#Prefer the site-packages version of edkrepo
sitepackages = site.getsitepackages()
if site.ENABLE_USER_SITE:
    sitepackages.append(site.getusersitepackages())
sys.path = sitepackages + sys.path
edkrepo_site_dir = None
edkrepo_package_path = os.path.dirname(os.path.dirname(edkrepo.__file__))
for directory in sitepackages:
    if edkrepo_package_path == directory:
        edkrepo_site_dir = edkrepo_package_path
        break
else:
    importlib.reload(edkrepo)
    edkrepo_package_path = os.path.dirname(os.path.dirname(edkrepo.__file__))
    for directory in sitepackages:
        if edkrepo_package_path == directory:
            edkrepo_site_dir = edkrepo_package_path
            break
if edkrepo_site_dir is None:
    print('Running EdkRepo from local source')

#Determine if this module is being imported by the launcher script
run_via_launcher_script = False
importer = ""
importer_file = ""
f = inspect.currentframe().f_back
while f is not None:
    if f.f_globals.get('__name__').find('importlib') == -1:
        importer = f.f_globals.get('__name__')
        importer_file = f.f_globals.get('__file__')
        if importer_file is None:
            importer_file = ""
        break
    f = f.f_back
if importer == "__main__":
    if os.path.basename(importer_file).lower() == "__main__.py":
        if os.path.basename(os.path.dirname(importer_file)).lower().find('edkrepo') != -1:
            run_via_launcher_script = True
    elif os.path.basename(importer_file).lower().find('edkrepo') != -1:
        run_via_launcher_script = True

if __name__ == "__main__" or run_via_launcher_script:
    #If this module is the entrypoint, we need to make
    #sure that the site-packages version is being executed
    if edkrepo_site_dir is not None and os.path.commonprefix([edkrepo_site_dir, __file__]) != edkrepo_site_dir:
        edkrepo_cli_file_name = os.path.join(edkrepo_site_dir, 'edkrepo', 'edkrepo_entry_point.py')
        if os.path.isfile(edkrepo_cli_file_name):
                spec = importlib.util.spec_from_file_location('edkrepo.edkrepo_entry_point.py', edkrepo_cli_file_name)
                edkrepo_entry_point = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(edkrepo_entry_point)
                try:
                    sys.exit(edkrepo_entry_point.main())
                except Exception as e:
                    traceback.print_exc()
                    sys.exit(1)

from edkrepo.config.config_factory import GlobalConfig

def main():
    cfg_file = GlobalConfig()
    pref_entry = (cfg_file.preferred_entry[0]).replace('.py', '')
    pref_entry_func = cfg_file.preferred_entry[1]

    try:
        mod = importlib.import_module(pref_entry)
        func = getattr(mod, pref_entry_func)
        return(func())
    except Exception as e:
        print('Unable to launch preferred entry point. Launching default entry point edkrepo.edkrepo_cli.py')
        traceback.print_exc()
        import edkrepo.edkrepo_cli
        return edkrepo.edkrepo_cli.main()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
