/** @file
  DefaultVersions.cs

  Reads and changes which installed version new terminals use, for the current user and for the system.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using Microsoft.Win32;
using TianoCore.EdkClang;

namespace TianoCore.EdkClangSettings
{
    internal enum ChangeResult
    {
        Success,
        Declined,
        Failed
    }

    internal static class DefaultVersions
    {
        private const int ErrorCancelled = 1223;

        public static string ReadUser()
        {
            using (RegistryKey key = EdkClangLayout.OpenCurrentUserEnvironment(false))
            {
                return key == null ? null : EdkClangLayout.GetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
            }
        }

        public static string ReadSystem()
        {
            using (RegistryKey key = EdkClangLayout.OpenMachineEnvironment(false))
            {
                return key == null ? null : EdkClangLayout.GetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
            }
        }

        public static void SetUser(InstallRoot root, string version)
        {
            if (!EdkClangLayout.IsVersionName(version))
            {
                throw new ArgumentException("Not a version number: " + version);
            }
            using (RegistryKey key = EdkClangLayout.OpenCurrentUserEnvironment(true))
            {
                EdkClangLayout.SetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName, Path.Combine(root.Root, version));
            }
            EdkClangLayout.BroadcastEnvironmentChange();
        }

        public static void ClearUser()
        {
            using (RegistryKey key = EdkClangLayout.OpenCurrentUserEnvironment(true))
            {
                EdkClangLayout.DeleteEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
            }
            EdkClangLayout.BroadcastEnvironmentChange();
        }

        //
        // Writing the system environment needs administrator rights. Settings itself does not run elevated, because
        // the user default must go to the signed-in user's registry rather than an administrator's.
        // edkclang already has an elevated entry point for this, so use it.
        //
        public static ChangeResult SetSystem(InstallRoot root, string version, out string error)
        {
            error = null;
            if (!EdkClangLayout.IsVersionName(version))
            {
                error = "Not a version number: " + version;
                return ChangeResult.Failed;
            }
            if (!File.Exists(root.CoreExePath))
            {
                error = "The edkclang command is missing from " + root.ToolsDirectory + ".";
                return ChangeResult.Failed;
            }
            ProcessStartInfo start = new ProcessStartInfo(root.CoreExePath, "--write-system-default " + version)
            {
                UseShellExecute = true,
                Verb = "runas",
                WindowStyle = ProcessWindowStyle.Hidden,
                WorkingDirectory = root.ToolsDirectory
            };
            try
            {
                using (Process process = Process.Start(start))
                {
                    process.WaitForExit();
                    if (process.ExitCode != 0)
                    {
                        error = string.Format("The system default was not changed (exit code {0}).", process.ExitCode);
                        return ChangeResult.Failed;
                    }
                }
            }
            catch (Win32Exception e)
            {
                if (e.NativeErrorCode == ErrorCancelled)
                {
                    return ChangeResult.Declined;
                }
                error = "Could not start the elevated helper: " + e.Message;
                return ChangeResult.Failed;
            }
            return ChangeResult.Success;
        }
    }
}
