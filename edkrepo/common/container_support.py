#!/usr/bin/env python3
#
## @file
# container_support.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys

if sys.platform == "win32":
    from ctypes import windll, c_void_p, c_bool, c_long, c_ulong, Structure, POINTER, byref, sizeof, WinError, GetLastError

    class _USEROBJECTFLAGS(Structure):
        _fields_ = [("fInherit", c_ulong),
                    ("fReserved", c_ulong),
                    ("dwFlags", c_ulong)]

    def _is_windows_interactive_session() -> bool:
        user32 = windll.user32
        GetProcessWindowStation = user32.GetProcessWindowStation
        GetProcessWindowStation.argtypes = []
        GetProcessWindowStation.restype = c_void_p
        GetUserObjectInformation = user32.GetUserObjectInformationW
        GetUserObjectInformation.argtypes = [c_void_p, c_long, POINTER(_USEROBJECTFLAGS), c_ulong, POINTER(c_ulong)]
        GetUserObjectInformation.restype = c_bool
        window_station = GetProcessWindowStation()
        uoFlags = _USEROBJECTFLAGS()
        nLengthNeeded = c_ulong(0)
        if window_station == 0:
            raise WinError(GetLastError())
        result = GetUserObjectInformation(window_station,
                                          1, # UOI_FLAGS
                                          byref(uoFlags),
                                          sizeof(_USEROBJECTFLAGS),
                                          byref(nLengthNeeded))
        if not result:
            raise WinError(GetLastError())
        if (uoFlags.dwFlags & 1) != 0: # WSF_VISIBLE
            return False
        else:
            return True
else:
    def _is_windows_interactive_session() -> bool:
        return False

def running_in_container() -> bool:
    if sys.platform == "win32":
        return _is_windows_interactive_session()
    elif sys.platform.startswith("linux"):
        return os.path.isfile("/.dockerenv")
    return False
