/** @file
  HelperMode.cs

  Installing or uninstalling a version can replace or delete EdkClangSettings.exe, so Settings cannot be running
  while it happens. Settings starts a copy of itself from the temp folder, exits, and the copy runs the installer or
  uninstaller, then starts Settings again.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Windows;

namespace TianoCore.EdkClangSettings
{
    internal static class HelperMode
    {
        public const string Switch = "--helper";
        private const string HelperFileName = "EdkClangSettingsHelper.exe";
        private const string WorkDirectoryPrefix = "EdkClangSettings-";
        private const int ErrorCancelled = 1223;
        private const string Caption = "EDK II Clang Settings";

        public static string CreateWorkDirectory()
        {
            string directory = Path.Combine(Path.GetTempPath(), WorkDirectoryPrefix + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            return directory;
        }

        public static void TryDeleteWorkDirectory(string directory)
        {
            try
            {
                Directory.Delete(directory, true);
            }
            catch (IOException)
            {
            }
            catch (UnauthorizedAccessException)
            {
            }
        }

        //
        // Starts the helper. The caller must exit right afterwards. expectedSha256 is null for a file that is already
        // installed (the uninstaller), otherwise the helper re-checks it just before running it.
        //
        public static void Launch(string program, string arguments, string expectedSha256, string workDirectory)
        {
            string settingsPath = Assembly.GetExecutingAssembly().Location;
            string helperPath = Path.Combine(workDirectory, HelperFileName);
            File.Copy(settingsPath, helperPath, true);

            List<string> helperArguments = new List<string>
            {
                Switch,
                "--file", program,
                "--args", arguments,
                "--sha256", expectedSha256 ?? "-",
                "--relaunch", settingsPath,
                "--cleanup", workDirectory
            };
            ProcessStartInfo start = new ProcessStartInfo(helperPath, Quote(helperArguments))
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                // The helper's own folder is deleted when it is done.
                WorkingDirectory = Environment.SystemDirectory
            };
            Process.Start(start).Dispose();
        }

        private static string Quote(List<string> arguments)
        {
            // None of the values can contain a quote: they are paths, hex digits and fixed switches.
            return string.Join(" ", arguments.ConvertAll(a => "\"" + a + "\""));
        }

        public static int Run(string[] args)
        {
            Dictionary<string, string> values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 1; i + 1 < args.Length; i += 2)
            {
                values[args[i]] = args[i + 1];
            }
            string file = Get(values, "--file");
            string arguments = Get(values, "--args");
            string sha256 = Get(values, "--sha256");
            string relaunch = Get(values, "--relaunch");
            string cleanup = Get(values, "--cleanup");

            try
            {
                if (file == null || !File.Exists(file))
                {
                    throw new FileNotFoundException("The installer was not found.", file);
                }
                RunElevated(file, arguments ?? string.Empty, sha256 == "-" ? null : sha256);
            }
            catch (Exception e)
            {
                MessageBox.Show(e.Message, Caption, MessageBoxButton.OK, MessageBoxImage.Error);
            }

            if (relaunch != null && File.Exists(relaunch))
            {
                Process.Start(new ProcessStartInfo(relaunch)
                {
                    UseShellExecute = false,
                    WorkingDirectory = Path.GetDirectoryName(relaunch)
                });
            }
            if (cleanup != null && IsWorkDirectory(cleanup))
            {
                StartCleanup(cleanup);
            }
            return 0;
        }

        private static string Get(Dictionary<string, string> values, string name)
        {
            string value;
            return values.TryGetValue(name, out value) ? value : null;
        }

        private static void RunElevated(string file, string arguments, string expectedSha256)
        {
            // Holding the file open without write sharing keeps it from being swapped after it was checked.
            FileStream guard = null;
            Process process = null;
            try
            {
                if (expectedSha256 != null)
                {
                    guard = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.Read);
                    string actual;
                    using (SHA256 hash = new SHA256CryptoServiceProvider())
                    {
                        actual = BitConverter.ToString(hash.ComputeHash(guard)).Replace("-", string.Empty);
                    }
                    if (!string.Equals(actual, expectedSha256, StringComparison.OrdinalIgnoreCase))
                    {
                        throw new InvalidDataException("The installer changed after it was downloaded, so it was not run.");
                    }
                }
                try
                {
                    process = Process.Start(new ProcessStartInfo(file, arguments)
                    {
                        UseShellExecute = true,
                        Verb = "runas",
                        WorkingDirectory = Path.GetDirectoryName(file)
                    });
                }
                catch (Win32Exception e)
                {
                    if (e.NativeErrorCode == ErrorCancelled)
                    {
                        // The user declined the administrator prompt, so there is nothing to wait for.
                        return;
                    }
                    throw;
                }
                if (guard != null)
                {
                    guard.Dispose();
                    guard = null;
                }
                process.WaitForExit();
            }
            finally
            {
                if (guard != null)
                {
                    guard.Dispose();
                }
                if (process != null)
                {
                    process.Dispose();
                }
            }
        }

        private static bool IsWorkDirectory(string directory)
        {
            string full = Path.GetFullPath(directory).TrimEnd('\\');
            string temp = Path.GetFullPath(Path.GetTempPath()).TrimEnd('\\');
            return string.Equals(Path.GetDirectoryName(full), temp, StringComparison.OrdinalIgnoreCase) &&
                Path.GetFileName(full).StartsWith(WorkDirectoryPrefix, StringComparison.Ordinal);
        }

        // The helper runs from the folder it deletes, so a separate process removes it after this one exits.
        private static void StartCleanup(string directory)
        {
            Process.Start(new ProcessStartInfo("cmd.exe", "/c choice /d y /t 3 > nul & rmdir /s /q \"" + directory + "\"")
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Environment.SystemDirectory
            }).Dispose();
        }
    }
}
