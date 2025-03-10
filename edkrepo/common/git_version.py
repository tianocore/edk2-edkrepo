#!/usr/bin/env python3
#
## @file
# git_version.py
#
# Copyright (c) 2018 - 2022, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import re

from edkrepo.common.edkrepo_exception import EdkrepoGitException

class GitVersion():
    """
    Initialize, describe and provide comparision operators for a git version number.
    """
    def __init__(self, git_version_string):
        version_pattern = re.compile(r'(\d+).(\d+).(\d+)')
        valid_version = re.search(version_pattern, git_version_string)
        if valid_version is None:
            raise EdkrepoGitException('{} is not a valid Git version number.'.format(git_version_string))
        self.major = int(valid_version.group(1))
        self.minor = int(valid_version.group(2))
        self.patch = int(valid_version.group(3))

    def __eq__(self, other):
        if self.major != other.major:
            return False
        elif self.minor != other.minor:
            return False
        elif self.patch != other.patch:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.major < other.major:
            return True
        elif self.major == other.major and self.minor < other.minor:
            return True
        elif self.minor == other.minor and self.patch < other.patch:
            return True
        else:
            return False

    def __le__(self, other):
        if self.__lt__(other) or self.__eq__(other):
            return True
        else:
            return False

    def __gt__(self, other):
        if self.major > other.major:
            return True
        elif self.major == other.major and self.minor > other.minor:
            return True
        elif self.minor == other.minor and self.patch > other.patch:
            return True
        else:
            return False

    def __ge__(self, other):
        if self.__gt__(other) or self.__eq__(other):
            return True
        else:
            return False

    def version_string(self):
        return '{}.{}.{}'.format(self.major, self.minor, self.patch)

    def __str__(self):
        return self.version_string()

    def __repr__(self):
        return "Git Version: '{}'".format(self.version_string())