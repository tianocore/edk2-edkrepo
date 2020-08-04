#!/usr/bin/env python3
#
## @file
# checkout_command.py
#
# Copyright (c) 2018 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import os
import sys
if sys.platform == "win32":
    from ctypes import windll, POINTER, byref, GetLastError, Structure, WinError
    from ctypes import c_void_p, c_ushort, c_int,  c_ulong, c_wchar, c_wchar_p
    from ctypes import create_unicode_buffer

def _is_wow64_process():
    kernel32 = windll.kernel32
    GetCurrentProcess = kernel32.GetCurrentProcess
    GetCurrentProcess.argtypes = []
    GetCurrentProcess.restype = c_void_p

    IsWow64Process2 = None
    IMAGE_FILE_MACHINE_UNKNOWN = 0
    try:
        #IsWow64Process2() is only available on Win10 TH2 or later
        IsWow64Process2 = kernel32.IsWow64Process2
    except AttributeError:
        IsWow64Process2 = None
    if IsWow64Process2 is not None:
        IsWow64Process2.argtypes = [c_void_p, POINTER(c_ushort), POINTER(c_ushort)]
        IsWow64Process2.restype = c_int
        ProcessMachine = c_ushort(1)
        NativeMachine = c_ushort(1)
        if IsWow64Process2(GetCurrentProcess(), byref(ProcessMachine), byref(NativeMachine)) != 0:
            if ProcessMachine.value == IMAGE_FILE_MACHINE_UNKNOWN:
                return False
            else:
                return True
        else:
            raise WinError(GetLastError())
    else:
        #Graceful fallback for older OSes
        IsWow64Process = kernel32.IsWow64Process
        IsWow64Process.argtypes = [c_void_p, POINTER(c_int)]
        IsWow64Process.restype = c_int
        is_wow64 = c_int(0)
        if IsWow64Process(GetCurrentProcess(), byref(is_wow64)) != 0:
            if is_wow64.value != 0:
                return True
            else:
                return False
        else:
            raise WinError(GetLastError())

#Gets the real path string for a file with correct casing on the
#file and directory names
def get_actual_path(path):
    path = os.path.normpath(path)
    if sys.platform == "win32":
        #API Definitions
        class _FILETIME(Structure):
            _fields_ = [("dwLowDateTime", c_ulong),
                        ("dwHighDateTime", c_ulong)]
        class _WIN32_FIND_DATAW(Structure):
            _fields_ = [("dwFileAttributes", c_ulong),
                        ("ftCreationTime", _FILETIME),
                        ("ftLastAccessTime", _FILETIME),
                        ("ftLastWriteTime", _FILETIME),
                        ("nFileSizeHigh", c_ulong),
                        ("nFileSizeLow", c_ulong),
                        ("dwReserved0", c_ulong),
                        ("dwReserved1", c_ulong),
                        ("cFileName", c_wchar * 260),
                        ("cAlternateFileName", c_wchar * 14)]
        kernel32 = windll.kernel32
        FindFirstFile = kernel32.FindFirstFileW
        FindFirstFile.argtypes = [c_wchar_p, POINTER(_WIN32_FIND_DATAW)]
        FindFirstFile.restype = c_void_p
        FindClose = kernel32.FindClose
        FindClose.argtypes = [c_void_p]
        FindClose.restype = c_int
        INVALID_HANDLE_VALUE = c_void_p(-1)
        is_wow64 = _is_wow64_process()
        if is_wow64:
            Wow64DisableWow64FsRedirection = kernel32.Wow64DisableWow64FsRedirection
            Wow64DisableWow64FsRedirection.argtypes = [POINTER(c_void_p)]
            Wow64DisableWow64FsRedirection.restype = c_int
            Wow64RevertWow64FsRedirection = kernel32.Wow64RevertWow64FsRedirection
            Wow64RevertWow64FsRedirection.argtypes = [c_void_p]
            Wow64RevertWow64FsRedirection.restype = c_int

        index = 0
        actual_path = [] #A list is used for efficiency, strings are immutable

        #Network paths (UNC paths) require special handling
        use_prefix = True
        unc_path = False
        if path[0:1] == os.sep*2:
            if path[2] == '?':
                use_prefix = False
            else:
                unc_path = True
        #Handle drive letters
        if len(path) > 2 and path[1] == ':':
            actual_path.append(path[0].upper())
            actual_path.append(':')
            if len(path) > 3 and path[2] == os.sep:
                actual_path.append(os.sep)
                index = 3
            else:
                index = 2
        last_path_component_start = index
        add_seperator = False
        try:
            #Disable WOW64 file redirection if needed
            if is_wow64:
                wow64_data = c_void_p(0)
                if Wow64DisableWow64FsRedirection(byref(wow64_data)) == 0:
                    wow64_data = c_void_p(0)
                    raise WinError(GetLastError())
            while index < len(path):
                #Find the next component of the path
                find_result = path.find(os.sep, index)
                if find_result != -1:
                    index = find_result
                else:
                    index = len(path)

                #Add a path seperator if this is not the first time through the loop
                if add_seperator:
                    actual_path.append(os.sep)

                #Add prefix to enable paths longer than 260 characters
                if use_prefix:
                    if unc_path:
                        input_path = r"\\?\UNC\{}".format(path[2:index])
                    else:
                        input_path = r"\\?\{}".format(path[0:index])
                else:
                    input_path = path[0:index]
                #Ask Windows what the real name is of the current path component
                info = _WIN32_FIND_DATAW()
                handle = FindFirstFile(input_path, byref(info))
                if handle != INVALID_HANDLE_VALUE.value:
                    FindClose(handle)
                    actual_path.append(info.cFileName)
                else:
                    #FindFirstFile() failed for some reason.
                    #Append the current path component as is
                    actual_path.append(path[last_path_component_start:index])
                index += 1
                last_path_component_start = index
                add_seperator = True
        finally:
            #If WOW64 file redirection was disable previously, re-enable it.
            if is_wow64 and wow64_data.value is not None:
                if Wow64RevertWow64FsRedirection(wow64_data) == 0:
                    raise WinError(GetLastError())
        #Concatenate all strings in the list to produce the final output
        return ''.join(actual_path)
    else:
        return path


