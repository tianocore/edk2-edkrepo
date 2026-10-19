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
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace TianoCore.EdkMingwInstaller
{
    public class InstallWorker
    {
        public static bool SilentMode { get; set; }

        public void SetBaseToolsMingwPathEnvironmentVariable(string path)
        {
            RegistryKey Hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey EnvironmentRegistryKey = Hklm.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", RegistryKeyPermissionCheck.ReadWriteSubTree);
            string MingwPathValueName = null;
            foreach (string ValueName in EnvironmentRegistryKey.GetValueNames())
            {
                if (string.Compare(ValueName, InstallerStrings.BaseToolsMingwPath, StringComparison.OrdinalIgnoreCase) == 0)
                {
                    MingwPathValueName = ValueName;
                    break;
                }
            }
            if (!string.IsNullOrEmpty(MingwPathValueName))
            {
                EnvironmentRegistryKey.DeleteValue(MingwPathValueName);
            }
            EnvironmentRegistryKey.SetValue(InstallerStrings.BaseToolsMingwPath, path);
            WindowsHelpers.SendEnvironmentVariableChangedMessage();
            InstallLogger.Log(string.Format("Created {0} environment variable.", InstallerStrings.BaseToolsMingwPath));
        }

        public void DeleteBaseToolsMingwPathEnvironmentVariable()
        {
            RegistryKey Hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey EnvironmentRegistryKey = Hklm.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", RegistryKeyPermissionCheck.ReadWriteSubTree);
            string MingwPathValueName = null;
            foreach (string ValueName in EnvironmentRegistryKey.GetValueNames())
            {
                if (string.Compare(ValueName, InstallerStrings.BaseToolsMingwPath, StringComparison.OrdinalIgnoreCase) == 0)
                {
                    MingwPathValueName = ValueName;
                    break;
                }
            }
            if (!string.IsNullOrEmpty(MingwPathValueName))
            {
                EnvironmentRegistryKey.DeleteValue(MingwPathValueName);
            }
            WindowsHelpers.SendEnvironmentVariableChangedMessage();
            InstallLogger.Log(string.Format("Deleted {0} environment variable.", InstallerStrings.BaseToolsMingwPath));
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
            string installPath = Path.Combine(
                Path.GetPathRoot(Environment.GetFolderPath(Environment.SpecialFolder.Windows)),
                InstallerStrings.InstallationDirectory);
            string sourcePath = Path.Combine(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()), InstallerStrings.SourceDirectory);

            //
            // Step 1 - Invoke the Pre-Install Event
            //
            if (VendorCustomizer.Instance != null)
            {
                installPath = VendorCustomizer.Instance?.PreInstallEvent(installPath, ReportFailure);
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
            // Step 2 - If EdkMingw is already installed, uninstall the currently installed version
            //
            string ProductCode = null;
            if (VendorCustomizer.Instance != null)
            {
                ProductCode = VendorCustomizer.Instance.ProductCode;
            }
            else
            {
                ProductCode = InstallerStrings.ProductCode;
            }
            RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey winUninstallRegistryKey = hklm.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", true);
            if (!string.IsNullOrWhiteSpace(ProductCode))
            {
                RegistryKey uninstallKey = winUninstallRegistryKey.OpenSubKey(ProductCode, true);
                if (uninstallKey != null)
                {
                    InstallLogger.Log(string.Format("Uninstalling current version of {0}", InstallerStrings.ProductName));
                    if (CancelPending())
                    {
                        ReportComplete(true, true);
                        return;
                    }
                    string uninstallString = string.Format("{0} /Silent", uninstallKey.GetValue("UninstallString"));
                    SilentProcess p = SilentProcess.StartConsoleProcessSilently("cmd.exe", string.Format("/S /C \"{0}\"", uninstallString));
                    p.WaitForExit();
                    Thread.Sleep(4000);
                    InstallLogger.Log(string.Format("{0} uninstalled.", InstallerStrings.ProductName));
                }
            }

            //
            // Step 3 - Check if the installation path exists, if it does ask the user if it is OK to delete it
            //
            if (CancelPending())
            {
                ReportComplete(true, true);
                return;
            }
            if (Directory.Exists(installPath))
            {
                if (!SilentMode)
                {
                    bool proceed = FluentDialogs.AskYesNo(
                        InstallerStrings.InstallerName,
                        string.Format("The contents of the folder {0} will be overwritten by {1}, would you like to continue installation?", installPath, InstallerStrings.ProductName),
                        TimeSpan.FromSeconds(120));
                    if (!proceed)
                    {
                        InstallLogger.Log(string.Format("Installation cancelled: the overwrite of {0} was not allowed.", installPath));
                        InstallLogger.Log("No new files were copied. Run the installer again and choose Yes to replace the existing contents.");
                        ReportComplete(false, false);
                        return;
                    }
                }
                InstallLogger.Log(string.Format("Deleting contents of {0}", installPath));
                DeleteDirectory(installPath);
            }

            //
            // Step 4 - Invoke the Pre-Copy Event
            //
            if (CancelPending())
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
            // Step 5 - Copy the files
            //
            int CompletionPercent = 0;
            int LastCompletionPercent = 0;
            int CurrentCount = 0;
            InstallLogger.Log(string.Format("Copying files..."));
            CreateInstallDirectory(installPath);
            List<Tuple<string, string>> FileCopyManifest = BuildFileCopyManifest(sourcePath, installPath);
            int FileCount = FileCopyManifest.Count;
            CopyFiles(FileCopyManifest, ref CurrentCount, delegate(int CurrentFileCount)
            {
                CompletionPercent = (CurrentFileCount * 100) / FileCount;
                if (CompletionPercent > LastCompletionPercent)
                {
                    ReportProgress(CompletionPercent);
                    LastCompletionPercent = CompletionPercent;
                }
            }, CancelPending);
            AllowCancel(false);
            if (CancelPending())
            {
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
            // Step 8 - Create the BASETOOLS_MINGW_PATH Environment Variable
            //
            SetBaseToolsMingwPathEnvironmentVariable(installPath);

            //
            // Step 9 - Create Programs and Features uninstall links
            //
            InstallLogger.Log(string.Format("Completing Install..."));
            string VendorPluginPath = string.Empty;
            if (VendorCustomizer.Instance != null)
            {
                VendorPluginPath = Path.Combine(installPath, Path.GetFileName(VendorCustomizer.VendorPluginPath));
            }
            string UninstallerPath = Path.Combine(installPath, Path.GetFileName(WindowsHelpers.GetApplicationPath()));
            if (File.Exists(UninstallerPath))
            {
                File.Delete(UninstallerPath);
            }
            CopyFile(WindowsHelpers.GetApplicationPath(), UninstallerPath);
            if (VendorCustomizer.Instance != null)
            {
                if (File.Exists(VendorPluginPath))
                {
                    File.Delete(VendorPluginPath);
                }
                CopyFile(VendorCustomizer.VendorPluginPath, VendorPluginPath);
            }
            RegistryKey edkMingwUninstallKey = winUninstallRegistryKey.OpenSubKey(InstallerStrings.ProductCode, true);
            if (edkMingwUninstallKey == null)
            {
                edkMingwUninstallKey = winUninstallRegistryKey.CreateSubKey(InstallerStrings.ProductCode);
            }
            edkMingwUninstallKey.SetValue("DisplayName", InstallerStrings.UninstallDisplayName);
            edkMingwUninstallKey.SetValue("UninstallString", string.Format("\"{0}\" /Uninstall", UninstallerPath));
            edkMingwUninstallKey.SetValue("DisplayIcon", UninstallerPath);
            edkMingwUninstallKey.SetValue("Publisher", InstallerStrings.UninstallPublisher);
            edkMingwUninstallKey.SetValue("DisplayVersion", InstallerStrings.UninstallDisplayVersion);
            edkMingwUninstallKey.SetValue("NoModify", 1);
            edkMingwUninstallKey.SetValue("NoRepair", 1);
            edkMingwUninstallKey.SetValue("EstimatedSize", InstallerStrings.UninstallEstimatedSize);

            InstallLogger.Log("Installation Successful");
            ReportComplete(true, false);
        }

        public void PerformUninstall(Action<bool, bool> ReportComplete, Action<int> ReportProgress, Action<bool> AllowCancel, Func<bool> CancelPending)
        {
            bool FailureReported = false;
            Action ReportFailure = new Action(delegate () { FailureReported = true; });
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance.WriteToInstallLog = new Action<string>(InstallLogger.Log);
            }
            string installPath = Path.GetDirectoryName(WindowsHelpers.GetApplicationPath());

            //
            // Step 1 - Invoke the Pre-Install Event
            //
            if (VendorCustomizer.Instance != null)
            {
                installPath = VendorCustomizer.Instance?.PreUninstallEvent(installPath, ReportFailure);
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
            // Step 2 - Delete the files
            //
            InstallLogger.Log(string.Format("Deleting files..."));
            DirectoryInfo directoryInfo = new DirectoryInfo(installPath);
            directoryInfo.Attributes &= ~FileAttributes.ReadOnly;
            directoryInfo.Refresh();
            foreach (DirectoryInfo dir in directoryInfo.EnumerateDirectories())
            {
                DeleteDirectory(dir.FullName);
            }
            string AppPath = WindowsHelpers.GetApplicationPath();
            foreach (FileInfo file in directoryInfo.EnumerateFiles())
            {
                if (!WindowsHelpers.IsSameFile(file.FullName, AppPath))
                {
                    if (VendorCustomizer.Instance != null)
                    {
                        if (!WindowsHelpers.IsSameFile(file.FullName, VendorCustomizer.VendorPluginPath))
                        {
                            file.Delete();
                        }
                    }
                    else
                    {
                        file.Delete();
                    }
                }
            }

            //
            // Step 3 - Delete the BASETOOLS_MINGW_PATH Environment Variable
            //
            DeleteBaseToolsMingwPathEnvironmentVariable();

            //
            // Step 4 - Invoke the Finish Uninstall Event
            //
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance?.FinishUninstallEvent(ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }

            //
            // Step 5 - Delete Programs and Feature uninstall link
            //
            RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey winUninstallRegistryKey = hklm.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", true);
            RegistryKey edkMingwUninstallKey = winUninstallRegistryKey.OpenSubKey(InstallerStrings.ProductCode, true);
            if (edkMingwUninstallKey != null)
            {
                edkMingwUninstallKey.Close();
                winUninstallRegistryKey.DeleteSubKey(InstallerStrings.ProductCode);
            }

            InstallLogger.Log("Uninstall Complete");
            ReportComplete(true, false);
        }
    }
}
