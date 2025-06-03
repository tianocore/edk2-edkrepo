/** @file
  WindowsHelpers.cs

@copyright
  Copyright 2025 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace TianoCore.EdkMingwInstaller
{
    public class WindowsHelpers
    {
        public static string GetApplicationPath()
        {
            //Note: The .NET libraries won't tell you the true .exe path
            uint ExePathCapacity = 261; //Start out with MAX_PATH + 1
            uint ExePathSize = ExePathCapacity;
            StringBuilder ExePath = new StringBuilder();
            while (ExePathSize >= ExePathCapacity)
            {
                ExePathCapacity = (15 * ExePathCapacity) / 10; //Slightly less than the Golden Ratio
                ExePath = new StringBuilder((int)ExePathCapacity);
                ExePathSize = GetModuleFileName(IntPtr.Zero, ExePath, (int)ExePathCapacity);
                if (ExePathSize == 0)
                {
                    throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
                }
            }
            return ExePath.ToString();
        }

        public static bool IsSameFile(string path1, string path2)
        {
            bool ret = false;

            //Check that the files exist... if they don't then they can't be the same
            if (!File.Exists(path1))
            {
                return false;
            }
            if (!File.Exists(path2))
            {
                return false;
            }

            //Open file 1
            IntPtr file1 = CreateFileNet(path1, EFileAccess.GenericRead,
            EFileShare.Read | EFileShare.Write, IntPtr.Zero,
                ECreationDisposition.OpenExisting, EFileAttributes.Normal, IntPtr.Zero);

            //Open file 2
            try
            {
                IntPtr file2 = CreateFileNet(path2, EFileAccess.GenericRead,
                EFileShare.Read | EFileShare.Write, IntPtr.Zero,
                    ECreationDisposition.OpenExisting, EFileAttributes.Normal, IntPtr.Zero);
                try
                {
                    BY_HANDLE_FILE_INFORMATION file1Info = GetFileInformationByHandleNet(file1);
                    BY_HANDLE_FILE_INFORMATION file2Info = GetFileInformationByHandleNet(file2);
                    if (file1Info.VolumeSerialNumber == file2Info.VolumeSerialNumber &&
                        file1Info.FileIndexHigh == file2Info.FileIndexHigh &&
                        file1Info.FileIndexLow == file2Info.FileIndexLow)
                    {
                        ret = true;
                    }
                }
                finally
                {
                    CloseHandleNet(file2);
                }
            }
            finally
            {
                CloseHandleNet(file1);
            }

            return ret;
        }

        public static void SendEnvironmentVariableChangedMessage()
        {
            SendMessage(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment");
        }

        //
        // These Win32 API definitions are copied from P/Invoke.net
        //
        [DllImport("kernel32.dll", SetLastError = true), PreserveSig]
        private static extern uint GetModuleFileName(
            [In] IntPtr hModule, [Out] StringBuilder lpFilename,
            [In, MarshalAs(UnmanagedType.U4)] int nSize);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr CreateFile(
           string lpFileName,
           EFileAccess dwDesiredAccess,
           EFileShare dwShareMode,
           IntPtr lpSecurityAttributes,
           ECreationDisposition dwCreationDisposition,
           EFileAttributes dwFlagsAndAttributes,
           IntPtr hTemplateFile);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetFileInformationByHandle(IntPtr hFile,
            out BY_HANDLE_FILE_INFORMATION lpFileInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr hObject);

        private static readonly IntPtr HWND_BROADCAST = new IntPtr(0xffff);
        private const int WM_SETTINGCHANGE = 0x001A;
        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        private static extern IntPtr SendMessage(IntPtr hWnd, int Msg, int wParam, [MarshalAs(UnmanagedType.LPWStr)] string lParam);

        //
        // These are wrappers that translate error codes
        // into exceptions to make error handling easier
        //
        private static IntPtr CreateFileNet(
           string lpFileName,
           EFileAccess dwDesiredAccess,
           EFileShare dwShareMode,
           IntPtr lpSecurityAttributes,
           ECreationDisposition dwCreationDisposition,
           EFileAttributes dwFlagsAndAttributes,
           IntPtr hTemplateFile)
        {
            IntPtr ret = CreateFile(lpFileName, dwDesiredAccess, dwShareMode, lpSecurityAttributes, dwCreationDisposition, dwFlagsAndAttributes, hTemplateFile);

            //If == INVALID_HANDLE_VALUE
            if (ret.ToInt32() == -1)
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
            return ret;
        }
        private static BY_HANDLE_FILE_INFORMATION GetFileInformationByHandleNet(IntPtr hFile)
        {
            BY_HANDLE_FILE_INFORMATION ret = new BY_HANDLE_FILE_INFORMATION();
            if (!GetFileInformationByHandle(hFile, out ret))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
            return ret;
        }
        private static void CloseHandleNet(IntPtr hObject)
        {
            if (!CloseHandle(hObject))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }

        internal struct BY_HANDLE_FILE_INFORMATION
        {
            public uint FileAttributes;
            public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
            public uint VolumeSerialNumber;
            public uint FileSizeHigh;
            public uint FileSizeLow;
            public uint NumberOfLinks;
            public uint FileIndexHigh;
            public uint FileIndexLow;
        }

        [Flags]
        internal enum EFileAccess : uint
        {
            GenericRead = 0x80000000,
            GenericWrite = 0x40000000,
            GenericExecute = 0x20000000,
            GenericAll = 0x10000000
        }

        [Flags]
        internal enum EFileShare : uint
        {
            None = 0x00000000,
            Read = 0x00000001,
            Write = 0x00000002,
            Delete = 0x00000004
        }

        internal enum ECreationDisposition : uint
        {
            New = 1,
            CreateAlways = 2,
            OpenExisting = 3,
            OpenAlways = 4,
            TruncateExisting = 5
        }

        [Flags]
        internal enum EFileAttributes : uint
        {
            Readonly = 0x00000001,
            Hidden = 0x00000002,
            System = 0x00000004,
            Directory = 0x00000010,
            Archive = 0x00000020,
            Device = 0x00000040,
            Normal = 0x00000080,
            Temporary = 0x00000100,
            SparseFile = 0x00000200,
            ReparsePoint = 0x00000400,
            Compressed = 0x00000800,
            Offline = 0x00001000,
            NotContentIndexed = 0x00002000,
            Encrypted = 0x00004000,
            Write_Through = 0x80000000,
            Overlapped = 0x40000000,
            NoBuffering = 0x20000000,
            RandomAccess = 0x10000000,
            SequentialScan = 0x08000000,
            DeleteOnClose = 0x04000000,
            BackupSemantics = 0x02000000,
            PosixSemantics = 0x01000000,
            OpenReparsePoint = 0x00200000,
            OpenNoRecall = 0x00100000,
            FirstPipeInstance = 0x00080000
        }
    }
}
