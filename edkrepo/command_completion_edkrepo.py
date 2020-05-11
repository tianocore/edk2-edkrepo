#!/usr/bin/env python3
#
## @file
# command_completion_edkrepo.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import argparse
import io
import os
import sys
import traceback

from edkrepo_manifest_parser.edk_manifest import ManifestXml
from edkrepo.common.common_repo_functions import combinations_in_manifest
from edkrepo.common.edkrepo_exception import EdkrepoManifestNotFoundException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import find_source_manifest_repo
from edkrepo.config import config_factory
from edkrepo.config.config_factory import get_workspace_manifest

def checkout(parsed_args, config):
    manifest = get_workspace_manifest()
    print(' '.join(combinations_in_manifest(manifest)))

def current_combo(parsed_args, config):
    manifest = get_workspace_manifest()
    print(" [{}]".format(manifest.general_config.current_combo))

def checkout_pin(parsed_args, config):
    pins = []
    manifest = get_workspace_manifest()
    manifest_directory = None
    try:
        source_manifest_repo = find_source_manifest_repo(manifest, config['cfg_file'], config['user_cfg_file'], )
        if source_manifest_repo:
            cfg, user_cfg, conflicts = list_available_manifest_repos(config['cfg_file'], config['user_cfgFile'])
            if source_manifest_repo in cfg:
                manifest_directory = config['cfg_file'].manifest_repo_abs_path(source_manifest_repo)
            elif source_manifest_repo in user_cfg:
                manifest_directory = config['user_cfg_file'].manifest_repo_abs_path(source_manifest_repo)
            else:
                manifest_directory = None
    except EdkrepoManifestNotFoundException:
        manifest_directory = None
    if manifest_directory:
        pin_folder = os.path.normpath(os.path.join(manifest_directory, manifest.general_config.pin_path))
        for dirpath, _, filenames in os.walk(pin_folder):
            for file in filenames:
                pin_file = os.path.join(dirpath, file)
                # Capture error output from manifest parser stdout so it is hidden unless verbose is enabled
                stdout = sys.stdout
                sys.stdout = io.StringIO()
                pin = ManifestXml(pin_file)
                parse_output = sys.stdout.getvalue()
                sys.stdout = stdout
                if parsed_args.verbose and parse_output.strip() != '':
                    print('Pin {} Parsing Errors: {}\n'.format(file, parse_output.strip()))
                if pin.project_info.codename == manifest.project_info.codename:
                    pins.append(file)
        print(' '.join(pins))

# To add command completions for a new command, add an entry to this dictionary.
command_completions = {
    'current-combo': current_combo,
    'checkout': checkout,
    'checkout-pin': checkout_pin,
    'chp': checkout_pin
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help='Increases command verbosity')
    subparsers = parser.add_subparsers(dest='subparser_name')
    for command_completion in command_completions:
        subparsers.add_parser(command_completion, formatter_class=argparse.RawTextHelpFormatter)
    if len(sys.argv) <= 1:
        return 0
    parsed_args = parser.parse_args()
    try:
        command_name = parsed_args.subparser_name
        config = {}
        config["cfg_file"] = config_factory.GlobalConfig()
        config["user_cfg_file"] = config_factory.GlobalUserConfig()
        if command_name not in command_completions:
            return 1
        command_completions[command_name](parsed_args, config)
        return 0
    except Exception as e:
        if parsed_args.verbose:
            traceback.print_exc()
            print("Error: {}".format(str(e)))
        return 1
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
