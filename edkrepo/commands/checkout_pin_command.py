#!/usr/bin/env python3
#
## @file
# checkout_pin_command.py
#
# Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

from git import Repo

from edkrepo.commands.edkrepo_command import EdkrepoCommand, OverrideArgument
import edkrepo.commands.arguments.checkout_pin_args as arguments
import edkrepo.commands.humble.checkout_pin_humble as humble
from edkrepo.common.common_repo_functions import sparse_checkout_enabled, reset_sparse_checkout, sparse_checkout
from edkrepo.common.common_repo_functions import check_dirty_repos, checkout_repos
from edkrepo.common.humble import SPARSE_CHECKOUT, SPARSE_RESET
from edkrepo.common.edkrepo_exception import EdkrepoInvalidParametersException, EdkrepoProjectMismatchException
from edkrepo.config.config_factory import get_workspace_path, get_workspace_manifest
from edkrepo_manifest_parser.edk_manifest import ManifestXml

class CheckoutPinCommand(EdkrepoCommand):
    def __init__(self):
        super().__init__()

    def get_metadata(self):
        metadata = {}
        metadata['name'] = 'checkout-pin'
        metadata['help-text'] = arguments.COMMAND_DESCRIPTION
        metadata['alias'] = 'chp'
        args = []
        metadata['arguments'] = args
        args.append({'name' : 'pinfile',
                     'positional' : True,
                     'position' : 0,
                     'required' : True,
                     'help-text' : arguments.PIN_FILE_HELP})
        args.append(OverrideArgument)
        return metadata

    def run_command(self, args, config):
        workspace_path = get_workspace_path()
        manifest = get_workspace_manifest()
        pin_path = self.__get_pin_path(args, workspace_path, config['cfg_file'].manifest_repo_abs_local_path, manifest)
        pin = ManifestXml(pin_path)
        manifest_sources = manifest.get_repo_sources(manifest.general_config.current_combo)
        check_dirty_repos(manifest, workspace_path)
        for source in manifest_sources:
            local_path = os.path.join(workspace_path, source.root)
            repo = Repo(local_path)
            origin = repo.remotes.origin
            origin.fetch()
        self.__pin_matches_project(pin, manifest, workspace_path)
        sparse_enabled = sparse_checkout_enabled(workspace_path, manifest_sources)
        if sparse_enabled:
            print(SPARSE_RESET)
            reset_sparse_checkout(workspace_path, manifest_sources)
        pin_repo_sources = pin.get_repo_sources(pin.general_config.current_combo)
        try:
            checkout_repos(args.verbose, args.override, pin_repo_sources, workspace_path, manifest)
            manifest.write_current_combo(humble.PIN_COMBO.format(args.pinfile))
        finally:
            if sparse_enabled:
                print(SPARSE_CHECKOUT)
                sparse_checkout(workspace_path, pin_repo_sources, manifest)

    def __get_pin_path(self, args, workspace_path, manifest_repo_path, manifest):
        if os.path.isabs(args.pinfile) and os.path.isfile(args.pinfile):
            return os.path.normpath(args.pinfile)
        elif os.path.isfile(os.path.join(manifest_repo_path, os.path.normpath(manifest.general_config.pin_path), args.pinfile)):
            return os.path.join(manifest_repo_path, os.path.normpath(manifest.general_config.pin_path), args.pinfile)
        elif os.path.isfile(os.path.join(manifest_repo_path, args.pinfile)):
            return os.path.join(manifest_repo_path, args.pinfile)
        elif os.path.isfile(os.path.join(workspace_path, args.pinfile)):
            return os.path.join(workspace_path, args.pinfile)
        elif os.path.isfile(os.path.join(workspace_path, 'repo', args.pinfile)):
            return os.path.join(workspace_path, 'repo', args.pinfile)
        elif not os.path.isfile(os.path.join(workspace_path, args.pinfile)) and os.path.dirname(args.pinfile) is None:
            for dirpath, dirnames, filenames in os.walk(workspace_path):
                if args.pinfile in filenames:
                    return os.path.join(dirpath, args.pinfile)
        else:
            raise EdkrepoInvalidParametersException(humble.NOT_FOUND)

    def __pin_matches_project(self, pin, manifest, workspace_path):
        if pin.project_info.codename != manifest.project_info.codename:
            raise EdkrepoProjectMismatchException(humble.MANIFEST_MISMATCH)
        elif not set(pin.remotes).issubset(set(manifest.remotes)):
            raise EdkrepoProjectMismatchException(humble.MANIFEST_MISMATCH)
        elif pin.general_config.current_combo not in [c.name for c in manifest.combinations]:
            print(humble.COMBO_NOT_FOUND.format(pin.general_config.current_combo))
        combo_name = pin.general_config.current_combo
        pin_sources = pin.get_repo_sources(combo_name)
        pin_root_remote = {source.root:source.remote_name for source in pin_sources}
        try:
            # If the pin and the project manifest have the same combo get the
            # repo sources from that combo. Otherwise get the default combo's
            # repo sources
            manifest_sources = manifest.get_repo_sources(combo_name)
        except ValueError:
            manifest_sources = manifest.get_repo_sources(manifest.general_config.default_combo)
        manifest_root_remote = {source.root:source.remote_name for source in manifest_sources}
        if set(pin_root_remote.items()).isdisjoint(set(manifest_root_remote.items())):
            raise EdkrepoProjectMismatchException(humble.MANIFEST_MISMATCH)
        pin_root_commit = {source.root:source.commit for source in pin_sources}
        for source in pin_sources:
            source_repo_path = os.path.join(workspace_path, source.root)
            repo = Repo(source_repo_path)
            if repo.commit(pin_root_commit[source.root]) is None:
                raise EdkrepoProjectMismatchException(humble.NOT_FOUND)
