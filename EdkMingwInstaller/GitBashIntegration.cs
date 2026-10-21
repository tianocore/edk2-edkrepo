/** @file
  GitBashIntegration.cs

  Installs and removes the edkclang function for Git for Windows.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using Microsoft.Win32;
using System;
using System.IO;
using System.Text;

namespace TianoCore.EdkMingwInstaller
{
    internal static class GitBashIntegration
    {
        public const string ScriptName = "edkclang.sh";

        //
        // Looks for git.exe on the PATH first, then in the registry.
        // The Git for Windows root is the folder that contains usr\bin\bash.exe.
        //
        public static string FindGitRoot()
        {
            foreach (string entry in (Environment.GetEnvironmentVariable("PATH") ?? string.Empty).Split(';'))
            {
                try
                {
                    string directory = entry.Trim().Trim('"');
                    if (directory.Length == 0 || !File.Exists(Path.Combine(directory, "git.exe")))
                    {
                        continue;
                    }
                    for (int level = 0; level < 3 && !string.IsNullOrEmpty(directory); level++)
                    {
                        if (IsGitRoot(directory))
                        {
                            return directory;
                        }
                        directory = Path.GetDirectoryName(directory);
                    }
                }
                catch (ArgumentException)
                {
                    // The PATH entry has invalid characters, skip it.
                }
            }

            foreach (RegistryHive hive in new[] { RegistryHive.LocalMachine, RegistryHive.CurrentUser })
            {
                using (RegistryKey baseKey = RegistryKey.OpenBaseKey(hive, RegistryView.Registry64))
                using (RegistryKey key = baseKey.OpenSubKey(@"SOFTWARE\GitForWindows"))
                {
                    string installPath = key == null ? null : key.GetValue("InstallPath") as string;
                    if (!string.IsNullOrEmpty(installPath) && IsGitRoot(installPath))
                    {
                        return installPath;
                    }
                }
            }
            return null;
        }

        private static bool IsGitRoot(string directory)
        {
            return File.Exists(Path.Combine(directory, "usr", "bin", "bash.exe"));
        }

        // Git Bash cannot run a script with Windows line endings.
        private static void WriteUnixFile(string path, string text)
        {
            File.WriteAllBytes(path, new UTF8Encoding(false).GetBytes(text.Replace("\r\n", "\n")));
        }

        public static void Install(string packageDirectory)
        {
            try
            {
                string gitRoot = FindGitRoot();
                if (gitRoot == null)
                {
                    InstallLogger.Log("Git for Windows not found; skipping Git Bash integration.");
                    return;
                }
                string profileDirectory = Path.Combine(gitRoot, "etc", "profile.d");
                if (!Directory.Exists(profileDirectory))
                {
                    InstallLogger.Log(string.Format("{0} not found; skipping Git Bash integration.", profileDirectory));
                    return;
                }

                string scriptPath = Path.Combine(profileDirectory, ScriptName);
                WriteUnixFile(scriptPath, File.ReadAllText(Path.Combine(packageDirectory, ScriptName)));
                InstallLogger.Log(string.Format("Installed the edkclang command for Git Bash at {0}.", scriptPath));
            }
            catch (Exception e)
            {
                // Git Bash support is optional, so a problem should not fail the installation.
                InstallLogger.Log(string.Format("Could not install the Git Bash integration: {0}", e.Message));
            }
        }

        public static void Remove()
        {
            try
            {
                string gitRoot = FindGitRoot();
                if (gitRoot == null)
                {
                    return;
                }
                DeleteIfPresent(Path.Combine(gitRoot, "etc", "profile.d", ScriptName));
            }
            catch (Exception e)
            {
                InstallLogger.Log(string.Format("Could not remove the Git Bash integration: {0}", e.Message));
            }
        }

        private static void DeleteIfPresent(string path)
        {
            if (File.Exists(path))
            {
                File.Delete(path);
                InstallLogger.Log(string.Format("Deleted {0}.", path));
            }
        }
    }
}
