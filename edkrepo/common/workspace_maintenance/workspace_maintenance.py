#!/usr/bin/env python3
#
## @file
# workspace_maintenance.py
#
# Copyright (c) 2017- 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

''' Contains shared workspace maintenance functions. '''

import os
import unicodedata

from edkrepo.common.edkrepo_exception import EdkrepoFoundMultipleException, EdkrepoNotFoundException
from edkrepo.common.humble import GEN_A_NOT_IN_B, GEN_FOUND_MULT_A_IN_B

def generate_name_for_obsolete_backup(absolute_path):
    if not os.path.exists(absolute_path):
        raise ValueError("{} does not exist".format(absolute_path))
    original_name = os.path.basename(absolute_path)
    dir_name = os.path.dirname(absolute_path)
    unique_name = ""
    unique_name_found = False
    index = 1
    while not unique_name_found:
        if index == 1:
            unique_name = "{}_old".format(original_name)
        else:
            unique_name = "{}_old{}".format(original_name, index)
        if not os.path.exists(os.path.join(dir_name, unique_name)):
            unique_name_found = True
        index += 1
    return unique_name

def case_insensitive_equal(str1, str2):
    return unicodedata.normalize("NFKD", str1.casefold()) == unicodedata.normalize("NFKD", str2.casefold())

def case_insensitive_single_match(str1, str_list):
    matches = [x for x in str_list if case_insensitive_equal(str1, x)]
    if len(matches) == 0:
        raise EdkrepoNotFoundException(GEN_A_NOT_IN_B.format(str1, str_list))
    elif len(matches) > 1:
        raise EdkrepoFoundMultipleException(GEN_FOUND_MULT_A_IN_B.format(str1, str_list))
    return matches[0]
