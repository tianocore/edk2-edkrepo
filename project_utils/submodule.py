#!/usr/bin/env python3
#
## @file
# submodule.py
#
# Copyright (c) 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import argparse
import git
import os
import sys
import traceback

from edkrepo_manifest_parser.edk_manifest import ManifestXml
import edkrepo.common.ui_functions as ui_functions
import project_utils.project_utils_strings as strings
import project_utils.arguments.submodule_args as arguments


def _init(repo, submodules=None, verbose=False):
    """
    Performs submodule initialization.  Note that if no selective submodule initialization
    is enabled the init will be handled in _update.

    repo       - GitPython Repo object
    submodules - The list of selective submodule init objects
    verbose    - Enable verbose messages
    """
    # Only handle selective initialization with this method.  For fully recursive init
    # it is cleaner to do it as part of the update process.
    if submodules is not None:
        for sub in submodules:
            if verbose:
                print(strings.SUBMOD_INIT_PATH.format(sub.path))
            output_data = repo.git.execute(['git', 'submodule', 'init', '--', sub.path],
                                           with_extended_output=True, with_stdout=True)
            ui_functions.display_git_output(output_data, verbose)
    return


def _deinit(repo, submodules=None, verbose=False):
    """
    Performs deinitialization of submodules.

    repo       - GitPython Repo object
    submodules - The list of selective submodule init objects
    verbose    - Enable verbose messages
    """
    if submodules is None:
        output_data = repo.git.execute(['git', 'submodule', 'deinit', '-f', '--all'],
                                       with_extended_output=True, with_stdout=True)
        ui_functions.display_git_output(output_data, verbose)
    else:
        for sub in submodules:
            if verbose:
                print(strings.SUBMOD_DEINIT_PATH.format(sub.path))
            output_data = repo.git.execute(['git', 'submodule', 'deinit', '-f', '--', sub.path],
                                           with_extended_output=True, with_stdout=True)
            ui_functions.display_git_output(output_data, verbose)
    return


def _update(repo, submodules=None, verbose=False, recursive=False, cache_path=None):
    """
    Performs the update of submodules.  This includes the sync and update operations.

    repo       - GitPython Repo object
    submodules - The list of selective submodule init objects
    verbose    - Enable verbose messages
    recursive  - If submodules is None then use this parameter to determine if initialization
                 should be recursive
    """
    # Now perform the update of the submodules.  For a fully recursive submodule init
    # this code will update and initialize at the same time.
    repo_filter = repo.git.execute(['git', 'config', 'remote.origin.partialclonefilter'])
    if repo_filter == "tree:0":
        submodule_filter = '--filter=tree:0'
    elif repo_filter == "blob:none":
        submodule_filter = '--filter=blob:none'
    else:
        submodule_filter = None

    if submodules is None:
        cmd = ['git', 'submodule', 'sync']
        if recursive:
            cmd.append('--recursive')
        output_data = repo.git.execute(cmd, with_extended_output=True, with_stdout=True)
        ui_functions.display_git_output(output_data, verbose)
        cmd = ['git', 'submodule', 'update', '--init']
        if recursive:
            cmd.append('--recursive')
        if cache_path is not None:
            cmd.extend(['--reference', cache_path])
        if submodule_filter != None:
            cmd.append(submodule_filter)
        output_data = repo.git.execute(cmd, with_extended_output=True, with_stdout=True)
        ui_functions.display_git_output(output_data, verbose)
    else:
        for sub in submodules:
            if verbose:
                print(strings.SUBMOD_SYNC_PATH.format(sub.path))
            cmd = ['git', 'submodule', 'sync']
            if sub.recursive:
                cmd.append('--recursive')
            cmd.extend(['--', sub.path])
            output_data = repo.git.execute(cmd, with_extended_output=True, with_stdout=True)
            ui_functions.display_git_output(output_data, verbose)
            if verbose:
                print(strings.SUBMOD_UPDATE_PATH.format(sub.path))
            cmd = ['git', 'submodule', 'update', '--init']
            if sub.recursive:
                cmd.append('--recursive')
            if cache_path is not None:
                cmd.extend(['--reference', cache_path])
            cmd.extend(['--', sub.path])
            if submodule_filter != None:
                cmd.append(submodule_filter)
            output_data = repo.git.execute(cmd, with_extended_output=True, with_stdout=True)
            ui_functions.display_git_output(output_data, verbose)
    return


def _compute_change(current_subs, new_subs):
    """
    Determines the list of submodules that have been removed.  Also needs to
    determine if any submodules need to have recursive init disabled

    current_subs - List of selective submodule init entries for the current combo
    new_subs     - List of selective submodule init entries for the new combo
    """
    # Create data objects for determining what submodules need to be deinitialized
    tmp_current = {x.path: x for x in current_subs}
    tmp_new = {x.path: x for x in new_subs}

    # Initial deinitialization list
    deinit_paths = list(set(tmp_current).difference(set(tmp_new)))

    # Check for change in recursive initialization for the specific submodules
    for path in tmp_new:
        if path in tmp_new and path in tmp_current:
            if tmp_current[path].recursive and not tmp_new[path].recursive:
                deinit_paths.append(path)

    # Create the final list of submodules that need to be deinitialized
    return [x for x in current_subs if x.path in deinit_paths]


