/** @file
  UserEnvironments.cs

  Visits the Environment registry key of every user account on the machine, including
  users who are not logged in (their NTUSER.DAT is loaded temporarily).

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Threading;

namespace TianoCore.EdkMingwInstaller
{
    internal static class UserEnvironments
    {
        // Domain/local accounts and Azure AD accounts. This skips the system, service and .DEFAULT hives.
        private static readonly Regex UserSid = new Regex(@"^S-1-(5-21|12-1)-[\d-]+$", RegexOptions.CultureInvariant);

        //
        // Calls visit(environmentKey, description) for each user. The key is writable and is closed after
        // visit returns. A user that cannot be opened is skipped without returning an error.
        //
        public static void ForEach(Action<RegistryKey, string> visit, Action<string> log)
        {
            HashSet<string> alreadyLoaded = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            using (RegistryKey users = RegistryKey.OpenBaseKey(RegistryHive.Users, RegistryView.Registry64))
            {
                foreach (string sid in users.GetSubKeyNames())
                {
                    alreadyLoaded.Add(sid);
                    if (!UserSid.IsMatch(sid))
                    {
                        continue;
                    }
                    VisitHive(users, sid, "user " + sid, visit, log);
                }

                EnablePrivilege("SeBackupPrivilege");
                EnablePrivilege("SeRestorePrivilege");
                using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                using (RegistryKey profileList = hklm.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"))
                {
                    if (profileList == null)
                    {
                        return;
                    }
                    foreach (string sid in profileList.GetSubKeyNames())
                    {
                        if (!UserSid.IsMatch(sid) || alreadyLoaded.Contains(sid))
                        {
                            continue;
                        }
                        string profileDirectory;
                        using (RegistryKey profile = profileList.OpenSubKey(sid))
                        {
                            profileDirectory = profile == null ? null : profile.GetValue("ProfileImagePath") as string;
                        }
                        if (string.IsNullOrEmpty(profileDirectory))
                        {
                            continue;
                        }
                        string hiveFile = Path.Combine(Environment.ExpandEnvironmentVariables(profileDirectory), "NTUSER.DAT");
                        if (!File.Exists(hiveFile))
                        {
                            continue;
                        }
                        VisitUnloadedHive(users, sid, hiveFile, visit, log);
                    }
                }
            }
        }

        private static void VisitUnloadedHive(RegistryKey users, string sid, string hiveFile, Action<RegistryKey, string> visit, Action<string> log)
        {
            string mountName = "EdkClangUninstall_" + Guid.NewGuid().ToString("N");
            int result = RegLoadKey(HKEY_USERS, mountName, hiveFile);
            if (result != 0)
            {
                log(string.Format("Could not load the registry hive of user {0} (error {1}). Skipping that user's environment.", sid, result));
                return;
            }
            try
            {
                VisitHive(users, mountName, "user " + sid + " (not logged in)", visit, log);
            }
            finally
            {
                Unload(mountName, sid, log);
            }
        }

        private static void VisitHive(RegistryKey users, string hiveName, string description, Action<RegistryKey, string> visit, Action<string> log)
        {
            try
            {
                using (RegistryKey environment = users.OpenSubKey(hiveName + @"\Environment", true))
                {
                    if (environment != null)
                    {
                        visit(environment, description);
                    }
                }
            }
            catch (Exception e)
            {
                log(string.Format("Could not update the environment of {0}: {1}", description, e.Message));
            }
        }

        private static void Unload(string mountName, string sid, Action<string> log)
        {
            // A hive cannot be unloaded while any handle to it is open, including unfinalized RegistryKey objects.
            int result = 0;
            for (int attempt = 0; attempt < 10; attempt++)
            {
                GC.Collect();
                GC.WaitForPendingFinalizers();
                result = RegUnLoadKey(HKEY_USERS, mountName);
                if (result == 0)
                {
                    return;
                }
                Thread.Sleep(200);
            }
            log(string.Format("Could not unload the registry hive of user {0} (error {1}); Windows will unload it later.", sid, result));
        }

        private static void EnablePrivilege(string name)
        {
            IntPtr token;
            if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, out token))
            {
                return;
            }
            try
            {
                TOKEN_PRIVILEGES privileges = new TOKEN_PRIVILEGES();
                if (!LookupPrivilegeValue(null, name, out privileges.Luid))
                {
                    return;
                }
                privileges.PrivilegeCount = 1;
                privileges.Attributes = SE_PRIVILEGE_ENABLED;
                AdjustTokenPrivileges(token, false, ref privileges, 0, IntPtr.Zero, IntPtr.Zero);
            }
            finally
            {
                CloseHandle(token);
            }
        }

        private static readonly IntPtr HKEY_USERS = new IntPtr(unchecked((int)0x80000003));
        private const uint TOKEN_ADJUST_PRIVILEGES = 0x20;
        private const uint TOKEN_QUERY = 0x8;
        private const uint SE_PRIVILEGE_ENABLED = 0x2;

        [StructLayout(LayoutKind.Sequential)]
        private struct LUID
        {
            public uint LowPart;
            public int HighPart;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct TOKEN_PRIVILEGES
        {
            public uint PrivilegeCount;
            public LUID Luid;
            public uint Attributes;
        }

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)]
        private static extern int RegLoadKey(IntPtr hKey, string subKey, string file);

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)]
        private static extern int RegUnLoadKey(IntPtr hKey, string subKey);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool OpenProcessToken(IntPtr process, uint desiredAccess, out IntPtr token);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool LookupPrivilegeValue(string systemName, string name, out LUID luid);

        [DllImport("advapi32.dll", SetLastError = true)]
        private static extern bool AdjustTokenPrivileges(IntPtr token, bool disableAll, ref TOKEN_PRIVILEGES newState, uint bufferLength, IntPtr previous, IntPtr returnLength);

        [DllImport("kernel32.dll")]
        private static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr handle);
    }
}
