#!/usr/bin/env python3
#
## @file
# workspace_pin_file_operations.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os

import edkrepo.common.edkrepo_exception as edkrepo_exception
import edkrepo.common.workspace_maintenance.humble.workspace_pin_file_operations_humble as workspace_pin_file_operations_humble
import edkrepo.common.workspace_maintenance.manifest_repos_maintenance as manifest_repos_maintenance
import edkrepo_manifest_parser.edk_manifest as edk_manifest


def get_checked_out_pin_file(pin_filename, workspace_manifest, config, workspace_path):
    """
    Loads a pin file and returns the ManifestXml object with commit SHAs.
    Searches for the pin file in the manifest repository pin folder first,
    then falls back to the workspace root if not found.
    """
    man_repo = manifest_repos_maintenance.find_source_manifest_repo(
        workspace_manifest, config["cfg_file"], config["user_cfg_file"]
    )
    manifest_repo_path = manifest_repos_maintenance.get_manifest_repo_path(man_repo, config)

    # Try manifest repo pin folder first
    pin_path = None
    if workspace_manifest.general_config.pin_path:
        pin_path = os.path.join(
            manifest_repo_path, workspace_manifest.general_config.pin_path, pin_filename
        )

    # If not found or no pin_path, try workspace root
    if not pin_path or not os.path.isfile(pin_path):
        pin_path = os.path.join(workspace_path, pin_filename)

    # Load and return pin manifest if found
    if os.path.isfile(pin_path):
        return edk_manifest.ManifestXml(pin_path)

    raise edkrepo_exception.EdkrepoPinFileNotFoundException(
        workspace_pin_file_operations_humble.PIN_FILE_NOT_FOUND.format(pin_filename)
    )
