#!/usr/bin/env python3
#
## @file
# edkrepo_exception.py
#
# Copyright (c) 2017- 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#



class EdkrepoException(Exception):
    def __init__(self, message, exit_code):
        super().__init__(message)
        self.exit_code = exit_code

class EdkrepoInvalidParametersException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 101)

class EdkrepoGlobalConfigNotFoundException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 102)

class EdkrepoConfigFileInvalidException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 103)

class EdkrepoManifestInvalidException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 104)

class EdkrepoWorkspaceInvalidException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 105)

class EdkrepoGlobalDataDirectoryNotFoundException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 106)

class EdkrepoUncommitedChangesException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 107)

class EdkrepoManifestNotFoundException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 108)

class EdkrepoManifestChangedException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 109)

class EdkrepoWitNotFoundException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 110)

class EdkrepoConfigFileReadOnlyException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 112)

class EdkrepoProjectMismatchException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 113)

class EdkrepoVerificationException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 114)

class EdkrepoSparseException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 115)

class EdkrepoNotFoundException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 116)

class EdkrepoFoundMultipleException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 117)

class EdkrepoWorkspaceCorruptException(EdkrepoException):
    def __ini__(self, message):
        super().__init__(message, 118)

class EdkrepoWarningException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 119)

class EdkrepoGitException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 120)

class EdkrepoHookNotFoundException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 121)

class EdkrepoGitConfigSetupException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 122)

class EdkrepoCacheException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 123)

class EdkrepoAbortCherryPickException(EdkrepoException):
    def __init__(self, message):
        super().__init__(message, 124)