def _get_bothseps(path):
    if isinstance(path, bytes):
        return b'\\/'
    else:
        return '\\/'


def expanduser(path):
    """
    Wrapper to consistently map the users HOME directory location.  Currently
    three separate environment variable sets exist to do this mapping.  The default
    python mapping in ntpath.py may not work because of different priority of decode.
    This function is designed to remove any variation.

    Note: This is a copy of the ntpath.py function with minor modifications.
    """
    if sys.platform != 'win32':
        return os.path.expanduser(path)

    path = os.fspath(path)
    if isinstance(path, bytes):
        tilde = b'~'
    else:
        tilde = '~'
    if not path.startswith(tilde):
        return path
    i, n = 1, len(path)
    while i < n and path[i] not in _get_bothseps(path):
        i += 1

    if 'HOME' in os.environ:
        userhome = os.environ['HOME']
    elif 'HOMEPATH' in os.environ:
        try:
            drive = os.environ['HOMEDRIVE']
        except KeyError:
            drive = ''
        userhome = os.path.join(drive, os.environ['HOMEPATH'])
    elif 'USERPROFILE' in os.environ:
        userhome = os.environ['USERPROFILE']
    else:
        return path

    if isinstance(path, bytes):
        userhome = os.fsencode(userhome)

    if i != 1:  # ~user
        userhome = os.path.join(os.path.dirname(userhome), path[1:i])

    return userhome + path[i:]

def get_subst_drive_dict():
    if sys.platform != "win32":
        return {}
    def _query_subst_drive(drive_letter):
        kernel32 = windll.kernel32
        QueryDosDevice = kernel32.QueryDosDeviceW
        QueryDosDevice.argtypes = [c_wchar_p, c_wchar_p, c_ulong]
        QueryDosDevice.restype = c_ulong
        MAX_PATH = 260

        if len(drive_letter) > 1 or len(drive_letter) == 0:
            raise ValueError("Bad drive letter")
        drive = '{}:'.format(drive_letter.upper())
        drive_buffer = create_unicode_buffer(drive)
        target_path_buffer_size = c_ulong(MAX_PATH)
        target_path_buffer = create_unicode_buffer(target_path_buffer_size.value)
        while True:
            count = QueryDosDevice(drive_buffer, target_path_buffer, target_path_buffer_size)
            if count == 0:
                last_error = GetLastError()
                if last_error == 122: #ERROR_INSUFFICIENT_BUFFER
                    #Increase the buffer size and try again
                    target_path_buffer_size = c_ulong((target_path_buffer_size.value * 161) / 100)
                    target_path_buffer = create_unicode_buffer(target_path_buffer_size.value)
                elif last_error == 2: #ERROR_FILE_NOT_FOUND
                    #This is an invalid drive, return an empty string
                    return ''
                else:
                    raise WinError(last_error)
            else:
                break
        target_path = target_path_buffer.value
        if len(target_path) > 4 and target_path[0:4] == '\\??\\':
            if (ord(target_path[4]) >= ord('A') and ord(target_path[4]) <= ord('Z')) or \
                (ord(target_path[4]) >= ord('a') and ord(target_path[4]) <= ord('z')):
                #This is a SUBST'd drive, return the path
                return target_path[4:].strip()
        #This is a non-SUBST'd (aka real) drive, return an empty string
        return ''
    subst_dict = {}
    for index in range(26):
        drive_letter = chr(ord('A') + index)
        target_path = _query_subst_drive(drive_letter)
        if target_path != '':
            subst_dict[drive_letter] = target_path
    return subst_dict
