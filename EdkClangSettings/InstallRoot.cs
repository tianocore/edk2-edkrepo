/** @file
  InstallRoot.cs

  Locates the EDK II Clang installation that this copy of Settings belongs to.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.IO;
using System.Reflection;
using Microsoft.Win32;
using TianoCore.EdkClang;

namespace TianoCore.EdkClangSettings
{
    internal sealed class InstallRoot
    {
        private const string UninstallRegistryPath = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";
        private const string VendorPluginName = "TianoCore.EdkMingwInstaller.VendorCustomizer.dll";
        private const string DefaultUninstallerName = "EdkMingwInstaller.exe";
        private const string RootOption = "--root";

        public string Root { get; private set; }

        public string ToolsDirectory
        {
            get { return Path.Combine(Root, EdkClangLayout.ToolsDirectoryName); }
        }

        public string CoreExePath
        {
            get { return Path.Combine(ToolsDirectory, "edkclang-core.exe"); }
        }

        // A vendor plugin means this is not the TianoCore variant, so its releases are not on GitHub.
        public bool IsVendorVariant
        {
            get { return File.Exists(Path.Combine(Root, VendorPluginName)); }
        }

        //
        // Settings runs from <root>\tools. The hidden --root <folder> option points it at another folder, so it can be
        // tried against a test installation.
        //
        public static bool TryLocate(string[] args, out InstallRoot installRoot, out string error)
        {
            installRoot = null;
            error = null;
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (string.Equals(args[i], RootOption, StringComparison.OrdinalIgnoreCase))
                {
                    installRoot = new InstallRoot { Root = Path.GetFullPath(args[i + 1]) };
                    return true;
                }
            }

            string tools = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            if (!string.Equals(Path.GetFileName(tools), EdkClangLayout.ToolsDirectoryName, StringComparison.OrdinalIgnoreCase))
            {
                error = "EDK II Clang Settings must run from the 'tools' folder of an EDK II Clang installation.";
                return false;
            }
            installRoot = new InstallRoot { Root = Path.GetDirectoryName(tools) };
            return true;
        }

        //
        // The shared uninstaller is named after the installer that wrote it, so ask Programs and Features
        // where it is rather than assuming a name.
        //
        public string FindUninstaller(string version)
        {
            string fallback = null;
            using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            using (RegistryKey uninstall = hklm.OpenSubKey(UninstallRegistryPath))
            {
                if (uninstall != null)
                {
                    foreach (string name in uninstall.GetSubKeyNames())
                    {
                        using (RegistryKey key = uninstall.OpenSubKey(name))
                        {
                            string executable = key == null ? null : GetExecutable(key.GetValue("UninstallString") as string);
                            if (executable == null || !EdkClangLayout.IsSameOrUnder(executable, Root) || !File.Exists(executable))
                            {
                                continue;
                            }
                            if (string.Equals(key.GetValue("EdkClangToolchainVersion") as string, version, StringComparison.Ordinal))
                            {
                                return executable;
                            }
                            fallback = fallback ?? executable;
                        }
                    }
                }
            }
            if (fallback != null)
            {
                return fallback;
            }
            string defaultPath = Path.Combine(Root, DefaultUninstallerName);
            return File.Exists(defaultPath) ? defaultPath : null;
        }

        private static string GetExecutable(string uninstallString)
        {
            if (string.IsNullOrWhiteSpace(uninstallString))
            {
                return null;
            }
            string text = uninstallString.Trim();
            string path;
            if (text.StartsWith("\"", StringComparison.Ordinal))
            {
                int end = text.IndexOf('"', 1);
                path = end < 0 ? null : text.Substring(1, end - 1);
            }
            else
            {
                int space = text.IndexOf(' ');
                path = space < 0 ? text : text.Substring(0, space);
            }
            return path != null && path.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) ? path : null;
        }
    }
}
