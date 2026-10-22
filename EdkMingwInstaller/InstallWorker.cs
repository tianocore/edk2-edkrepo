/** @file
  InstallWorker.cs

@copyright
  Copyright 2025 - 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using TianoCore.EdkClang;

namespace TianoCore.EdkMingwInstaller
{
    public class InstallWorker
    {
        public static bool SilentMode { get; set; }

        private const string UninstallRegistryPath = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";

        //
        // The version selected with /Version for an uninstall, or null when the caller did not specify one.
        //
        public static string UninstallVersion { get; set; }

        //
        // Set by PerformUninstall when it removed the last installed version. The uninstaller then deletes
        // itself and the installation directory, which is now empty.
        //
        public static bool RemovedLastVersion { get; private set; }

        //
        // The version to make the system default, chosen on the options page. When null, the default
        // switches to this installer's version if it is newer than the current default.
        //
        public string DefaultVersionChoice { get; set; }

        //
        // The LLVM version this package contains.
        //
        public static string ToolchainVersion
        {
            get
            {
                AssemblyInformationalVersionAttribute attribute =
                    (AssemblyInformationalVersionAttribute)Attribute.GetCustomAttribute(
                        Assembly.GetExecutingAssembly(), typeof(AssemblyInformationalVersionAttribute));
                string version = attribute == null ? null : attribute.InformationalVersion;
                if (!EdkClangLayout.IsVersionName(version))
                {
                    throw new InvalidOperationException(
                        string.Format("The installer's toolchain version '{0}' is not a version number such as 20.1.8.", version));
                }
                return version;
            }
        }

        //
        // Version of the install/uninstall engine, independent of the toolchain. A newer engine
        // replaces the shared uninstaller on disk, an older one does not.
        //
        public static Version EngineVersion
        {
            get
            {
                AssemblyFileVersionAttribute attribute =
                    (AssemblyFileVersionAttribute)Attribute.GetCustomAttribute(
                        Assembly.GetExecutingAssembly(), typeof(AssemblyFileVersionAttribute));
                return Version.Parse(attribute.Version);
            }
        }

        //
        // Programs and Features entry for one installed toolchain version. The name is derived from
        // ProductCode, so the same version always maps to the same key.
        //
        public static string VersionProductCode(string toolchainVersion)
        {
            return EdkClangLayout.FormatProductCode(
                EdkClangLayout.CreateNameBasedGuid(Guid.Parse(InstallerStrings.ProductCode), toolchainVersion));
        }

        //
        // Whether older versions with the same major number as this installer's (for example 22.1.3 when
        // installing 22.2.1) are uninstalled once the new version is installed.
        // In /Passive or /Silent mode this is false only when /KeepOldVersions is given.
        //
        public bool RemoveOlderSameMajorVersions { get; set; } = true;

        public static string GetDefaultInstallRoot()
        {
            return Path.Combine(
                Path.GetPathRoot(Environment.GetFolderPath(Environment.SpecialFolder.Windows)),
                InstallerStrings.InstallationDirectory);
        }

        private static RegistryKey OpenUninstallKey(bool writable = true)
        {
            using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            {
                return hklm.OpenSubKey(UninstallRegistryPath, writable);
            }
        }

        private static string LegacyClangPath(string root)
        {
            return Path.Combine(root, "bin", "clang.exe");
        }

        //
        // Older installers put clang directly in the installation directory instead of a version folder.
        //
        public static bool IsLegacyLayout(string root)
        {
            return File.Exists(LegacyClangPath(root));
        }

        public static string DetectLegacyVersion(string root)
        {
            string clang = LegacyClangPath(root);
            if (File.Exists(clang))
            {
                try
                {
                    ProcessStartInfo start = new ProcessStartInfo(clang, "--version")
                    {
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true
                    };
                    using (Process process = Process.Start(start))
                    {
                        Task<string> output = process.StandardOutput.ReadToEndAsync();
                        if (process.WaitForExit(15000))
                        {
                            Match match = Regex.Match(output.Result, @"clang version (\d+\.\d+\.\d+)");
                            if (match.Success && EdkClangLayout.IsVersionName(match.Groups[1].Value))
                            {
                                return match.Groups[1].Value;
                            }
                        }
                        else
                        {
                            process.Kill();
                        }
                    }
                }
                catch (Exception e)
                {
                    InstallLogger.Log(string.Format("Could not run {0}: {1}", clang, e.Message));
                }
            }

            using (RegistryKey uninstall = OpenUninstallKey(false))
            using (RegistryKey legacyKey = uninstall.OpenSubKey(InstallerStrings.ProductCode))
            {
                string displayVersion = legacyKey == null ? null : legacyKey.GetValue("DisplayVersion") as string;
                Match match = Regex.Match(displayVersion ?? string.Empty, @"^(\d+\.\d+\.\d+)");
                if (match.Success && EdkClangLayout.IsVersionName(match.Groups[1].Value))
                {
                    return match.Groups[1].Value;
                }
            }
            return null;
        }

        //
        // The version that BASETOOLS_MINGW_PATH currently selects system wide, or null if unset or invalid.
        //
        public static string GetCurrentSystemDefaultVersion(string root)
        {
            string value;
            using (RegistryKey machine = EdkClangLayout.OpenMachineEnvironment(false))
            {
                value = machine == null ? null : EdkClangLayout.GetEnvironmentValue(machine, EdkClangLayout.BaseToolsMingwPathName);
            }
            string name;
            if (EdkClangLayout.TryGetVersionName(value, root, out name))
            {
                return File.Exists(Path.Combine(root, name, "bin", "clang.exe")) ? name : null;
            }
            if (EdkClangLayout.IsSamePath(value, root) && IsLegacyLayout(root))
            {
                return DetectLegacyVersion(root);
            }
            return null;
        }

        //
        // Used by /Passive and /Silent installs, and to prepopulate the options page. The new
        // version becomes the default if no default is usable, or if it is newer than the current one.
        //
        public static string ChooseDefaultAutomatically(string root, string newVersion)
        {
            string current = GetCurrentSystemDefaultVersion(root);
            Version currentVersion;
            Version newVersionNumber;
            if (current != null &&
                EdkClangLayout.TryParseVersion(current, out currentVersion) &&
                EdkClangLayout.TryParseVersion(newVersion, out newVersionNumber) &&
                currentVersion >= newVersionNumber)
            {
                return current;
            }
            return newVersion;
        }

        //
        // Every version that will exist once this installer finishes, newest first.
        //
        public static List<string> GetVersionsAfterInstall(string root)
        {
            HashSet<string> names = new HashSet<string>(StringComparer.Ordinal);
            foreach (InstalledVersion installed in EdkClangLayout.EnumerateInstalledVersions(root))
            {
                if (installed.IsComplete)
                {
                    names.Add(installed.Name);
                }
            }
            if (IsLegacyLayout(root))
            {
                string legacyVersion = DetectLegacyVersion(root);
                if (legacyVersion != null)
                {
                    names.Add(legacyVersion);
                }
            }
            names.Add(ToolchainVersion);
            return names.OrderByDescending(n => Version.Parse(n)).ToList();
        }

        //
        // Installed versions with the same major number as newVersion and a
        // lower minor or patch number, newest first.
        //
        public static List<string> GetOlderSameMajorVersions(string root, string newVersion)
        {
            Version newest;
            if (!EdkClangLayout.TryParseVersion(newVersion, out newest))
            {
                return new List<string>();
            }
            return GetVersionsAfterInstall(root)
                .Where(name => EdkClangLayout.IsOlderSameMajor(Version.Parse(name), newest))
                .ToList();
        }

        public static List<string> GetVersionsAfterInstall(string root, bool removeOlderSameMajorVersions)
        {
            List<string> versions = GetVersionsAfterInstall(root);
            if (removeOlderSameMajorVersions)
            {
                List<string> older = GetOlderSameMajorVersions(root, ToolchainVersion);
                versions.RemoveAll(v => older.Contains(v));
            }
            return versions;
        }

        //
        // Registry functions for the default version. In addition to a system wide BASETOOLS_MINGW_PATH environment
        // variable, each user could have their own copy of BASETOOLS_MINGW_PATH.
        // All copies of this environment variable must point to a version that exists.
        //

        // The retarget() delegate should return the new value,
        // string.Empty to delete the variable, or null to leave it alone.
        private static void RetargetDefaults(Func<string, string> retarget)
        {
            using (RegistryKey machine = EdkClangLayout.OpenMachineEnvironment(true))
            {
                ApplyRetarget(machine, "the system", retarget);
            }
            UserEnvironments.ForEach(
                delegate (RegistryKey environment, string description) { ApplyRetarget(environment, description, retarget); },
                InstallLogger.Log);
            EdkClangLayout.BroadcastEnvironmentChange();
        }

        private static void ApplyRetarget(RegistryKey environment, string description, Func<string, string> retarget)
        {
            string current = EdkClangLayout.GetEnvironmentValue(environment, EdkClangLayout.BaseToolsMingwPathName);
            if (string.IsNullOrEmpty(current))
            {
                return;
            }
            string updated = retarget(current);
            if (updated == null)
            {
                return;
            }
            if (updated.Length == 0)
            {
                EdkClangLayout.DeleteEnvironmentValue(environment, EdkClangLayout.BaseToolsMingwPathName);
                InstallLogger.Log(string.Format("Removed {0} for {1}: it pointed at {2}, which is no longer installed.",
                    EdkClangLayout.BaseToolsMingwPathName, description, DescribeVersionPath(current)));
            }
            else
            {
                EdkClangLayout.SetEnvironmentValue(environment, EdkClangLayout.BaseToolsMingwPathName, updated);
                InstallLogger.Log(string.Format("Changed {0} for {1} from {2} to {3}.",
                    EdkClangLayout.BaseToolsMingwPathName, description, DescribeVersionPath(current), DescribeVersionPath(updated)));
            }
        }

        private static string DescribeVersionPath(string path)
        {
            string name = Path.GetFileName(EdkClangLayout.NormalizePath(path));
            return EdkClangLayout.IsVersionName(name) ? name : path;
        }

        private static void SetSystemDefault(string versionDirectory)
        {
            using (RegistryKey machine = EdkClangLayout.OpenMachineEnvironment(true))
            {
                EdkClangLayout.SetEnvironmentValue(machine, EdkClangLayout.BaseToolsMingwPathName, versionDirectory);
            }
            EdkClangLayout.BroadcastEnvironmentChange();
            InstallLogger.Log(string.Format("Set the system default {0} to {1}.", EdkClangLayout.BaseToolsMingwPathName, DescribeVersionPath(versionDirectory)));
        }

        private void InsertAdminOnlyAcl(DirectorySecurity security)
        {
            //
            // Subfolders and Files Only      CREATOR OWNER                 GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.CreatorOwnerSid, null),
                FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // This Folder Only               CREATOR OWNER                 GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.CreatorOwnerSid, null),
                FileSystemRights.FullControl,
                InheritanceFlags.None,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // Subfolders and Files Only      NT AUTHORITY\SYSTEM           GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null),
                FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // This Folder Only               NT AUTHORITY\SYSTEM           GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null),
                FileSystemRights.FullControl,
                InheritanceFlags.None,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // Subfolders and Files Only      BUILTIN\Administrators        GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null),
                FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // This Folder Only               BUILTIN\Administrators        GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null),
                FileSystemRights.FullControl,
                InheritanceFlags.None,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // Subfolders and Files Only      NT SERVICE\TrustedInstaller        GENERIC_ALL
            //
            SecurityIdentifier TrustedInstaller =
                new SecurityIdentifier("S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464");
            security.AddAccessRule(new FileSystemAccessRule(
                TrustedInstaller,
                FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // This Folder Only               NT SERVICE\TrustedInstaller        GENERIC_ALL
            //
            security.AddAccessRule(new FileSystemAccessRule(
                TrustedInstaller,
                FileSystemRights.FullControl,
                InheritanceFlags.None,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // Subfolders and Files Only      BUILTIN\Users                 GENERIC_READ | GENERIC_EXECUTE
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                FileSystemRights.ReadAndExecute,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                PropagationFlags.None,
                AccessControlType.Allow
                ));

            //
            // This Folder Only               BUILTIN\Users                 GENERIC_READ | GENERIC_EXECUTE
            //
            security.AddAccessRule(new FileSystemAccessRule(
                new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                FileSystemRights.ReadAndExecute,
                InheritanceFlags.None,
                PropagationFlags.None,
                AccessControlType.Allow
                ));
        }

        public void CreateInstallDirectory(string installDirectory)
        {
            if (!Directory.Exists(installDirectory))
            {
                DirectorySecurity security = new DirectorySecurity();
                InsertAdminOnlyAcl(security);
                Directory.CreateDirectory(installDirectory, security);
            }
            else
            {
                DirectorySecurity security = new DirectorySecurity();
                InsertAdminOnlyAcl(security);
                Directory.SetAccessControl(installDirectory, security);
            }
        }

        [ThreadStatic]
        private static byte[] CopyBuffer;

        public void CopyFile(string SourceFile, string DestinationFile)
        {
            const int BufferSize = 0x100000; //1 MB
            // Reuse CopyBuffer on a per-thread basis to prevent a 1 MB heap
            // allocation on every file copied, which will result in a large
            // number of garbage collections.
            if (CopyBuffer == null)
            {
                CopyBuffer = new byte[BufferSize];
            }
            byte[] buffer = CopyBuffer;

            using (FileStream src = new FileStream(SourceFile, FileMode.Open, FileAccess.Read, FileShare.ReadWrite, 1, FileOptions.SequentialScan))
            {
                using (FileStream dest = new FileStream(DestinationFile, FileMode.Create, FileAccess.Write, FileShare.ReadWrite, 1))
                {
                    dest.SetLength(src.Length);
                    int bytesRead = 1;
                    while (bytesRead > 0)
                    {
                        bytesRead = src.Read(buffer, 0, buffer.Length);
                        if (bytesRead > 0)
                        {
                            dest.Write(buffer, 0, bytesRead);
                        }
                    }
                    dest.Flush();
                }
            }
        }

        public List<Tuple<string, string>> BuildFileCopyManifest(string source, string destination)
        {
            List<Tuple<string, string>> manifest = new List<Tuple<string, string>>();
            AddFilesToCopyManifest(source, destination, manifest);
            return manifest;
        }

        private void AddFilesToCopyManifest(string source, string destination, List<Tuple<string, string>> manifest)
        {
            DirectoryInfo sourceDir = new DirectoryInfo(source);
            if (!sourceDir.Exists)
            {
                throw new DirectoryNotFoundException(string.Format("{0} Not Found", sourceDir.FullName));
            }
            if (!Directory.Exists(destination))
            {
                Directory.CreateDirectory(destination);
            }
            foreach (FileInfo file in sourceDir.EnumerateFiles())
            {
                manifest.Add(Tuple.Create(file.FullName, Path.Combine(destination, file.Name)));
            }
            foreach (DirectoryInfo SubDir in sourceDir.EnumerateDirectories())
            {
                AddFilesToCopyManifest(SubDir.FullName, Path.Combine(destination, SubDir.Name), manifest);
            }
        }

        public void CopyFiles(List<Tuple<string, string>> FileCopyManifest, ref int CurrentCount, Action<int> ReportProgress, Func<bool> CancelPending)
        {
            int LocalCount = CurrentCount;
            object ProgressLock = new object();
            ParallelOptions options = new ParallelOptions { MaxDegreeOfParallelism = Math.Min(8, Environment.ProcessorCount * 2) };

            Parallel.ForEach(FileCopyManifest, options, (FileToCopy, LoopState) =>
            {
                if (CancelPending != null && CancelPending())
                {
                    LoopState.Stop();
                    return;
                }
                CopyFile(FileToCopy.Item1, FileToCopy.Item2);
                if (ReportProgress != null)
                {
                    int NewCount = Interlocked.Increment(ref LocalCount);
                    // Serialize callback invocations since the caller's delegate mutates shared progress state.
                    lock (ProgressLock)
                    {
                        ReportProgress(NewCount);
                    }
                }
            });

            CurrentCount = LocalCount;
        }

        public void ClearReadOnlyAttribute(string directory)
        {
            if (!Directory.Exists(directory))
            {
                return;
            }
            DirectoryInfo directoryInfo = new DirectoryInfo(directory);
            foreach (FileInfo file in directoryInfo.EnumerateFiles())
            {
                file.Attributes &= ~FileAttributes.ReadOnly;
                file.Refresh();
            }
            foreach (DirectoryInfo dir in directoryInfo.EnumerateDirectories())
            {
                dir.Attributes &= ~FileAttributes.ReadOnly;
                dir.Refresh();
                ClearReadOnlyAttribute(dir.FullName);
            }
        }

        public void DeleteDirectory(string directory)
        {
            ClearReadOnlyAttribute(directory);
            if (!Directory.Exists(directory))
            {
                return;
            }
            DirectoryInfo directoryInfo = new DirectoryInfo(directory);
            foreach(DirectoryInfo dir  in directoryInfo.EnumerateDirectories())
            {
                DeleteDirectory(dir.FullName);
            }
            Directory.Delete(directory, true);
        }

        // Remove a registry key if it has nothing in it.
        private static void DeleteRegistryKeyIfEmpty(RegistryKey baseKey, string path)
        {
            try
            {
                using (RegistryKey key = baseKey.OpenSubKey(path))
                {
                    if (key == null || key.SubKeyCount != 0 || key.ValueCount != 0)
                    {
                        return;
                    }
                }
                baseKey.DeleteSubKey(path, false);
            }
            catch (InvalidOperationException)
            {
                // Something was added to the key after it was checked.
            }
        }

        private static readonly string[] ToolFileNames = { "edkclang-core.exe", "edkclang.cmd" };

        private static void VerifyPackage(string packageDirectory)
        {
            foreach (string name in ToolFileNames.Concat(new[] { GitBashIntegration.ScriptName }))
            {
                if (!File.Exists(Path.Combine(packageDirectory, name)))
                {
                    throw new FileNotFoundException(string.Format("The installer package is incomplete: {0} is missing.", name), name);
                }
            }
        }

        private static bool IsInstalledVersion(string root, string version)
        {
            return EdkClangLayout.IsVersionName(version) && File.Exists(Path.Combine(root, version, "bin", "clang.exe"));
        }

        private static bool IsVersionRegistered(string version)
        {
            using (RegistryKey uninstall = OpenUninstallKey(false))
            using (RegistryKey entry = uninstall.OpenSubKey(VersionProductCode(version)))
            {
                return entry != null;
            }
        }

        private void TryDeleteDirectory(string directory)
        {
            try
            {
                DeleteDirectory(directory);
            }
            catch (Exception e)
            {
                InstallLogger.Log(string.Format("Could not delete {0}: {1}", directory, e.Message));
            }
        }

        //
        // The installation directory is created with an administrators-only ACL. An existing directory that
        // already holds files is left alone. Changing its ACL would also change the ACL of every installed version.
        //
        private void EnsureInstallRoot(string root)
        {
            if (!Directory.Exists(root) || !Directory.EnumerateFileSystemEntries(root).Any())
            {
                CreateInstallDirectory(root);
            }
        }

        //
        // Moves an install made by the legacy installer (which put clang directly in the installation directory)
        // into its own version folder. Returns the version that was moved, or null if there was nothing to migrate.
        //
        private string MigrateLegacyInstall(string root)
        {
            if (!IsLegacyLayout(root))
            {
                return null;
            }
            string legacyVersion = DetectLegacyVersion(root);
            if (legacyVersion == null)
            {
                throw new InvalidOperationException(string.Format(
                    "An existing installation was found in {0}, but its version could not be determined. Uninstall it and run this installer again.", root));
            }
            string legacyDirectory = Path.Combine(root, legacyVersion);
            if (Directory.Exists(legacyDirectory))
            {
                throw new InvalidOperationException(string.Format(
                    "Cannot move the existing installation to {0} because that folder already exists.", legacyDirectory));
            }

            InstallLogger.Log(string.Format("Found legacy installation of edk2-clang {0}. Moving it to {1}...", legacyVersion, legacyDirectory));
            string uninstallerName = Path.GetFileName(WindowsHelpers.GetApplicationPath());
            string vendorPluginName = VendorCustomizer.Instance != null ? Path.GetFileName(VendorCustomizer.VendorPluginPath) : null;
            List<FileSystemInfo> toMove = new List<FileSystemInfo>();
            foreach (FileSystemInfo entry in new DirectoryInfo(root).EnumerateFileSystemInfos())
            {
                if (string.Equals(entry.Name, uninstallerName, StringComparison.OrdinalIgnoreCase) ||
                    (vendorPluginName != null && string.Equals(entry.Name, vendorPluginName, StringComparison.OrdinalIgnoreCase)) ||
                    string.Equals(entry.Name, InstallerStrings.ToolsDirectoryName, StringComparison.OrdinalIgnoreCase) ||
                    EdkClangLayout.IsVersionName(entry.Name))
                {
                    continue;
                }
                toMove.Add(entry);
            }

            CreateInstallDirectory(legacyDirectory);
            List<Tuple<string, string>> moved = new List<Tuple<string, string>>();
            try
            {
                foreach (FileSystemInfo entry in toMove)
                {
                    string destination = Path.Combine(legacyDirectory, entry.Name);
                    if (entry is DirectoryInfo)
                    {
                        Directory.Move(entry.FullName, destination);
                    }
                    else
                    {
                        File.Move(entry.FullName, destination);
                    }
                    moved.Add(Tuple.Create(entry.FullName, destination));
                }
            }
            catch (Exception e)
            {
                for (int i = moved.Count - 1; i >= 0; i--)
                {
                    try
                    {
                        if (Directory.Exists(moved[i].Item2))
                        {
                            Directory.Move(moved[i].Item2, moved[i].Item1);
                        }
                        else
                        {
                            File.Move(moved[i].Item2, moved[i].Item1);
                        }
                    }
                    catch (Exception undoError)
                    {
                        InstallLogger.Log(string.Format("Could not move {0} back: {1}", moved[i].Item2, undoError.Message));
                    }
                }
                try
                {
                    Directory.Delete(legacyDirectory);
                }
                catch (IOException)
                {
                }
                throw new IOException(string.Format(
                    "Could not move the existing installation into {0}. Close any programs that are using files in {1} and try again. ({2})",
                    legacyDirectory, root, e.Message), e);
            }

            RetargetDefaults(delegate (string value)
            {
                return EdkClangLayout.IsSamePath(value, root) ? legacyDirectory : null;
            });
            return legacyVersion;
        }

        private static Version ReadInstalledEngineVersion()
        {
            using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            using (RegistryKey state = hklm.OpenSubKey(InstallerStrings.StateRegistryKeyPath))
            {
                Version version;
                string text = state == null ? null : state.GetValue("EngineVersion") as string;
                return Version.TryParse(text, out version) ? version : null;
            }
        }

        //
        // The uninstaller, the vendor plugin and the edkclang command are shared by every installed version.
        // They are only written when the engine on disk is older than the one packaged in the self-extracting
        // archive, so an older installer won't replace a newer uninstaller.
        //
        private void InstallSharedFiles(string root, string packageDirectory, bool forceRefresh)
        {
            string toolsDirectory = Path.Combine(root, InstallerStrings.ToolsDirectoryName);
            string applicationPath = WindowsHelpers.GetApplicationPath();
            string uninstallerPath = Path.Combine(root, Path.GetFileName(applicationPath));
            string vendorPluginPath = VendorCustomizer.Instance != null
                ? Path.Combine(root, Path.GetFileName(VendorCustomizer.VendorPluginPath))
                : null;

            Version onDisk = ReadInstalledEngineVersion();
            Version packaged = EngineVersion;
            bool refresh = forceRefresh ||
                onDisk == null ||
                onDisk < packaged ||
                !File.Exists(uninstallerPath) ||
                (vendorPluginPath != null && !File.Exists(vendorPluginPath)) ||
                ToolFileNames.Any(name => !File.Exists(Path.Combine(toolsDirectory, name)));
            if (!refresh)
            {
                InstallLogger.Log(string.Format("The installed shared tools (v{0}) are up to date.", onDisk));
                return;
            }

            InstallLogger.Log("Installing shared tools...");
            CopyFile(applicationPath, uninstallerPath);
            if (vendorPluginPath != null)
            {
                CopyFile(VendorCustomizer.VendorPluginPath, vendorPluginPath);
            }
            CreateInstallDirectory(toolsDirectory);
            foreach (string name in ToolFileNames)
            {
                CopyFile(Path.Combine(packageDirectory, name), Path.Combine(toolsDirectory, name));
            }

            using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            using (RegistryKey state = hklm.CreateSubKey(InstallerStrings.StateRegistryKeyPath))
            {
                state.SetValue("EngineVersion", packaged.ToString());
            }
        }

        private static int? GetEstimatedSizeInKilobytes(string versionDirectory)
        {
            if (VendorCustomizer.Instance != null)
            {
                return VendorCustomizer.Instance.UninstallEstimatedSize;
            }
            try
            {
                long bytes = new DirectoryInfo(versionDirectory)
                    .EnumerateFiles("*", SearchOption.AllDirectories)
                    .Sum(file => file.Length);
                return (int)Math.Min(int.MaxValue, (bytes + 1023) / 1024);
            }
            catch (Exception e)
            {
                InstallLogger.Log(string.Format("Could not measure {0}: {1}", versionDirectory, e.Message));
                return null;
            }
        }

        private static void WriteVersionUninstallKey(string root, string version, string displayVersion)
        {
            string uninstallerPath = Path.Combine(root, Path.GetFileName(WindowsHelpers.GetApplicationPath()));
            int? estimatedSize = GetEstimatedSizeInKilobytes(Path.Combine(root, version));
            using (RegistryKey uninstall = OpenUninstallKey())
            using (RegistryKey key = uninstall.CreateSubKey(VersionProductCode(version)))
            {
                key.SetValue("DisplayName", InstallerStrings.VersionDisplayName(version));
                key.SetValue("UninstallString", string.Format("\"{0}\" /Uninstall /Version {1}", uninstallerPath, version));
                key.SetValue("DisplayIcon", uninstallerPath);
                key.SetValue("Publisher", InstallerStrings.UninstallPublisher);
                key.SetValue("DisplayVersion", displayVersion);
                key.SetValue("NoModify", 1);
                key.SetValue("NoRepair", 1);
                if (estimatedSize.HasValue)
                {
                    key.SetValue("EstimatedSize", estimatedSize.Value, RegistryValueKind.DWord);
                }
                key.SetValue("EdkClangBaseProductCode", InstallerStrings.ProductCode);
                key.SetValue("EdkClangToolchainVersion", version);
            }
        }

        //
        // Ensure every installed version has a Programs and Features entry,
        // and remove any entries created by the old installer.
        //
        private static void RegisterInstalledVersions(string root, string newVersion)
        {
            foreach (InstalledVersion installed in EdkClangLayout.EnumerateInstalledVersions(root))
            {
                if (!installed.IsComplete)
                {
                    continue;
                }
                bool hasEntry;
                using (RegistryKey uninstall = OpenUninstallKey())
                using (RegistryKey existing = uninstall.OpenSubKey(VersionProductCode(installed.Name)))
                {
                    hasEntry = existing != null;
                }
                if (installed.Name == newVersion)
                {
                    WriteVersionUninstallKey(root, installed.Name, InstallerStrings.UninstallDisplayVersion);
                }
                else if (!hasEntry)
                {
                    WriteVersionUninstallKey(root, installed.Name, installed.Name);
                }
            }
            using (RegistryKey uninstall = OpenUninstallKey())
            {
                uninstall.DeleteSubKeyTree(InstallerStrings.ProductCode, false);
            }
        }

        //
        // Removes versions that the new version replaces. Any errors are logged
        // but do not cause an installation failure since the new version is
        // already in place. Defaults that selected a removed version move to
        // the new version.
        //
        private void UninstallOlderVersions(string root, List<string> versions, string replacementVersion)
        {
            if (versions.Count == 0)
            {
                return;
            }
            string replacementDirectory = Path.Combine(root, replacementVersion);
            List<string> removedDirectories = new List<string>();
            foreach (string version in versions)
            {
                string directory = Path.Combine(root, version);
                InstallLogger.Log(string.Format("Removing the older version {0}...", version));
                removedDirectories.Add(directory);
                try
                {
                    DeleteDirectory(directory);
                }
                catch (Exception e)
                {
                    InstallLogger.Log(string.Format(
                        "Could not remove {0}: {1}.",
                        directory, e.Message));
                    continue;
                }
                using (RegistryKey uninstall = OpenUninstallKey())
                {
                    uninstall.DeleteSubKeyTree(VersionProductCode(version), false);
                }
            }
            RetargetDefaults(delegate (string value)
            {
                return removedDirectories.Any(d => EdkClangLayout.IsSameOrUnder(value, d)) ? replacementDirectory : null;
            });
        }

        public void PerformInstall(Action<bool, bool> ReportComplete, Action<int> ReportProgress, Action<bool> AllowCancel, Func<bool> CancelPending)
        {
            if (ReportProgress == null || ReportComplete == null || AllowCancel == null || CancelPending == null)
            {
                throw new ArgumentException();
            }
            bool FailureReported = false;
            Action ReportFailure = new Action(delegate () { FailureReported = true; });
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance.WriteToInstallLog = new Action<string>(InstallLogger.Log);
            }
            string toolchainVersion = ToolchainVersion;
            string installRoot = GetDefaultInstallRoot();
            string packageDirectory = Path.GetDirectoryName(WindowsHelpers.GetApplicationPath());
            string sourcePath = Path.Combine(packageDirectory, InstallerStrings.SourceDirectory);

            //
            // Step 1 - Make sure the package is complete
            //
            VerifyPackage(packageDirectory);

            //
            // Step 2 - Invoke the Pre-Install Event
            //
            if (VendorCustomizer.Instance != null)
            {
                installRoot = VendorCustomizer.Instance?.PreInstallEvent(installRoot, ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }
            if (CancelPending())
            {
                ReportComplete(true, true);
                return;
            }

            //
            // Step 3 - If an older installer put clang directly in the installation directory, move it into a
            // versioned folder so side-by-side clang installs are possible. Once it is moved, only the new
            // uninstaller can remove it, so cancelling is not allowed from here on.
            //
            bool cancelLocked = IsLegacyLayout(installRoot);
            if (cancelLocked)
            {
                AllowCancel(false);
            }
            Func<bool> CancelRequested = () => !cancelLocked && CancelPending();
            string migratedVersion = MigrateLegacyInstall(installRoot);
            List<string> olderVersions = RemoveOlderSameMajorVersions
                ? GetOlderSameMajorVersions(installRoot, toolchainVersion)
                : new List<string>();
            if (CancelRequested())
            {
                ReportComplete(true, true);
                return;
            }

            //
            // Step 4 - If this version's folder already exists, replace it.
            //
            string versionDirectory = Path.Combine(installRoot, toolchainVersion);
            if (Directory.Exists(versionDirectory))
            {
                bool known = migratedVersion == toolchainVersion || IsVersionRegistered(toolchainVersion);
                if (!known && !SilentMode && !cancelLocked)
                {
                    bool proceed = FluentDialogs.AskYesNo(
                        InstallerStrings.InstallerName,
                        string.Format("The folder {0} already exists, but {1} {2} is not registered as installed. Its contents will be replaced. Would you like to continue installation?", versionDirectory, InstallerStrings.ProductName, toolchainVersion),
                        TimeSpan.FromSeconds(120));
                    if (!proceed)
                    {
                        InstallLogger.Log(string.Format("Installation cancelled: replacing {0} was not allowed.", versionDirectory));
                        InstallLogger.Log("No new files were copied. Run the installer again and choose Yes to replace the existing contents.");
                        ReportComplete(false, false);
                        return;
                    }
                }
                InstallLogger.Log(string.Format("Replacing the existing {0}...", versionDirectory));
                try
                {
                    DeleteDirectory(versionDirectory);
                }
                catch (Exception e)
                {
                    throw new IOException(string.Format(
                        "Could not remove the existing {0}. Close any programs that are using files in it and try again. ({1})",
                        versionDirectory, e.Message), e);
                }
            }

            //
            // Step 5 - Invoke the Pre-Copy Event
            //
            if (CancelRequested())
            {
                ReportComplete(true, true);
                return;
            }
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance?.PreCopyEvent(ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }

            //
            // Step 6 - Copy the files
            //
            int CompletionPercent = 0;
            int LastCompletionPercent = 0;
            int CurrentCount = 0;
            InstallLogger.Log(string.Format("Copying files to {0}...", versionDirectory));
            EnsureInstallRoot(installRoot);
            CreateInstallDirectory(versionDirectory);
            try
            {
                List<Tuple<string, string>> FileCopyManifest = BuildFileCopyManifest(sourcePath, versionDirectory);
                int FileCount = FileCopyManifest.Count;
                CopyFiles(FileCopyManifest, ref CurrentCount, delegate (int CurrentFileCount)
                {
                    CompletionPercent = (CurrentFileCount * 100) / FileCount;
                    if (CompletionPercent > LastCompletionPercent)
                    {
                        ReportProgress(CompletionPercent);
                        LastCompletionPercent = CompletionPercent;
                    }
                }, CancelRequested);
            }
            catch
            {
                // A half-copied folder would be listed as an installed version.
                TryDeleteDirectory(versionDirectory);
                throw;
            }
            AllowCancel(false);
            if (CancelRequested())
            {
                TryDeleteDirectory(versionDirectory);
                ReportComplete(true, true);
                return;
            }

            //
            // Step 7 - Invoke the Finish-Install Event
            //
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance?.FinishInstallEvent(ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }

            //
            // Step 8 - Install the shared files, and put the edkclang command on the system PATH
            //
            InstallLogger.Log(string.Format("Completing Install..."));
            InstallSharedFiles(installRoot, packageDirectory, migratedVersion != null);
            string toolsDirectory = Path.Combine(installRoot, InstallerStrings.ToolsDirectoryName);
            if (EdkClangLayout.AddToMachinePath(toolsDirectory))
            {
                InstallLogger.Log(string.Format("Added {0} to the system PATH.", toolsDirectory));
            }
            GitBashIntegration.Install(packageDirectory);

            //
            // Step 9 - Choose the system default version
            //
            string defaultVersion = DefaultVersionChoice;
            if (string.IsNullOrEmpty(defaultVersion) || !IsInstalledVersion(installRoot, defaultVersion) || olderVersions.Contains(defaultVersion))
            {
                defaultVersion = ChooseDefaultAutomatically(installRoot, toolchainVersion);
            }
            SetSystemDefault(Path.Combine(installRoot, defaultVersion));

            //
            // Step 10 - Remove the older versions of this release series
            //
            UninstallOlderVersions(installRoot, olderVersions, toolchainVersion);

            //
            // Step 11 - Create Programs and Features uninstall links
            //
            RegisterInstalledVersions(installRoot, toolchainVersion);
            EdkClangLayout.BroadcastEnvironmentChange();

            InstallLogger.Log("Installation Successful");
            ReportComplete(true, false);
        }

        //
        // After the last version is uninstalled the uninstaller deletes itself and the installation directory,
        // if nothing else is in it. It cannot do that while it is running, so a helper does it after it exits.
        //
        public static void StartSelfCleanupIfLastVersionRemoved()
        {
            if (!RemovedLastVersion)
            {
                return;
            }
            string applicationPath = WindowsHelpers.GetApplicationPath();
            string root = Path.GetDirectoryName(applicationPath);
            StringBuilder command = new StringBuilder("/c cd /d \"%SystemRoot%\" & choice /d y /t 3 > nul");
            command.AppendFormat(" & del /F /Q \"{0}\"", applicationPath);
            if (VendorCustomizer.Instance != null)
            {
                command.AppendFormat(" & del /F /Q \"{0}\"", Path.Combine(root, Path.GetFileName(VendorCustomizer.VendorPluginPath)));
            }
            command.AppendFormat(" & rmdir \"{0}\"", root);
            command.AppendFormat(" & if exist \"{0}\" (choice /d y /t 5 > nul & rmdir \"{0}\")", root);
            SilentProcess.StartConsoleProcessSilently("cmd.exe", command.ToString());
        }

        public void PerformUninstall(Action<bool, bool> ReportComplete, Action<int> ReportProgress, Action<bool> AllowCancel, Func<bool> CancelPending)
        {
            bool FailureReported = false;
            Action ReportFailure = new Action(delegate () { FailureReported = true; });
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance.WriteToInstallLog = new Action<string>(InstallLogger.Log);
            }
            string installRoot = Path.GetDirectoryName(WindowsHelpers.GetApplicationPath());
            RemovedLastVersion = false;

            //
            // Step 1 - Determine which version to remove.
            //
            string version = UninstallVersion;
            if (version == null)
            {
                List<InstalledVersion> installed = EdkClangLayout.EnumerateInstalledVersions(installRoot);
                if (installed.Count > 1)
                {
                    throw new InvalidOperationException(string.Format(
                        "More than one version is installed ({0}). Run the uninstaller with /Version <version>.",
                        string.Join(", ", installed.Select(v => v.Name))));
                }
                if (installed.Count == 1)
                {
                    version = installed[0].Name;
                }
            }
            else if (!EdkClangLayout.IsVersionName(version))
            {
                throw new ArgumentException(string.Format("'{0}' is not a version number such as 20.1.8.", version));
            }

            //
            // Step 2 - Invoke the Pre-Uninstall Event
            //
            if (VendorCustomizer.Instance != null)
            {
                installRoot = VendorCustomizer.Instance?.PreUninstallEvent(installRoot, version ?? string.Empty, ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }
            AllowCancel(false);
            if (CancelPending())
            {
                ReportComplete(true, true);
                return;
            }

            //
            // Step 3 - Delete the files of that version
            //
            string versionDirectory = version == null ? null : Path.Combine(installRoot, version);
            if (versionDirectory != null && Directory.Exists(versionDirectory))
            {
                InstallLogger.Log(string.Format("Deleting files in {0}...", versionDirectory));
                DeleteDirectory(versionDirectory);
            }

            //
            // Step 4 - Point all instances of BASETOOLS_MINGW_PATH that selected the removed
            // version to the newest version that remains, or remove it if no version is left.
            //
            List<InstalledVersion> remaining = EdkClangLayout.EnumerateInstalledVersions(installRoot)
                .Where(v => v.IsComplete && v.Name != version)
                .ToList();
            InstalledVersion fallback = remaining.OrderByDescending(v => v.Version).FirstOrDefault();
            RetargetDefaults(delegate (string value)
            {
                if (versionDirectory != null && EdkClangLayout.IsSameOrUnder(value, versionDirectory))
                {
                    return fallback != null ? fallback.FullPath : string.Empty;
                }
                if (fallback == null && EdkClangLayout.IsSameOrUnder(value, installRoot))
                {
                    return string.Empty;
                }
                return null;
            });

            //
            // Step 5 - Invoke the Finish Uninstall Event
            //
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance?.FinishUninstallEvent(version ?? string.Empty, ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }

            //
            // Step 6 - Delete the Programs and Features uninstall link for the version that was removed
            //
            using (RegistryKey uninstall = OpenUninstallKey())
            {
                if (version != null)
                {
                    uninstall.DeleteSubKeyTree(VersionProductCode(version), false);
                }
                if (remaining.Count == 0)
                {
                    uninstall.DeleteSubKeyTree(InstallerStrings.ProductCode, false);
                }
            }

            //
            // Step 7 - If this is the last version, remove what is shared: the edkclang command,
            // its PATH entry and the installer's state.
            //
            if (remaining.Count == 0)
            {
                string toolsDirectory = Path.Combine(installRoot, InstallerStrings.ToolsDirectoryName);
                if (Directory.Exists(toolsDirectory))
                {
                    DeleteDirectory(toolsDirectory);
                }
                if (EdkClangLayout.RemoveFromMachinePath(toolsDirectory))
                {
                    InstallLogger.Log(string.Format("Removed {0} from the system PATH.", toolsDirectory));
                }
                GitBashIntegration.Remove();
                using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                {
                    hklm.DeleteSubKeyTree(InstallerStrings.StateRegistryKeyPath, false);
                    try
                    {
                        hklm.DeleteSubKey(@"SOFTWARE\TianoCore\EdkClangMingw", false);
                    }
                    catch (InvalidOperationException)
                    {
                        // Another product variant still has its state there.
                    }
                    DeleteRegistryKeyIfEmpty(hklm, @"SOFTWARE\TianoCore");
                }
                RemovedLastVersion = true;
            }
            EdkClangLayout.BroadcastEnvironmentChange();

            InstallLogger.Log("Uninstall Complete");
            ReportComplete(true, false);
        }
    }
}