def _get_submodule_enable(manifest, remote_name, combo):
    """
    Determines if submodules are enabled for the current repo and combo

    manifest    - Manifest object
    remote_name - The name of the current remote being processed
    combo       - The current combo name being processed
    """
    repo_sources = manifest.get_repo_sources(combo)
    for source in repo_sources:
        if source.remote_name == remote_name:
            return source.enable_submodule
    return False


def _get_submodule_state(remote_name, start_manifest, start_combo, end_manifest=None, end_combo=None):
    """
    Determines the state of submodules across manifest and combo changes.

        remote_name    - The name of the current remote being processed.
        start_manifest - Initial manifest parser object.
        start_combo    - Initial combo.
        end_manifest   - The manifest parser object for the project if the manifest is being updated.
        end_combo      - The combination name at the end of the operation if being modified.
    """
    start_subs = start_manifest.get_submodule_init_paths(remote_name, start_combo)
    start_subs_enabled = _get_submodule_enable(start_manifest, remote_name, start_combo)
    if end_combo is not None:
        if end_manifest is not None:
            end_subs = end_manifest.get_submodule_init_paths(remote_name, end_combo)
            end_subs_enabled = _get_submodule_enable(end_manifest, remote_name, end_combo)
        else:
            end_subs = start_manifest.get_submodule_init_paths(remote_name, end_combo)
            end_subs_enabled = _get_submodule_enable(start_manifest, remote_name, end_combo)
    else:
        if end_manifest is not None:
            end_subs = end_manifest.get_submodule_init_paths(remote_name, start_combo)
            end_subs_enabled = _get_submodule_enable(end_manifest, remote_name, start_combo)
        else:
            end_subs = start_subs
            end_subs_enabled = start_subs_enabled
    return start_subs, start_subs_enabled, end_subs, end_subs_enabled


def deinit_full(workspace, manifest, verbose=False):
    """
    Does full submodule deinit based on the current combo.

        workspace - Path to the current workspace.
        manifest  - The current manifest parser object.
    """
    print(strings.SUBMOD_DEINIT_FULL)
    current_combo = manifest.general_config.current_combo
    repo_sources = manifest.get_repo_sources(current_combo)
    for source in repo_sources:
        if _get_submodule_enable(manifest, source.remote_name, current_combo):
            # Open the repo and process submodules
            try:
                repo = git.Repo(os.path.join(workspace, source.root))
            except Exception as repo_error:
                if args.verbose:
                    print(strings.SUBMOD_EXCEPTION.format(repo_error))
                continue
            _deinit(repo, None, verbose)


def init_full(workspace, manifest, verbose=False):
    """
    Does full submodule init based on the current combo.

        workspace - Path to the current workspace.
        manifest  - The current manifest parser object.
    """
    print(strings.SUBMOD_INIT_FULL)
    current_combo = manifest.general_config.current_combo
    repo_sources = manifest.get_repo_sources(current_combo)
    for source in repo_sources:
        if _get_submodule_enable(manifest, source.remote_name, current_combo):
            # Open the repo and process submodules
            try:
                repo = git.Repo(os.path.join(workspace, source.root))
            except Exception as repo_error:
                if args.verbose:
                    print(strings.SUBMOD_EXCEPTION.format(repo_error))
                continue
            _update(repo, None, verbose, True)


def deinit_submodules(workspace, start_manifest, start_combo,
                      end_manifest=None, end_combo=None,
                      verbose=False):
    """
    Deinitializes the submodules for a project.

        workspace      - Path to the current workspace.
        start_manifest - The manifest parser object for the project.
        start_combo    - The combination name at the start of the operation.
        end_manifest   - The manifest parser object for the project if the manifest is being updated.  If the
                         manifest file is not being updated us the value None.
        end_combo      - The combination name at the end of the operation.  If the combo will not change
                         use the value None.
        verbose        - Enable verbose messages.
    """
    # Process each repo that may have submodules enabled
    print(strings.SUBMOD_DEINIT)
    repo_sources = start_manifest.get_repo_sources(start_combo)
    for source in repo_sources:
        # Open the repo and process submodules
        try:
            repo = git.Repo(os.path.join(workspace, source.root))
        except Exception as repo_error:
            if args.verbose:
                print(strings.SUBMOD_EXCEPTION.format(repo_error))
            continue

        # Collect the submodule initialization data from manifest as well as if submodules
        # should be processed for the repo.
        start_subs, start_subs_enabled, end_subs, end_subs_enabled = _get_submodule_state(source.remote_name,
                                                                                          start_manifest,
                                                                                          start_combo,
                                                                                          end_manifest,
                                                                                          end_combo)
        if not start_subs_enabled and not end_subs_enabled:
            # At this point submodules are not enabled on this repo
            continue

        # Compute the list of submodules that need to be removed and added
        deinit_list = _compute_change(start_subs, end_subs)

        # Deinitialize submodules
        if (start_subs_enabled and not end_subs_enabled) or (len(start_subs) == 0 and len(end_subs) != 0):
            # Submodules are being disabled for the entire repo so do a
            # full deinit on the repo.
            _deinit(repo, None, verbose)
        else:
            # Do the deinit based on the list
            _deinit(repo, deinit_list, verbose)


