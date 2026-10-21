/** @file
  ShellDetector.cs

  Finds the interactive shell that an edkclang invocation should change.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace TianoCore.EdkClang
{
    internal enum ShellKind
    {
        Cmd,
        PowerShell,
        Other
    }

    internal sealed class ShellInfo
    {
        public ShellKind Kind { get; set; }
        public int ProcessId { get; set; }
        public string Name { get; set; }
    }

    internal static class ShellDetector
    {
        private sealed class ProcessEntry
        {
            public int ProcessId;
            public int ParentProcessId;
            public string ExeName;
        }

        //
        // PowerShell runs edkclang.cmd using cmd.exe, which becomes as a child of the PowerShell process, so a
        // cmd.exe process that was started to run edkclang.cmd must be skipped. An interactive cmd.exe, or a cmd.exe
        // running anything else ends the search.
        //
        public static ShellInfo FindControllingShell()
        {
            Dictionary<int, ProcessEntry> table = SnapshotProcesses();
            int childId = Process.GetCurrentProcess().Id;
            ProcessEntry child;
            if (!table.TryGetValue(childId, out child))
            {
                return new ShellInfo { Kind = ShellKind.Other, Name = "unknown" };
            }

            for (int hops = 0; hops < 16; hops++)
            {
                ProcessEntry parent;
                if (!table.TryGetValue(child.ParentProcessId, out parent))
                {
                    return new ShellInfo { Kind = ShellKind.Other, Name = "unknown" };
                }

                // A parent process that started after its child means the parent has exited and its PID was reused.
                long childStart = GetStartTime(child.ProcessId);
                long parentStart = GetStartTime(parent.ProcessId);
                if (childStart != 0 && parentStart != 0 && parentStart > childStart)
                {
                    return new ShellInfo { Kind = ShellKind.Other, Name = "unknown" };
                }

                string name = parent.ExeName;
                if (name.Equals("cmd.exe", StringComparison.OrdinalIgnoreCase))
                {
                    string commandLine = GetCommandLine(parent.ProcessId);
                    if (commandLine != null && IsCmdRunningEdkClangWrapper(commandLine))
                    {
                        child = parent;
                        continue;
                    }
                    return new ShellInfo { Kind = ShellKind.Cmd, ProcessId = parent.ProcessId, Name = name };
                }
                if (name.Equals("powershell.exe", StringComparison.OrdinalIgnoreCase) ||
                    name.Equals("pwsh.exe", StringComparison.OrdinalIgnoreCase))
                {
                    return new ShellInfo { Kind = ShellKind.PowerShell, ProcessId = parent.ProcessId, Name = name };
                }
                return new ShellInfo { Kind = ShellKind.Other, ProcessId = parent.ProcessId, Name = name };
            }
            return new ShellInfo { Kind = ShellKind.Other, Name = "unknown" };
        }

        // Detects an invocation of "cmd.exe /c" for running edkclang.cmd, or the "for /f" loop inside it that
        // launches edkclang-core.exe. The /c may be combined with other switches.
        internal static bool IsCmdRunningEdkClangWrapper(string commandLine)
        {
            if (commandLine.IndexOf("edkclang.cmd", StringComparison.OrdinalIgnoreCase) < 0 &&
                commandLine.IndexOf("edkclang-core.exe", StringComparison.OrdinalIgnoreCase) < 0)
            {
                return false;
            }
            List<string> tokens = Tokenize(commandLine);
            for (int i = 1; i < tokens.Count; i++)
            {
                string token = tokens[i];
                if (!token.StartsWith("/", StringComparison.Ordinal))
                {
                    return false;
                }
                foreach (string part in token.Split('/'))
                {
                    if (part.Length == 0)
                    {
                        continue;
                    }
                    char c = char.ToLowerInvariant(part[0]);
                    if (c == 'c' || c == 'r')
                    {
                        return true;
                    }
                    if (c == 'k')
                    {
                        return false;
                    }
                }
            }
            return false;
        }

        private static List<string> Tokenize(string commandLine)
        {
            List<string> tokens = new List<string>();
            System.Text.StringBuilder current = new System.Text.StringBuilder();
            bool inQuotes = false;
            foreach (char c in commandLine)
            {
                if (c == '"')
                {
                    inQuotes = !inQuotes;
                }
                else if (char.IsWhiteSpace(c) && !inQuotes)
                {
                    if (current.Length > 0)
                    {
                        tokens.Add(current.ToString());
                        current.Clear();
                    }
                }
                else
                {
                    current.Append(c);
                }
            }
            if (current.Length > 0)
            {
                tokens.Add(current.ToString());
            }
            return tokens;
        }

        private static Dictionary<int, ProcessEntry> SnapshotProcesses()
        {
            Dictionary<int, ProcessEntry> table = new Dictionary<int, ProcessEntry>();
            IntPtr snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
            if (snapshot == INVALID_HANDLE_VALUE)
            {
                return table;
            }
            try
            {
                PROCESSENTRY32 entry = new PROCESSENTRY32();
                entry.dwSize = (uint)Marshal.SizeOf(typeof(PROCESSENTRY32));
                for (bool ok = Process32First(snapshot, ref entry); ok; ok = Process32Next(snapshot, ref entry))
                {
                    table[(int)entry.th32ProcessID] = new ProcessEntry
                    {
                        ProcessId = (int)entry.th32ProcessID,
                        ParentProcessId = (int)entry.th32ParentProcessID,
                        ExeName = entry.szExeFile
                    };
                }
            }
            finally
            {
                CloseHandle(snapshot);
            }
            return table;
        }

        // Returns 0 when the start time cannot be read.
        private static long GetStartTime(int processId)
        {
            IntPtr handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, (uint)processId);
            if (handle == IntPtr.Zero)
            {
                return 0;
            }
            try
            {
                long creation, exit, kernel, user;
                return GetProcessTimes(handle, out creation, out exit, out kernel, out user) ? creation : 0;
            }
            finally
            {
                CloseHandle(handle);
            }
        }

        // Returns null when the command line cannot be read (for example on Windows 7).
        private static string GetCommandLine(int processId)
        {
            IntPtr handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, (uint)processId);
            if (handle == IntPtr.Zero)
            {
                return null;
            }
            try
            {
                uint length = 0;
                NtQueryInformationProcess(handle, ProcessCommandLineInformation, IntPtr.Zero, 0, out length);
                if (length == 0 || length > 0x10000)
                {
                    return null;
                }
                IntPtr buffer = Marshal.AllocHGlobal((int)length);
                try
                {
                    if (NtQueryInformationProcess(handle, ProcessCommandLineInformation, buffer, length, out length) != 0)
                    {
                        return null;
                    }
                    UNICODE_STRING text = (UNICODE_STRING)Marshal.PtrToStructure(buffer, typeof(UNICODE_STRING));
                    return text.Buffer == IntPtr.Zero ? null : Marshal.PtrToStringUni(text.Buffer, text.Length / 2);
                }
                finally
                {
                    Marshal.FreeHGlobal(buffer);
                }
            }
            finally
            {
                CloseHandle(handle);
            }
        }

        private const uint TH32CS_SNAPPROCESS = 0x2;
        private const uint PROCESS_QUERY_LIMITED_INFORMATION = 0x1000;
        private const int ProcessCommandLineInformation = 60;
        private static readonly IntPtr INVALID_HANDLE_VALUE = new IntPtr(-1);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct PROCESSENTRY32
        {
            public uint dwSize;
            public uint cntUsage;
            public uint th32ProcessID;
            public UIntPtr th32DefaultHeapID;
            public uint th32ModuleID;
            public uint cntThreads;
            public uint th32ParentProcessID;
            public int pcPriClassBase;
            public uint dwFlags;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
            public string szExeFile;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct UNICODE_STRING
        {
            public ushort Length;
            public ushort MaximumLength;
            public IntPtr Buffer;
        }

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint processId);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
        private static extern bool Process32First(IntPtr snapshot, ref PROCESSENTRY32 entry);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
        private static extern bool Process32Next(IntPtr snapshot, ref PROCESSENTRY32 entry);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(uint desiredAccess, bool inheritHandle, uint processId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr handle);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetProcessTimes(IntPtr process, out long creationTime, out long exitTime, out long kernelTime, out long userTime);

        [DllImport("ntdll.dll")]
        private static extern int NtQueryInformationProcess(IntPtr process, int informationClass, IntPtr information, uint informationLength, out uint returnLength);
    }
}
