/** @file
  EdkClangLayout.cs

  Shared by EdkMingwInstaller and edkclang-core. Describes the on-disk layout of
  side-by-side edk2-clang versions and the environment variable plumbing around it.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace TianoCore.EdkClang
{
    internal sealed class InstalledVersion
    {
        public string Name { get; set; }
        public Version Version { get; set; }
        public string FullPath { get; set; }

        // False for a folder left behind by an interrupted install or uninstall.
        public bool IsComplete { get; set; }
    }

    internal static class EdkClangLayout
    {
        public const string BaseToolsMingwPathName = "BASETOOLS_MINGW_PATH";
        public const string ClangBinName = "CLANG_BIN";
        public const string PathName = "PATH";
        public const string ToolsDirectoryName = "tools";
        public const string MachineEnvironmentKeyPath = @"SYSTEM\CurrentControlSet\Control\Session Manager\Environment";

        private static readonly Regex VersionNamePattern = new Regex(@"^\d+\.\d+\.\d+(\.\d+)?$", RegexOptions.CultureInvariant);

        //
        // Anything that becomes part of a file system path or registry value must pass
        // through here first.
        //
        public static bool TryParseVersion(string name, out Version version)
        {
            version = null;
            if (string.IsNullOrEmpty(name) || !VersionNamePattern.IsMatch(name))
            {
                return false;
            }
            Version parsed;
            if (!Version.TryParse(name, out parsed))
            {
                return false;
            }
            // Reject names like 20.01.8 so a version has exactly one folder name.
            if (!string.Equals(parsed.ToString(), name, StringComparison.Ordinal))
            {
                return false;
            }
            version = parsed;
            return true;
        }

        public static bool IsVersionName(string name)
        {
            Version ignored;
            return TryParseVersion(name, out ignored);
        }

        public static List<InstalledVersion> EnumerateInstalledVersions(string root)
        {
            List<InstalledVersion> versions = new List<InstalledVersion>();
            if (string.IsNullOrEmpty(root) || !Directory.Exists(root))
            {
                return versions;
            }
            foreach (string directory in Directory.EnumerateDirectories(root))
            {
                string name = Path.GetFileName(directory);
                Version version;
                if (!TryParseVersion(name, out version))
                {
                    continue;
                }
                versions.Add(new InstalledVersion
                {
                    Name = name,
                    Version = version,
                    FullPath = directory,
                    IsComplete = File.Exists(Path.Combine(directory, "bin", "clang.exe"))
                });
            }
            versions.Sort((a, b) => a.Version.CompareTo(b.Version));
            return versions;
        }

        public static string NormalizePath(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
            {
                return string.Empty;
            }
            return path.Trim().Trim('"').Replace('/', '\\').TrimEnd('\\');
        }

        public static bool IsSamePath(string a, string b)
        {
            string left = NormalizePath(a);
            return left.Length != 0 && string.Equals(left, NormalizePath(b), StringComparison.OrdinalIgnoreCase);
        }

        public static bool IsSameOrUnder(string path, string directory)
        {
            string p = NormalizePath(path);
            string d = NormalizePath(directory);
            if (p.Length == 0 || d.Length == 0)
            {
                return false;
            }
            return p.Equals(d, StringComparison.OrdinalIgnoreCase) ||
                   p.StartsWith(d + "\\", StringComparison.OrdinalIgnoreCase);
        }

        //
        // If value points at (or is inside) <root>\<version>, returns that version's folder name.
        //
        public static bool TryGetVersionName(string value, string root, out string versionName)
        {
            versionName = null;
            string p = NormalizePath(value);
            string r = NormalizePath(root);
            if (p.Length <= r.Length + 1 || !IsSameOrUnder(p, r))
            {
                return false;
            }
            string first = p.Substring(r.Length + 1).Split('\\')[0];
            if (!IsVersionName(first))
            {
                return false;
            }
            versionName = first;
            return true;
        }

        public static InstalledVersion FindNewestComplete(IEnumerable<InstalledVersion> versions, string excludeName)
        {
            return versions
                .Where(v => v.IsComplete && !string.Equals(v.Name, excludeName, StringComparison.Ordinal))
                .OrderByDescending(v => v.Version)
                .FirstOrDefault();
        }

        //
        // RFC 4122 version 5. SHA-1 is what the GUID spec mandates, it is not
        // being used for any security purpose.
        //
        public static Guid CreateNameBasedGuid(Guid namespaceId, string name)
        {
            byte[] namespaceBytes = namespaceId.ToByteArray();
            SwapGuidByteOrder(namespaceBytes);
            byte[] nameBytes = Encoding.UTF8.GetBytes(name);
            byte[] data = new byte[namespaceBytes.Length + nameBytes.Length];
            Buffer.BlockCopy(namespaceBytes, 0, data, 0, namespaceBytes.Length);
            Buffer.BlockCopy(nameBytes, 0, data, namespaceBytes.Length, nameBytes.Length);

            byte[] hash;
            using (SHA1 sha1 = SHA1.Create())
            {
                hash = sha1.ComputeHash(data);
            }
            byte[] guidBytes = new byte[16];
            Buffer.BlockCopy(hash, 0, guidBytes, 0, 16);
            guidBytes[6] = (byte)((guidBytes[6] & 0x0F) | 0x50);
            guidBytes[8] = (byte)((guidBytes[8] & 0x3F) | 0x80);
            SwapGuidByteOrder(guidBytes);
            return new Guid(guidBytes);
        }

        // System.Guid stores its first three fields little-endian, RFC 4122 hashes them big-endian.
        private static void SwapGuidByteOrder(byte[] b)
        {
            Swap(b, 0, 3);
            Swap(b, 1, 2);
            Swap(b, 4, 5);
            Swap(b, 6, 7);
        }

        private static void Swap(byte[] b, int i, int j)
        {
            byte t = b[i];
            b[i] = b[j];
            b[j] = t;
        }

        public static string FormatProductCode(Guid guid)
        {
            return "{" + guid.ToString().ToUpperInvariant() + "}";
        }

        //
        // Registry environment helpers
        //
        public static RegistryKey OpenMachineEnvironment(bool writable)
        {
            using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            {
                return hklm.OpenSubKey(MachineEnvironmentKeyPath, writable);
            }
        }

        public static RegistryKey OpenCurrentUserEnvironment(bool writable)
        {
            using (RegistryKey hkcu = RegistryKey.OpenBaseKey(RegistryHive.CurrentUser, RegistryView.Registry64))
            {
                return hkcu.OpenSubKey("Environment", writable);
            }
        }

        public static string GetEnvironmentValue(RegistryKey environmentKey, string name)
        {
            return environmentKey.GetValue(name, null, RegistryValueOptions.DoNotExpandEnvironmentNames) as string;
        }

        public static void SetEnvironmentValue(RegistryKey environmentKey, string name, string value)
        {
            environmentKey.SetValue(name, value, RegistryValueKind.String);
        }

        public static void DeleteEnvironmentValue(RegistryKey environmentKey, string name)
        {
            environmentKey.DeleteValue(name, false);
        }

        public static bool AddToMachinePath(string directory)
        {
            using (RegistryKey key = OpenMachineEnvironment(true))
            {
                List<string> entries = ReadPathEntries(key);
                if (entries.Any(e => IsSamePath(e, directory)))
                {
                    return false;
                }
                entries.Add(directory);
                WritePathEntries(key, entries);
                return true;
            }
        }

        public static bool RemoveFromMachinePath(string directory)
        {
            using (RegistryKey key = OpenMachineEnvironment(true))
            {
                List<string> entries = ReadPathEntries(key);
                int removed = entries.RemoveAll(e => IsSamePath(e, directory));
                if (removed == 0)
                {
                    return false;
                }
                WritePathEntries(key, entries);
                return true;
            }
        }

        private static List<string> ReadPathEntries(RegistryKey environmentKey)
        {
            string current = GetEnvironmentValue(environmentKey, "Path") ?? string.Empty;
            return current.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries).ToList();
        }

        private static void WritePathEntries(RegistryKey environmentKey, List<string> entries)
        {
            // Keep the existing value type, so a REG_EXPAND_SZ Path keeps expanding %SystemRoot% and friends.
            RegistryValueKind kind = RegistryValueKind.ExpandString;
            try
            {
                kind = environmentKey.GetValueKind("Path");
            }
            catch (IOException)
            {
            }
            environmentKey.SetValue("Path", string.Join(";", entries), kind);
        }

        //
        // Tells running programs (Explorer, new shells) to re-read the environment.
        //
        public static void BroadcastEnvironmentChange()
        {
            UIntPtr ignored;
            SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, UIntPtr.Zero, "Environment", SMTO_ABORTIFHUNG, 5000, out ignored);
        }

        private static readonly IntPtr HWND_BROADCAST = new IntPtr(0xffff);
        private const uint WM_SETTINGCHANGE = 0x001A;
        private const uint SMTO_ABORTIFHUNG = 0x0002;

        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern IntPtr SendMessageTimeout(
            IntPtr hWnd, uint msg, UIntPtr wParam, string lParam, uint flags, uint timeout, out UIntPtr result);

        //
        // Shell environment rewriting
        //

        // Changes an entry for <root>\<version> (or in the pre-side-by-side <root>\bin layout) to newVersionDir.
        public static string RewriteEntryForVersion(string entry, string root, string newVersionDir)
        {
            string n = NormalizePath(entry);
            string r = NormalizePath(root);
            if (n.Length <= r.Length + 1 || !IsSameOrUnder(n, r))
            {
                return entry;
            }
            string rest = n.Substring(r.Length + 1);
            int separator = rest.IndexOf('\\');
            string first = separator < 0 ? rest : rest.Substring(0, separator);
            string tail = separator < 0 ? string.Empty : rest.Substring(separator);
            if (first.Equals(ToolsDirectoryName, StringComparison.OrdinalIgnoreCase))
            {
                return entry;
            }
            string result = IsVersionName(first) ? newVersionDir + tail : newVersionDir + "\\" + rest;
            return entry.TrimEnd().EndsWith("\\", StringComparison.Ordinal) ? result + "\\" : result;
        }

        public static string RewritePathList(string pathList, string root, string newVersionDir)
        {
            return string.Join(";", pathList.Split(';').Select(e => RewriteEntryForVersion(e, root, newVersionDir)));
        }

        //
        // The variables a shell needs to change to switch to the given versionDir. PATH and CLANG_BIN are
        // only rewritten when they use the old root directory, edkclang does not add new entries.
        //
        public static List<KeyValuePair<string, string>> ComputeShellEnvironment(string root, string versionDir, Func<string, string> getEnvironmentVariable)
        {
            List<KeyValuePair<string, string>> changes = new List<KeyValuePair<string, string>>();
            changes.Add(new KeyValuePair<string, string>(BaseToolsMingwPathName, versionDir));

            string path = getEnvironmentVariable(PathName);
            if (!string.IsNullOrEmpty(path))
            {
                string rewritten = RewritePathList(path, root, versionDir);
                if (!string.Equals(rewritten, path, StringComparison.Ordinal))
                {
                    changes.Add(new KeyValuePair<string, string>(PathName, rewritten));
                }
            }

            string clangBin = getEnvironmentVariable(ClangBinName);
            if (!string.IsNullOrEmpty(clangBin))
            {
                string rewritten = RewriteEntryForVersion(clangBin, root, versionDir);
                if (!string.Equals(rewritten, clangBin, StringComparison.Ordinal))
                {
                    changes.Add(new KeyValuePair<string, string>(ClangBinName, rewritten));
                }
            }
            return changes;
        }
    }
}