def maintain_submodules(workspace, manifest, combo_name, verbose=False, cache_path=None):
    """
    Updates the submodules for a specific repo.

        workspace  - Path to the current workspace.
        manifest   - The manifest parser object for the project.
        combo_name - The combination name to use for submodule maintenance.
        verbose    - Enable verbose messages.
        cache_path - Path to the submodule cache repo.  A value of None indicates that no cache repo exists.
    """
    # Process each repo that may have submodules enabled
    ui_functions.print_info_msg(strings.SUBMOD_INIT_UPDATE)
    repo_sources = manifest.get_repo_sources(combo_name)
    for source in repo_sources:
        # Open the repo and process submodules
        try:
            repo = git.Repo(os.path.join(workspace, source.root))
        except Exception as repo_error:
            if args.verbose:
                ui_functions.print_error_msg(strings.SUBMOD_EXCEPTION.format(repo_error))
            continue

        # Collect the submodule initialization data from manifest as well as if submodules
        # should be processed for the repo.
        repo_subs = manifest.get_submodule_init_paths(source.remote_name, combo_name)
        repo_subs_enabled = _get_submodule_enable(manifest, source.remote_name, combo_name)
        if not repo_subs_enabled:
            continue

        # Initialize submodules
        if len(repo_subs) > 0:
            _init(repo, repo_subs, verbose)

        # Perform sync/update
        if len(repo_subs) == 0:
            _update(repo, None, verbose, cache_path=cache_path)
        else:
            _update(repo, repo_subs, verbose, cache_path=cache_path)


if __name__ == '__main__':
    def parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('manifest_file', metavar='MANIFEST', help=arguments.SUBMOD_MANIFEST_HELP)
        parser.add_argument('--combo', default=None, help=arguments.SUBMOD_COMBO_HELP)
        parser.add_argument('--new-manifest', default=None, help=arguments.SUBMOD_NEW_MANIFEST_HELP)
        parser.add_argument('--new-combo', default=None, help=arguments.SUBMOD_NEW_COMBO_HELP)
        parser.add_argument('--deinit', action='store_true', help=arguments.SUBMOD_DEINIT_HELP)
        parser.add_argument('--init-full', action='store_true', help=arguments.SUBMOD_INIT_FULL_HELP)
        parser.add_argument('--deinit-full', action='store_true', help=arguments.SUBMOD_DEINIT_FULL_HELP)
        parser.add_argument('--workspace', default='.', help=arguments.SUBMOD_WORKSPACE_HELP)
        parser.add_argument('--verbose', action='store_true', help=arguments.SUBMOD_VERBOSE_HELP)
        return parser.parse_args()

    def main(args):
        # Optional data init
        new_manifest = None
        all_new_combos = None

        # Extract basic manifest data
        manifest = ManifestXml(args.manifest_file)
        init_manifest = manifest
        all_combos = manifest.combinations
        all_combos.extend(manifest.archived_combinations)
        if args.new_manifest is not None:
            new_manifest = ManifestXml(args.new_manifest)
            all_new_combos = new_manifest.combinations
            all_new_combos.extend(new_manifest.archived_combinations)
            init_manifest = new_manifest

        # Determine current and new combo information
        current_combo = manifest.general_config.current_combo
        new_combo = args.new_combo
        for combo in all_combos:
            if args.combo is not None:
                if args.combo.lower() == combo.name.lower():
                    current_combo = combo.name
            if args.new_combo is not None:
                if args.new_combo.lower() == combo.name.lower():
                    new_combo = combo.name
        init_combo = current_combo
        if new_combo is not None:
            init_combo = new_combo

        if args.deinit_full:
            deinit_full(args.workspace, manifest, args.verbose)
        elif args.init_full:
            init_full(args.workspace, manifest, args.verbose)
        else:
            if args.deinit:
                deinit_submodules(args.workspace, manifest, current_combo,
                                  new_manifest, new_combo, args.verbose)
            maintain_submodules(args.workspace, init_manifest, init_combo, args.verbose)

        return 0

    try:
        args = parse_args()
        sys.exit(main(args))
    except Exception:
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
