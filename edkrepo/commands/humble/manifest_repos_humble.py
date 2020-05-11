#!/usr/bin/env python3
#
## @file
# manifest_repos_humble.py
#
# Copyright (c) 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
Contains user visible strings printed by the manifest_repos command.
'''

CFG_LIST_ENTRY = 'Config File: edkrepo.cfg Manifest Repository Name: {}'
USER_CFG_LIST_ENTRY = 'Config File: edkrepo_user.cfg Manifest Repository Name: {}'
NAME_REQUIRED = 'The "name" argument is required to add/remove a manifest repository'
ADD_REQUIRED = 'The "name", "url", "branch" and "local-path" arguments are required to add a manifest repository'
CANNOT_REMOVE_CFG = 'Manifest repositories cannot be removed from the edkrepo.cfg file.'
REMOVE_NOT_EXIST = 'The selected manifest repository does note exist in the edkrepo_user.cfg file.'
ALREADY_EXISTS = 'A manifest repository already exists with name: {}'
