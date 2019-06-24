/** @file
  WindowsHelpers.cs

@copyright
  Copyright 2017 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Security.Principal;

namespace TianoCore.EdkRepoInstaller
{
    public class WindowsHelpers
    {
        public static bool RunningOnWindows()
        {
            PlatformID p = Environment.OSVersion.Platform;
            if (p == PlatformID.Win32S || p == PlatformID.Win32Windows ||
                p == PlatformID.Win32NT || p == PlatformID.WinCE)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

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

        public static string GetAllUsersAppDataPath()
        {
            StringBuilder path = new StringBuilder((int)MAX_PATH);
            int hr = SHGetFolderPath(IntPtr.Zero, CSIDL_COMMON_APPDATA, IntPtr.Zero, SHGFP_TYPE_CURRENT, path);
            Exception e = Marshal.GetExceptionForHR(hr);
            if (e != null)
            {
                throw e;
            }
            return path.ToString();
        }

        public static CpuArchitecture GetWindowsOsArchitecture()
        {
            SYSTEM_INFO systemInfo = new SYSTEM_INFO();
            if (Environment.OSVersion.Version.Major > 5 ||
                (Environment.OSVersion.Version.Major == 5 && Environment.OSVersion.Version.Minor >= 1))
            {
                GetNativeSystemInfo(ref systemInfo);
            }
            else
            {
                GetSystemInfo(ref systemInfo);
            }

            switch (systemInfo.wProcessorArchitecture)
            {
                case PROCESSOR_ARCHITECTURE_AMD64:
                    return CpuArchitecture.X64;
                case PROCESSOR_ARCHITECTURE_INTEL:
                    return CpuArchitecture.IA32;
                default:
                    return CpuArchitecture.Unknown;
            }
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

        public static string GetSymlinkTarget(string SymlinkPath)
        {
            if (Environment.OSVersion.Version.Major <= 5)
            {
                throw new InvalidOperationException("Only supported on Vista or later");
            }
            IntPtr hFile = CreateFileNet(
                SymlinkPath,
                EFileAccess.GenericRead,
                EFileShare.Read | EFileShare.Write | EFileShare.Delete,
                IntPtr.Zero,
                ECreationDisposition.OpenExisting,
                EFileAttributes.BackupSemantics | EFileAttributes.OpenReparsePoint,
                IntPtr.Zero
                );
            try
            {
                uint bufferSize = MAXIMUM_REPARSE_DATA_BUFFER_SIZE;
                IntPtr symData = Marshal.AllocHGlobal((int)bufferSize);
                try
                {
                    uint bytesReturned = 0;
                    try
                    {
                        DeviceIoControlNet(hFile, FSCTL_GET_REPARSE_POINT, IntPtr.Zero, 0, symData, bufferSize, out bytesReturned, IntPtr.Zero);
                    }
                    catch (NotASymlinkException)
                    {
                        throw new NotASymlinkException(string.Format("{0} is not a symlink", SymlinkPath));
                    }
                    REPARSE_DATA_BUFFER symDataHeader = (REPARSE_DATA_BUFFER)Marshal.PtrToStructure(symData, typeof(REPARSE_DATA_BUFFER));
                    if (symDataHeader.ReparseTag == IO_REPARSE_TAG_SYMLINK)
                    {
                        int subNameLength = ((int)symDataHeader.unnamedUnion.SymbolicLinkReparseBuffer.SubstituteNameLength) / ((int)Marshal.SizeOf(typeof(ushort)));
                        uint subNameOffset = (uint)symDataHeader.unnamedUnion.SymbolicLinkReparseBuffer.SubstituteNameOffset;
                        long pathOffset = symData.ToInt64();
                        pathOffset += Marshal.OffsetOf(typeof(REPARSE_DATA_BUFFER), "unnamedUnion").ToInt64();
                        pathOffset += Marshal.SizeOf(typeof(SymbolicLinkReparseBufferStructure));
                        pathOffset += subNameOffset;
                        IntPtr pathBuffer = new IntPtr(pathOffset);
                        string subPath = Marshal.PtrToStringUni(pathBuffer, subNameLength);
                        if (subPath.StartsWith("\\??\\"))
                        {
                            subPath = subPath.Substring(4);
                        }
                        return subPath;
                    }
                    else
                    {
                        throw new NotASymlinkException(string.Format("{0} is not a symlink", SymlinkPath));
                    }
                }
                finally
                {
                    Marshal.FreeHGlobal(symData);
                }
            }
            finally
            {
                CloseHandleNet(hFile);
            }
        }

        public static void CreateSymbolicLink(string SymlinkFileName, string TargetFileName, SYMBOLIC_LINK_FLAG LinkType)
        {
            if(SymlinkFileName.Length >= MAX_PATH)
            {
                SymlinkFileName = string.Format(@"\\?\{0}", SymlinkFileName);
            }
            if(TargetFileName.Length >= MAX_PATH)
            {
                TargetFileName = string.Format(@"\\?\{0}", TargetFileName);
            }
            if (!createSymbolicLink(SymlinkFileName, TargetFileName, LinkType))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }

        public static bool RunningInWindowsService()
        {
            USEROBJECTFLAGS uoFlags;
            uint nLengthNeeded;
            IntPtr Hwinsta = GetProcessWindowStationNet();
            GetUserObjectInformationNet(Hwinsta, UOI_FLAGS, out uoFlags, (uint)Marshal.SizeOf(typeof(USEROBJECTFLAGS)), out nLengthNeeded);
            if((uoFlags.dwFlags & WSF_VISIBLE) != 0)
            {
                return false;
            }
            else
            {
                return true;
            }
        }

        public static bool RunningWithAdminRights()
        {
            return new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator);
        }

        public static bool IsUacEnabled()
        {
            IntPtr hProcess = GetCurrentProcess();
            IntPtr hToken = OpenProcessTokenNet(hProcess, TOKEN_QUERY);
            try
            {
                TOKEN_ELEVATION_TYPE elevationType = TOKEN_ELEVATION_TYPE.TokenElevationTypeDefault;
                uint dwReturnLength = 0;
                uint size = (uint)Marshal.SizeOf((int)elevationType);
                IntPtr pElevationType = Marshal.AllocHGlobal((int)size);
                try
                {
                    GetTokenInformationNet(hToken, TOKEN_INFORMATION_CLASS.TokenElevationType,
                        pElevationType, size, out dwReturnLength);
                    if (dwReturnLength != size)
                    {
                        throw new System.ComponentModel.Win32Exception("Returned length was incorrect");
                    }
                    elevationType = (TOKEN_ELEVATION_TYPE)Marshal.ReadInt32(pElevationType);
                }
                finally
                {
                    Marshal.FreeHGlobal(pElevationType);
                }

                if (elevationType == TOKEN_ELEVATION_TYPE.TokenElevationTypeFull
                    || elevationType == TOKEN_ELEVATION_TYPE.TokenElevationTypeLimited)
                {
                    return true;
                }
                else
                {
                    return false;
                }
            }
            finally
            {
                CloseHandleNet(hToken);
            }
        }

        public static void SendEnvironmentVariableChangedMessage()
        {
            SendMessage(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment");
        }

        public static void RunProgramWithAdminPrivilegesViaUacPrompt(string ExePath)
        {
            //Elevate to UAC "High Integrity" level
            SHELLEXECUTEINFO executeInfo = new SHELLEXECUTEINFO();
            executeInfo.cbSize = Marshal.SizeOf(typeof(SHELLEXECUTEINFO));
            executeInfo.fMask = 0;
            executeInfo.hwnd = IntPtr.Zero;
            executeInfo.lpVerb = "runas";
            executeInfo.lpFile = ExePath;
            executeInfo.lpParameters = string.Empty;
            executeInfo.lpDirectory = Environment.CurrentDirectory;
            executeInfo.nShow = 1; /* SW_NORMAL */
            ShellExecuteExNet(ref executeInfo);
        }

        private const uint MAX_PATH = 260;
        private const ushort MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 0x4000; //16KB
        private const int ERROR_NOT_A_REPARSE_POINT = 4390;
        private const uint FSCTL_GET_REPARSE_POINT = 0x900A8;
        private const uint IO_REPARSE_TAG_SYMLINK     = 0xA000000C;
        private const uint IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003;
        [StructLayout(LayoutKind.Sequential)]
        private struct SymbolicLinkReparseBufferStructure
        {
            public ushort SubstituteNameOffset;
            public ushort SubstituteNameLength;
            public ushort PrintNameOffset;
            public ushort PrintNameLength;
            public uint Flags;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct MountPointReparseBufferStructure
        {
            public ushort SubstituteNameOffset;
            public ushort SubstituteNameLength;
            public ushort PrintNameOffset;
            public ushort PrintNameLength;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct GenericReparseBufferStructure
        {
            public IntPtr DataBuffer;
        }

        [StructLayout(LayoutKind.Explicit)]
        private struct UnnamedUnion
        {
            [FieldOffset(0)]
            public SymbolicLinkReparseBufferStructure SymbolicLinkReparseBuffer;
            [FieldOffset(0)]
            public MountPointReparseBufferStructure MountPointReparseBuffer;
            [FieldOffset(0)]
            public GenericReparseBufferStructure GenericReparseBuffer;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct REPARSE_DATA_BUFFER
        {
            public uint ReparseTag;
            public ushort ReparseDataLength;
            public ushort Reserved;
            public UnnamedUnion unnamedUnion;
        }

        private const uint WSF_VISIBLE = 1;
        [StructLayout(LayoutKind.Sequential)]
        private struct USEROBJECTFLAGS
        {
            public bool fInherit;
            public bool fReserved;
            public uint dwFlags;
        }

        //
        // These Win32 API definitions are copied from P/Invoke.net
        //
        private const ushort PROCESSOR_ARCHITECTURE_INTEL = 0;
        private const ushort PROCESSOR_ARCHITECTURE_AMD64 = 9;
        [StructLayout(LayoutKind.Sequential)]
        private struct SYSTEM_INFO
        {
            public ushort wProcessorArchitecture;
            public ushort wReserved;
            public uint dwPageSize;
            public IntPtr lpMinimumApplicationAddress;
            public IntPtr lpMaximumApplicationAddress;
            public UIntPtr dwActiveProcessorMask;
            public uint dwNumberOfProcessors;
            public uint dwProcessorType;
            public uint dwAllocationGranularity;
            public ushort wProcessorLevel;
            public ushort wProcessorRevision;
        };
        private enum TOKEN_INFORMATION_CLASS
        {
            TokenUser = 1,
            TokenGroups,
            TokenPrivileges,
            TokenOwner,
            TokenPrimaryGroup,
            TokenDefaultDacl,
            TokenSource,
            TokenType,
            TokenImpersonationLevel,
            TokenStatistics,
            TokenRestrictedSids,
            TokenSessionId,
            TokenGroupsAndPrivileges,
            TokenSessionReference,
            TokenSandBoxInert,
            TokenAuditPolicy,
            TokenOrigin,
            TokenElevationType,
            TokenLinkedToken,
            TokenElevation,
            TokenHasRestrictions,
            TokenAccessInformation,
            TokenVirtualizationAllowed,
            TokenVirtualizationEnabled,
            TokenIntegrityLevel,
            TokenUIAccess,
            TokenMandatoryPolicy,
            TokenLogonSid,
            MaxTokenInfoClass
        }
        private enum TOKEN_ELEVATION_TYPE
        {
            TokenElevationTypeDefault = 1,
            TokenElevationTypeFull,
            TokenElevationTypeLimited
        }
        [StructLayout(LayoutKind.Sequential)]
        private struct SHELLEXECUTEINFO
        {
            public int cbSize;
            public uint fMask;
            public IntPtr hwnd;
            [MarshalAs(UnmanagedType.LPTStr)]
            public string lpVerb;
            [MarshalAs(UnmanagedType.LPTStr)]
            public string lpFile;
            [MarshalAs(UnmanagedType.LPTStr)]
            public string lpParameters;
            [MarshalAs(UnmanagedType.LPTStr)]
            public string lpDirectory;
            public int nShow;
            public IntPtr hInstApp;
            public IntPtr lpIDList;
            [MarshalAs(UnmanagedType.LPTStr)]
            public string lpClass;
            public IntPtr hkeyClass;
            public uint dwHotKey;
            public IntPtr hIcon;
            public IntPtr hProcess;
        }
        [DllImport("kernel32.dll")]
        private static extern void GetNativeSystemInfo(ref SYSTEM_INFO lpSystemInfo);

        [DllImport("kernel32.dll")]
        private static extern void GetSystemInfo(ref SYSTEM_INFO lpSystemInfo);

        [DllImport("kernel32.dll", SetLastError = true), PreserveSig]
        private static extern uint GetModuleFileName(
            [In] IntPtr hModule, [Out] StringBuilder lpFilename,
            [In, MarshalAs(UnmanagedType.U4)] int nSize);
        private const int ERROR_SUCCESS = 0;

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

        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool DeviceIoControl(
            IntPtr hDevice,
            uint dwIoControlCode,
            IntPtr lpInBuffer,
            uint nInBufferSize,
            IntPtr lpOutBuffer,
            uint nOutBufferSize,
            out uint lpBytesReturned,
            IntPtr lpOverlapped
            );

        public enum SYMBOLIC_LINK_FLAG
        {
            File = 0,
            Directory = 1
        }

        [DllImport("kernel32.dll", SetLastError = true, EntryPoint = "CreateSymbolicLinkW", CharSet = CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.I1)]
        private static extern bool createSymbolicLink(string lpSymlinkFileName, string lpTargetFileName, SYMBOLIC_LINK_FLAG dwFlags);

        private const int CSIDL_COMMON_APPDATA = 0x0023;
        private const uint SHGFP_TYPE_CURRENT = 0;
        [DllImport("shell32.dll")]
        private static extern int SHGetFolderPath(IntPtr hwndOwner, int nFolder, IntPtr hToken, uint dwFlags, [Out] StringBuilder pszPath);

        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr GetProcessWindowStation();

        private const int UOI_FLAGS = 1;
        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool GetUserObjectInformation(IntPtr hObj, int nIndex, [Out] out USEROBJECTFLAGS pvInfo, uint nLength, out uint lpnLengthNeeded);

        [DllImport("kernel32.dll")]
        static extern IntPtr GetCurrentProcess();

        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool OpenProcessToken(IntPtr ProcessHandle,
            UInt32 DesiredAccess, out IntPtr TokenHandle);
        private const uint TOKEN_QUERY = 0x0008;
        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool GetTokenInformation(
            IntPtr TokenHandle,
            TOKEN_INFORMATION_CLASS TokenInformationClass,
            IntPtr TokenInformation,
            uint TokenInformationLength,
            out uint ReturnLength);

        [DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool ShellExecuteEx(ref SHELLEXECUTEINFO lpExecInfo);

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
        private static void DeviceIoControlNet(
            IntPtr hDevice,
            uint dwIoControlCode,
            IntPtr lpInBuffer,
            uint nInBufferSize,
            IntPtr lpOutBuffer,
            uint nOutBufferSize,
            out uint lpBytesReturned,
            IntPtr lpOverlapped
            )
        {
            if (!DeviceIoControl(hDevice, dwIoControlCode, lpInBuffer, nInBufferSize, lpOutBuffer, nOutBufferSize, out lpBytesReturned, lpOverlapped))
            {
                if (Marshal.GetLastWin32Error() == ERROR_NOT_A_REPARSE_POINT)
                {
                    throw new NotASymlinkException();
                }
                else
                {
                    Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
                }
            }
        }
        private static IntPtr GetProcessWindowStationNet()
        {
            IntPtr windowsStation = GetProcessWindowStation();
            if (windowsStation == IntPtr.Zero)
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
            return windowsStation;
        }
        private static void GetUserObjectInformationNet(IntPtr hObj, int nIndex, out USEROBJECTFLAGS pvInfo, uint nLength, out uint lpnLengthNeeded)
        {
            if(!GetUserObjectInformation(hObj, nIndex, out pvInfo, nLength, out lpnLengthNeeded))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }
        private static IntPtr OpenProcessTokenNet(IntPtr ProcessHandle, UInt32 DesiredAccess)
        {
            IntPtr ret;
            if (!OpenProcessToken(ProcessHandle, DesiredAccess, out ret))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
            return ret;
        }
        private static void GetTokenInformationNet(
                        IntPtr TokenHandle,
                        TOKEN_INFORMATION_CLASS TokenInformationClass,
                        IntPtr TokenInformation,
                        uint TokenInformationLength,
                        out uint ReturnLength)
        {
            if (!GetTokenInformation(TokenHandle, TokenInformationClass,
                TokenInformation, TokenInformationLength, out ReturnLength))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }

        private static void ShellExecuteExNet(ref SHELLEXECUTEINFO lpExecInfo)
        {
            if (!ShellExecuteEx(ref lpExecInfo))
            {
                Marshal.ThrowExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }
    }

    public class NotASymlinkException : Exception
    {
        public NotASymlinkException()
        {
        }

        public NotASymlinkException(string message)
            : base(message)
        {
        }

        public NotASymlinkException(string message, Exception inner)
            : base(message, inner)
        {
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
