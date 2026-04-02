#!/usr/bin/env python3
#
## @file
# workspace_pin_file_operations.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

if sys.platform == "win32":
    from ctypes import c_uint32, c_void_p, c_wchar_p, create_unicode_buffer, oledll

from edkrepo_manifest_parser import edk_manifest

from edkrepo.common.edkrepo_exception import EdkrepoPinFileNotFoundException
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import (
    find_source_manifest_repo,
    get_manifest_repo_path,
)


def get_checked_out_pin_file(pin_filename, workspace_manifest, config, workspace_path):
    """
    Loads a pin file and returns the ManifestXml object with commit SHAs.
    Searches for the pin file in the manifest repository pin folder first,
    then falls back to the workspace root if not found.
    """
    man_repo = find_source_manifest_repo(
        workspace_manifest, config["cfg_file"], config["user_cfg_file"]
    )
    manifest_repo_path = get_manifest_repo_path(man_repo, config)

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

    raise EdkrepoPinFileNotFoundException(
        f"Pin file '{pin_filename}' not found in manifest repository or workspace root"
    )
