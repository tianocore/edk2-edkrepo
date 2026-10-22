/** @file
  Authenticode.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Runtime.InteropServices;

namespace TianoCore.EdkClangSettings
{
    internal static class Authenticode
    {
        private const uint WTD_UI_NONE = 2;
        private const uint WTD_REVOKE_NONE = 0;
        private const uint WTD_CHOICE_FILE = 1;
        private const uint WTD_STATEACTION_VERIFY = 1;
        private const uint WTD_STATEACTION_CLOSE = 2;
        // Revocation servers are not reachable on every network, and the digest was checked separately.
        private const uint WTD_REVOCATION_CHECK_NONE = 0x10;

        private static readonly IntPtr InvalidHandle = new IntPtr(-1);

        // WINTRUST_ACTION_GENERIC_VERIFY_V2
        private static readonly Guid GenericVerifyV2 = new Guid("00AAC56B-CD44-11d0-8CC2-00C04FC295EE");

        [StructLayout(LayoutKind.Sequential)]
        private struct WINTRUST_FILE_INFO
        {
            public uint cbStruct;
            public IntPtr pcwszFilePath;
            public IntPtr hFile;
            public IntPtr pgKnownSubject;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct WINTRUST_DATA
        {
            public uint cbStruct;
            public IntPtr pPolicyCallbackData;
            public IntPtr pSIPClientData;
            public uint dwUIChoice;
            public uint fdwRevocationChecks;
            public uint dwUnionChoice;
            public IntPtr pFile;
            public uint dwStateAction;
            public IntPtr hWVTStateData;
            public IntPtr pwszURLReference;
            public uint dwProvFlags;
            public uint dwUIContext;
        }

        [DllImport("wintrust.dll", ExactSpelling = true)]
        private static extern int WinVerifyTrust(IntPtr hwnd, [MarshalAs(UnmanagedType.LPStruct)] Guid pgActionID, IntPtr pWVTData);

        //
        // Returns 0 if the file has a valid Authenticode signature from a trusted publisher. Any other value is the
        // HRESULT from WinVerifyTrust, including a file that is not signed at all.
        //
        public static int Verify(string path)
        {
            IntPtr pathPointer = Marshal.StringToCoTaskMemUni(path);
            IntPtr filePointer = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(WINTRUST_FILE_INFO)));
            IntPtr dataPointer = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(WINTRUST_DATA)));
            try
            {
                WINTRUST_FILE_INFO file = new WINTRUST_FILE_INFO
                {
                    cbStruct = (uint)Marshal.SizeOf(typeof(WINTRUST_FILE_INFO)),
                    pcwszFilePath = pathPointer
                };
                Marshal.StructureToPtr(file, filePointer, false);

                WINTRUST_DATA data = new WINTRUST_DATA
                {
                    cbStruct = (uint)Marshal.SizeOf(typeof(WINTRUST_DATA)),
                    dwUIChoice = WTD_UI_NONE,
                    fdwRevocationChecks = WTD_REVOKE_NONE,
                    dwUnionChoice = WTD_CHOICE_FILE,
                    pFile = filePointer,
                    dwStateAction = WTD_STATEACTION_VERIFY,
                    dwProvFlags = WTD_REVOCATION_CHECK_NONE
                };
                Marshal.StructureToPtr(data, dataPointer, false);

                int result = WinVerifyTrust(InvalidHandle, GenericVerifyV2, dataPointer);

                // WinVerifyTrust keeps state until it is told to close.
                data = (WINTRUST_DATA)Marshal.PtrToStructure(dataPointer, typeof(WINTRUST_DATA));
                data.dwStateAction = WTD_STATEACTION_CLOSE;
                Marshal.StructureToPtr(data, dataPointer, false);
                WinVerifyTrust(InvalidHandle, GenericVerifyV2, dataPointer);
                return result;
            }
            finally
            {
                Marshal.FreeHGlobal(dataPointer);
                Marshal.FreeHGlobal(filePointer);
                Marshal.FreeCoTaskMem(pathPointer);
            }
        }
    }
}
