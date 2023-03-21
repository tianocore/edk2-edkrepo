/** @file
  InstallWorker.cs

@copyright
  Copyright 2017 - 2023 Intel Corporation. All rights reserved.<BR>
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

namespace TianoCore.EdkRepoInstaller
{
    public class InstallWorker
    {
        private void UninstallExistingExclusivePackages(
            List<Tuple<string, PythonVersion>> ExclusivePackages,
            List<PythonVersion> PythonVersions,
            Action<bool, bool> ReportComplete,
            Action<int> ReportProgress,
            Action<bool> AllowCancel,
            Func<bool> CancelPending,
            List<PythonVersion> ObsoletedPythonVersions
            )
        {
            if (ExclusivePackages.Count > 0 && PythonVersions.Count > 0)
            {
                InstallLogger.Log("Determining currently installed Python packages...");
                bool FoundConflicting = false;
                List<Tuple<string, PythonVersion>> PythonPaths = new List<Tuple<string, PythonVersion>>();
                foreach (PythonVersion PyVersion in PythonVersions)
                {
                    bool Has32Bit;
                    bool Has64Bit;
                    PythonOperations.GetPythonBitness(PyVersion.Major, PyVersion.Minor, out Has32Bit, out Has64Bit);
                    string PythonPath = PythonOperations.FindPython(PyVersion.Major, PyVersion.Minor, false);
                    PythonPaths.Add(new Tuple<string, PythonVersion>(PythonPath, PyVersion));
                    if (Has32Bit && Has64Bit)
                    {
                        PythonPath = PythonOperations.FindPython(PyVersion.Major, PyVersion.Minor, true);
                        PythonPaths.Add(new Tuple<string, PythonVersion>(PythonPath, PyVersion));
                    }
                    if (CancelPending())
                    {
                        ReportComplete(true, true);
                        return;
                    }
                }
                foreach (Tuple<string, PythonVersion> PythonPath in PythonPaths)
                {
                    List<PythonPackage> InstalledPackages = PythonOperations.GetInstalledPythonPackages(PythonPath.Item1);
                    foreach (PythonPackage Package in InstalledPackages)
                    {
                        if (ExclusivePackages.Select(p => p.Item1).Contains(Package.Name))
                        {
                            AllowCancel(false);
                            if (CancelPending())
                            {
                                ReportComplete(true, true);
                                return;
                            }
                            FoundConflicting = true;
                            PythonVersion newPyVersion = ExclusivePackages.Where(p => p.Item1 == Package.Name).First().Item2;
                            if (newPyVersion.Major != PythonPath.Item2.Major || newPyVersion.Minor != PythonPath.Item2.Minor)
                            {
                                if (!ObsoletedPythonVersions.Contains(PythonPath.Item2))
                                {
                                    ObsoletedPythonVersions.Add(PythonPath.Item2);
                                }
                            }
                            InstallLogger.Log(string.Format("Uninstalling current version of {0}", Package.Name));
                            PythonOperations.UninstallPythonPackage(PythonPath.Item1, Package.Name);
                        }
                    }
                }
                if (!FoundConflicting)
                {
                    InstallLogger.Log("No conflicting Python packages found.");
                }
            }
        }

        private List<Tuple<string, PythonVersion>> GetExistingEdkRepoPaths(
            List<PythonVersion> PythonVersions,
            Action<bool, bool> ReportComplete,
            Action<int> ReportProgress,
            Action<bool> AllowCancel,
            Func<bool> CancelPending
            )
        {
            List<Tuple<string, PythonVersion>> EdkRepoPaths = new List<Tuple<string, PythonVersion>>();
            if (PythonVersions.Count > 0)
            {
                InstallLogger.Log(string.Format("Searching for existing {0} installations...", InstallerStrings.ProductName));
                List<Tuple<string, PythonVersion>> PythonPaths = new List<Tuple<string, PythonVersion>>();
                foreach (PythonVersion PyVersion in PythonVersions)
                {
                    bool Has32Bit;
                    bool Has64Bit;
                    PythonOperations.GetPythonBitness(PyVersion.Major, PyVersion.Minor, out Has32Bit, out Has64Bit);
                    string PythonPath = PythonOperations.FindPython(PyVersion.Major, PyVersion.Minor, false);
                    PythonPaths.Add(new Tuple<string, PythonVersion>(PythonPath, PyVersion));
                    if (Has32Bit && Has64Bit)
                    {
                        PythonPath = PythonOperations.FindPython(PyVersion.Major, PyVersion.Minor, true);
                        PythonPaths.Add(new Tuple<string, PythonVersion>(PythonPath, PyVersion));
                    }
                    if (CancelPending())
                    {
                        ReportComplete(true, true);
                        return null;
                    }
                }
                foreach (Tuple<string, PythonVersion> PythonPath in PythonPaths)
                {
                    List<PythonPackage> InstalledPackages = PythonOperations.GetInstalledPythonPackages(PythonPath.Item1);
                    foreach (PythonPackage Package in InstalledPackages)
                    {
                        if (Package.Name == InstallerStrings.EdkrepoPackageName)
                        {
                            EdkRepoPaths.Add(PythonPath);
                        }
                    }
                    if (CancelPending())
                    {
                        ReportComplete(true, true);
                        return null;
                    }
                }
            }
            return EdkRepoPaths;
        }

        public byte[] ReadFile(string filename)
        {
            using (BinaryReader reader = new BinaryReader(File.Open(filename, FileMode.Open)))
            {
                using (MemoryStream mem = new MemoryStream())
                {
                    byte[] buffer = new byte[4096];
                    int count;
                    while ((count = reader.Read(buffer, 0, buffer.Length)) != 0)
                    {
                        mem.Write(buffer, 0, count);
                    }
                    return mem.ToArray();
                }
            }
        }
        public string ComputeSha256(byte[] data)
        {
            StringBuilder hashstring = new StringBuilder();
            SHA256Managed hasher = new SHA256Managed();
            byte[] hash = hasher.ComputeHash(data);
            foreach (byte b in hash)
            {
                hashstring.Append(string.Format("{0:x2}", b));
            }
            return hashstring.ToString();
        }

        public void CreateEdkrepoGlobalDataDirectory()
        {
            string EdkrepoCfgDir = Path.Combine(WindowsHelpers.GetAllUsersAppDataPath(), InstallerStrings.EdkrepoGlobalDirectoryName);
            if (!Directory.Exists(EdkrepoCfgDir))
            {
                InstallLogger.Log("Creating edkrepo global data directory...");
                DirectorySecurity security = new DirectorySecurity();
                security.AddAccessRule(new FileSystemAccessRule(
                    new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                    FileSystemRights.FullControl,
                    InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                    PropagationFlags.None,
                    AccessControlType.Allow
                    ));
                Directory.CreateDirectory(EdkrepoCfgDir, security);
            }
            else
            {
                //Use the users account instead
                DirectorySecurity security = Directory.GetAccessControl(EdkrepoCfgDir);
                security.RemoveAccessRuleAll(new FileSystemAccessRule(
                    new SecurityIdentifier(WellKnownSidType.WorldSid, null),
                    FileSystemRights.FullControl,
                    AccessControlType.Allow
                    ));
                security.AddAccessRule(new FileSystemAccessRule(
                    new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                    FileSystemRights.FullControl,
                    InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                    PropagationFlags.None,
                    AccessControlType.Allow
                    ));
                Directory.SetAccessControl(EdkrepoCfgDir, security);
            }
        }

        public IEnumerable<string> GetPreviousEdkrepoCfgFileHashes()
        {
            string line, tmp_line, section;
            char[] section_chars = new char[] { '[', ']' };
            string ShaDataCfg = Path.Combine(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()), "sha_data.cfg");
            List<string> ShaValues = new List<string>();
            StreamReader ShaCfgFile = new StreamReader(ShaDataCfg);

            bool add_data = false;
            while((line = ShaCfgFile.ReadLine()) != null)
            {
                tmp_line = line.Trim();
                if(String.IsNullOrEmpty(tmp_line))
                {
                    continue;
                }
                if(tmp_line.StartsWith("[") && tmp_line.EndsWith("]"))
                {
                    add_data = false;
                    section = tmp_line.Trim(section_chars);
                    if(section == "previous_cfg_sha256")
                    {
                        add_data = true;
                    }
                    continue;
                }
                if(add_data)
                {
                    ShaValues.Add(tmp_line);
                }
            }

            return ShaValues;
        }

        public bool IsWindowsDirectoryInPath()
        {
            RegistryKey Hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey EnvironmentRegistryKey = Hklm.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Session Manager\Environment");
            if(!EnvironmentRegistryKey.GetValueNames().Contains("Path"))
            {
                return false;
            }
            string PathVariable = EnvironmentRegistryKey.GetValue("Path") as string;
            if (PathVariable != null)
            {
                List<string> Paths = new List<string>(PathVariable.Split(';'));
                string WinDir = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
                foreach (string path in Paths)
                {
                    string FullPath = string.Empty;
                    try
                    {
                        FullPath = Environment.ExpandEnvironmentVariables(Path.Combine(path.Replace("\"", "")));
                    }
                    catch (ArgumentException)
                    {
                        //If there are invalid characters in the user's path string,
                        //then ignore that path string and try the next one
                        continue;
                    }
                    if (string.Compare(FullPath, WinDir, StringComparison.OrdinalIgnoreCase) == 0)
                    {
                        return true;
                    }
                }
            }
            return false;
        }

        public void CheckWindowsDirectoryInPath()
        {
            if (!IsWindowsDirectoryInPath())
            {
                RegistryKey Hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
                RegistryKey EnvironmentRegistryKey = Hklm.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", RegistryKeyPermissionCheck.ReadWriteSubTree);
                string PathVariable = string.Empty;
                if (EnvironmentRegistryKey.GetValueNames().Contains("Path"))
                {
                    PathVariable = EnvironmentRegistryKey.GetValue("Path") as string;
                    if (PathVariable == null)
                    {
                        PathVariable = string.Empty;
                    }
                }
                string WinDir = Environment.GetFolderPath(Environment.SpecialFolder.Windows);

                List<string> Paths = new List<string>(PathVariable.Split(';'));
                Paths.Add(WinDir);
                PathVariable = string.Join(";", Paths.Where(p => !string.IsNullOrWhiteSpace(p.Replace("\"", ""))));

                EnvironmentRegistryKey.SetValue("Path", PathVariable);
                WindowsHelpers.SendEnvironmentVariableChangedMessage();
                InstallLogger.Log("WARNING: The Windows directory is not in %PATH%, it has been added.");
            }
            else
            {
                InstallLogger.Log("Windows directory is in %PATH%.");
            }
        }

        public void CreatePythonLaunchers(string GitPath, List<PythonVersion> PythonVersions, PythonVersion EdkRepoPythonVersion)
        {
            bool HasPy2 = false;
            bool HasPy3 = false;
            foreach (PythonVersion PyVer in PythonVersions)
            {
                if (PyVer.Major == 2)
                {
                    HasPy2 = true;
                }
                if (PyVer.Major == 3)
                {
                    HasPy3 = true;
                }
            }
            string GitBashBinPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(GitPath)), "usr", "bin");
            if (Directory.Exists(GitBashBinPath))
            {
                InstallLogger.Log("Creating python launcher in Git Bash...");
                string PythonScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoPythonLauncherScript);
                if (File.Exists(PythonScriptPath))
                {
                    File.Delete(PythonScriptPath);
                }
                using (BinaryWriter writer = new BinaryWriter(File.Open(PythonScriptPath, FileMode.Create)))
                {
                    string sanitized = EdkrepoPythonLauncher.Replace("\r\n", "\n");
                    writer.Write(Encoding.UTF8.GetBytes(sanitized));
                }
                if (HasPy3)
                {
                    InstallLogger.Log("Creating python3 launcher in Git Bash...");
                    string Python3ScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoPython3LauncherScript);
                    if (File.Exists(Python3ScriptPath))
                    {
                        File.Delete(Python3ScriptPath);
                    }
                    using (BinaryWriter writer = new BinaryWriter(File.Open(Python3ScriptPath, FileMode.Create)))
                    {
                        string EdkRepoPython3LauncherWithVersion = string.Format(EdkrepoPython3Launcher, EdkRepoPythonVersion.Major, EdkRepoPythonVersion.Minor);
                        string sanitized = EdkRepoPython3LauncherWithVersion.Replace("\r\n", "\n");
                        writer.Write(Encoding.UTF8.GetBytes(sanitized));
                    }
                }
                if (HasPy2)
                {
                    InstallLogger.Log("Creating python2 launcher in Git Bash...");
                    string Python2ScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoPython2LauncherScript);
                    if (File.Exists(Python2ScriptPath))
                    {
                        File.Delete(Python2ScriptPath);
                    }
                    using (BinaryWriter writer = new BinaryWriter(File.Open(Python2ScriptPath, FileMode.Create)))
                    {
                        string sanitized = EdkrepoPython2Launcher.Replace("\r\n", "\n");
                        writer.Write(Encoding.UTF8.GetBytes(sanitized));
                    }
                }
            }
        }

        private void GetSuitablePythonInterperter(SubstitutablePythons SubPy, PythonVersion PyVer, ref bool FoundSuitablePythonInterperter, ref PythonVersion SuitablePythonVersion)
        {
            bool FoundUnknownArch = false;
            //
            // There is a Python interperter installed that meets the version requirements
            // check to make sure it matches the machine architecture of the wheels we have
            //
            foreach (PythonInstance PyInstance in SubPy.PythonInstances)
            {
                if (PyInstance.Architecture == CpuArchitecture.Unknown)
                {
                    FoundSuitablePythonInterperter = true;
                    FoundUnknownArch = true;
                    if (SuitablePythonVersion < PyVer)
                    {
                        SuitablePythonVersion = PyVer;
                    }
                    break;
                }
            }
            if (!FoundUnknownArch)
            {
                bool Has64Bit = false;
                bool Has32Bit = false;
                PythonOperations.GetPythonBitness(PyVer.Major, PyVer.Minor, out Has32Bit, out Has64Bit);
                foreach (PythonInstance PyInstance in SubPy.PythonInstances)
                {
                    if (Has64Bit && PyInstance.Architecture == CpuArchitecture.X64)
                    {
                        FoundSuitablePythonInterperter = true;
                        if (SuitablePythonVersion < PyVer)
                        {
                            SuitablePythonVersion = PyVer;
                        }
                        break;
                    }
                    if (Has32Bit && PyInstance.Architecture == CpuArchitecture.IA32)
                    {
                        FoundSuitablePythonInterperter = true;
                        if (SuitablePythonVersion < PyVer)
                        {
                            SuitablePythonVersion = PyVer;
                        }
                        break;
                    }
                }
            }
        }

        public List<PythonInstance> GetPythonWheelsToInstall(EdkRepoConfig Config, List<PythonVersion> PythonVersions, Action ReportFailure)
        {
            if (VendorCustomizer.Instance != null)
            {
                if(VendorCustomizer.Instance.GetPythonWheelsToInstall != null)
                {
                    return VendorCustomizer.Instance.GetPythonWheelsToInstall(Config, PythonVersions, ReportFailure);
                }
            }
            CpuArchitecture WindowsArch = WindowsHelpers.GetWindowsOsArchitecture();
            List<PythonInstance> PythonWheelsToRun = new List<PythonInstance>();
            bool Has64Bit = false;
            bool Has32Bit = false;
            foreach (SubstitutablePythons SubPy in Config.Pythons)
            {
                //
                // Search for a Python interperter that meets the version requirements.
                //
                PythonInstance FoundPyInstance = null;
                bool FoundSuitablePythonInterperter = false;
                PythonVersion SuitablePythonVersion = new PythonVersion(-1, -1, -1);
                foreach (PythonVersion PyVer in PythonVersions)
                {
                    if (PyVer.Major == SubPy.MinVersion.Major && PyVer >= SubPy.MinVersion)
                    {
                        if (SubPy.MaxVersion != new PythonVersion(-1, -1, -1))
                        {
                            if (PyVer <= SubPy.MaxVersion)
                            {
                                GetSuitablePythonInterperter(SubPy, PyVer, ref FoundSuitablePythonInterperter, ref SuitablePythonVersion);
                            }
                        }
                        else
                        {
                            GetSuitablePythonInterperter(SubPy, PyVer, ref FoundSuitablePythonInterperter, ref SuitablePythonVersion);
                        }
                    }
                }
                if (!FoundSuitablePythonInterperter)
                {
                    if (SubPy.MaxVersion == new PythonVersion(-1, -1, -1))
                    {
                        InstallLogger.Log(string.Format("Error: Python version {0} or later is required to run EdkRepo. Please install it before continuing.", SubPy.MinVersion));
                    }
                    else
                    {
                        InstallLogger.Log(string.Format("Error: Python version in between {0} and {1} is required to run EdkRepo. Please install it before continuing.", SubPy.MinVersion, SubPy.MaxVersion));
                    }
                    ReportFailure();
                    return new List<PythonInstance>(); ;
                }
                //
                // A compatible Python interperter has been found, now decide which machine architecture to use
                //
                Has64Bit = false;
                Has32Bit = false;
                PythonOperations.GetPythonBitness(SuitablePythonVersion.Major, SuitablePythonVersion.Minor, out Has32Bit, out Has64Bit);
                // Prefer binary architecture matching native machine architecture first
                foreach (PythonInstance PyInstance in SubPy.PythonInstances)
                {
                    if (PyInstance.Architecture == WindowsArch)
                    {
                        if (PyInstance.Architecture == CpuArchitecture.X64 && Has64Bit)
                        {
                            FoundPyInstance = PyInstance;
                            break;
                        }
                        if(PyInstance.Architecture == CpuArchitecture.IA32 && Has32Bit)
                        {
                            FoundPyInstance = PyInstance;
                            break;
                        }
                    }
                }
                // If this is an X64 system, prefer IA32 binaries next
                if (FoundPyInstance == null && WindowsArch == CpuArchitecture.X64 && Has32Bit)
                {
                    foreach (PythonInstance PyInstance in SubPy.PythonInstances)
                    {
                        if (PyInstance.Architecture == CpuArchitecture.IA32)
                        {
                            FoundPyInstance = PyInstance;
                            break;
                        }
                    }
                }
                // Use generic binaries.
                if (FoundPyInstance == null)
                {
                    foreach (PythonInstance PyInstance in SubPy.PythonInstances)
                    {
                        if (PyInstance.Architecture == CpuArchitecture.Unknown)
                        {
                            FoundPyInstance = PyInstance;
                            if(Has64Bit)
                            {
                                FoundPyInstance.Architecture = CpuArchitecture.X64;
                            }
                            else if(Has32Bit)
                            {
                                FoundPyInstance.Architecture = CpuArchitecture.IA32;
                            }
                            else
                            {
                                InstallLogger.Log(string.Format("Error: Python {0} interperter architecture not found.", SuitablePythonVersion));
                                ReportFailure();
                                return new List<PythonInstance>(); ;
                            }
                            break;
                        }
                    }
                }
                if (FoundPyInstance == null)
                {
                    InstallLogger.Log("Error: EdkRepo is not compatible with your computer's processor.");
                    ReportFailure();
                    return new List<PythonInstance>(); ;
                }
                else
                {
                    FoundPyInstance.Version = SuitablePythonVersion;
                    PythonWheelsToRun.Add(FoundPyInstance);
                }
            }
            return PythonWheelsToRun;
        }

        public IEnumerable<string> GetPythonWheelsToUninstall()
        {
            if (VendorCustomizer.Instance != null)
            {
                if (VendorCustomizer.Instance.GetPythonWheelsToUninstall != null)
                {
                    //
                    // pip doesn't understand the difference between '_' and '-'
                    //
                    return VendorCustomizer.Instance.GetPythonWheelsToUninstall().Select(p => p.Replace('_', '-'));
                }
            }
            //
            // pip doesn't understand the difference between '_' and '-'
            //
            return (new string[] { InstallerStrings.EdkrepoPackageName }).Select(p => p.Replace('_', '-'));
        }

        public void PerformInstall(Action<bool, bool> ReportComplete, Action<int> ReportProgress, Action<bool> AllowCancel, Func<bool> CancelPending)
        {
            if (ReportProgress == null || ReportComplete == null || AllowCancel == null || CancelPending == null)
            {
                throw new ArgumentException();
            }
            //
            // Step 1 - Determine which versions of Python are already installed
            //
            bool FailureReported = false;
            Action ReportFailure = new Action(delegate () { FailureReported = true; });
            Environment.SetEnvironmentVariable("PYTHONHOME", null);
            Environment.SetEnvironmentVariable("PYTHONPATH", null);
            Environment.SetEnvironmentVariable("PIP_INDEX_URL", null);
            Environment.SetEnvironmentVariable("PIP_TARGET", null);
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance.WriteToInstallLog = new Action<string>(InstallLogger.Log);
            }
            EdkRepoConfig config = XmlConfigParser.ParseEdkRepoInstallerConfig();
            List<PythonVersion> PythonVersions = PythonOperations.GetInstalledPythonVersions();

            //
            // Step 2 - Determine the set of Python Wheels to be installed.
            //
            List<PythonInstance> PythonWheelsToInstall = GetPythonWheelsToInstall(config, PythonVersions, ReportFailure);
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
            // Step 3 - Determine the Git installation directory
            //
            string GitPath = PythonOperations.GetFullPath("git.exe");
            if (GitPath == null)
            {
                InstallLogger.Log("Error: git.exe was not found on the path. This likely means Git For Windows is not installed. Please install it before continuing.");
                ReportComplete(false, false);
                return;
            }
            if(WindowsHelpers.RunningInWindowsServiceOrContainer())
            {
                Environment.SetEnvironmentVariable("GIT_PYTHON_GIT_EXECUTABLE", GitPath);
            }
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(GitPath, "--version", dataCapture.DataReceivedHandler);
            process.WaitForExit();
            PythonVersion gitVersion = new PythonVersion(dataCapture.GetData().Trim());
            if (gitVersion < new PythonVersion(2, 13, 0))
            {
                InstallLogger.Log(string.Format("Git Version 2.13 or later is required. You have version {0}, please upgrade to a newer version of Git.", gitVersion));
                ReportComplete(false, false);
                return;
            }
            InstallLogger.Log(string.Format("Git Version: {0}", gitVersion));
            //
            // Run git lfs install
            //
            InstallLogger.Log("Running git lfs install");
            SilentProcess.StdoutDataCapture lfsCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess lfsProcess = SilentProcess.StartConsoleProcessSilently(GitPath, "lfs install", lfsCapture.DataReceivedHandler);
            lfsProcess.WaitForExit();
            //
            // Step 4 - Determine list of exclusive packages
            //
            List<Tuple<string, PythonVersion>> ExclusivePackages = new List<Tuple<string, PythonVersion>>();
            foreach (PythonInstance PyInstance in PythonWheelsToInstall)
            {
                foreach (PythonWheel Wheel in PyInstance.Wheels)
                {
                    if (Wheel.UninstallAllOtherCopies)
                    {
                        //
                        // pip doesn't understand the difference between '_' and '-'
                        //
                        ExclusivePackages.Add(new Tuple<string, PythonVersion>(Wheel.Package.Name.Replace('_', '-'), PyInstance.Version));
                    }
                }
            }

            //
            // Step 5 - Get current location of EdkRepo
            //
            List<Tuple<string, PythonVersion>> ExistingEdkRepoPaths;
            ExistingEdkRepoPaths = GetExistingEdkRepoPaths(PythonVersions, ReportComplete, ReportProgress, AllowCancel, CancelPending);

            //
            // Step 6 - Uninstall any existing copies of the exclusive packages
            //
            List<PythonVersion> ObsoletedPythonVersions = new List<PythonVersion>();
            UninstallExistingExclusivePackages(
                ExclusivePackages,
                PythonVersions,
                ReportComplete,
                ReportProgress,
                AllowCancel,
                CancelPending,
                ObsoletedPythonVersions
                );
            AllowCancel(false);
            if (CancelPending())
            {
                ReportComplete(true, true);
                return;
            }
            //
            // If the existing Python interperter that is hosting EdkRepo is now obsolete
            // the existing EdkRepo must be fully uninstalled since the path to EdkRepo
            // will now be different
            //
            foreach (PythonVersion Obsolete in ObsoletedPythonVersions)
            {
                if (ExistingEdkRepoPaths.Select(p => p.Item2).Contains(Obsolete))
                {
                    foreach (string ExistingEdkrepoPythonPath in ExistingEdkRepoPaths.Where(p => p.Item2 == Obsolete).Select(p => p.Item1))
                    {
                        string UninstallerPath = Path.Combine(Path.GetDirectoryName(ExistingEdkrepoPythonPath), "Lib", "site-packages");
                        UninstallerPath = Path.Combine(UninstallerPath, Path.GetFileName(WindowsHelpers.GetApplicationPath()));
                        if (File.Exists(UninstallerPath))
                        {
                            InstallLogger.Log(string.Format("Uninstalling {0}...", UninstallerPath));
                            string UninstallString = string.Format("\"{0}\" /Uninstall /Passive", UninstallerPath);
                            SilentProcess p = SilentProcess.StartConsoleProcessSilently("cmd.exe", string.Format("/S /C \"{0}\"", UninstallString));
                            p.WaitForExit();
                            Thread.Sleep(4000);
                        }
                    }
                }
            }

            //
            // Step 7 - Invoke the Pre-Wheel-Install Event
            //
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance?.PreWheelInstallEvent(PythonWheelsToInstall, ref PythonVersions,
                                                                ExclusivePackages, ReportFailure,
                                                                ref ObsoletedPythonVersions);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }

            //
            // Step 8 - Install all Wheels
            //
            string EdkrepoPythonPath = null;
            PythonVersion? EdkRepoPythonVersion = null;
            foreach (PythonInstance PyInstance in PythonWheelsToInstall)
            {
                string PythonPath;
                bool Has32Bit;
                bool Has64Bit;
                bool DeleteObsoletePackages = false;
                PythonOperations.GetPythonBitness(PyInstance.Version.Major, PyInstance.Version.Minor, out Has32Bit, out Has64Bit);
                if (Has32Bit && Has64Bit && PyInstance.Architecture == CpuArchitecture.IA32)
                {
                    PythonPath = PythonOperations.FindPython(PyInstance.Version.Major, PyInstance.Version.Minor, true);
                }
                else
                {
                    PythonPath = PythonOperations.FindPython(PyInstance.Version.Major, PyInstance.Version.Minor, false);
                }
                List<PythonPackage> InstalledPackages = PythonOperations.GetInstalledPythonPackages(PythonPath);
                foreach (PythonWheel Wheel in PyInstance.Wheels)
                {
                    //If a package is already installed, check if we have a newer version bundled in the installer
                    //If yes, the package will be upgraded, make sure obsolete packages are uninstalled first
                    PythonPackage InstalledPackage = InstalledPackages.Where(p => p.Name == Wheel.Package.Name.Replace('_', '-')).FirstOrDefault();
                    if (InstalledPackage != null && InstalledPackage.Version < Wheel.Package.Version)
                    {
                        DeleteObsoletePackages = true;
                        break;
                    }
                }
                if (DeleteObsoletePackages)
                {
                    //
                    // Delete obsolete dependencies
                    //
                    foreach (string PackageName in new string[] { "smmap2", "gitdb2" })
                    {
                        if (InstalledPackages.Where(p => p.Name == PackageName).FirstOrDefault() != null)
                        {
                            InstallLogger.Log(string.Format("Uninstalling {0}", PackageName));
                            PythonOperations.UninstallPythonPackage(PythonPath, PackageName);
                        }
                    }
                }
                foreach (PythonWheel Wheel in PyInstance.Wheels)
                {
                    //PythonPackage InstalledPackage = (from package in InstalledPackages
                    //                                  where package.Name == Wheel.Package.Name
                    //                                  select package).FirstOrDefault();
                    //If the package is already installed, check if we have a newer version bundled in the installer
                    //If so, upgrade the package
                    PythonPackage InstalledPackage = InstalledPackages.Where(p => p.Name == Wheel.Package.Name.Replace('_', '-')).FirstOrDefault();
                    if (InstalledPackage != null)
                    {
                        if (InstalledPackage.Version < Wheel.Package.Version)
                        {
                            InstallLogger.Log(string.Format("Upgrading {0} version {1} to {2}", Wheel.Package.Name, InstalledPackage.Version, Wheel.Package.Version));
                            PythonOperations.UninstallPythonPackage(PythonPath, Wheel.Package.Name);
                            PythonOperations.InstallPythonPackage(PythonPath, Wheel.Path);
                        }
                        else
                        {
                            InstallLogger.Log(string.Format("Version {0} of package {1} is already installed", InstalledPackage.Version, InstalledPackage.Name));
                            continue;
                        }
                    }
                    else
                    {
                        InstallLogger.Log(string.Format("Installing {0} version {1}", Wheel.Package.Name, Wheel.Package.Version));
                        PythonOperations.InstallPythonPackage(PythonPath, Wheel.Path);
                    }
                    if (Wheel.Package.Name == InstallerStrings.EdkrepoPackageName)
                    {
                        EdkrepoPythonPath = PythonPath;
                        EdkRepoPythonVersion = PyInstance.Version;
                    }
                }
            }

            //
            // Step 9 - Make sure the windows directory is in the PATH environment variable
            //
            CheckWindowsDirectoryInPath();

            //
            // Step 10 - Setup symlink to edkrepo and bash script to launch edkrepo from git bash
            //
            string EdkrepoSymlinkPath = null;
            if (!string.IsNullOrEmpty(EdkrepoPythonPath) && EdkRepoPythonVersion != null)
            {
                string EdkrepoScriptPath = Path.Combine(Path.GetDirectoryName(EdkrepoPythonPath), "Scripts", InstallerStrings.EdkrepoCliExecutable);
                EdkrepoSymlinkPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), InstallerStrings.EdkrepoCliExecutable);
                if (File.Exists(EdkrepoScriptPath))
                {
                    bool CreateSymlink = true;
                    if (File.Exists(EdkrepoSymlinkPath))
                    {
                        try
                        {
                            if (WindowsHelpers.IsSameFile(WindowsHelpers.GetSymlinkTarget(EdkrepoSymlinkPath), EdkrepoScriptPath))
                            {
                                CreateSymlink = false;
                            }
                        }
                        catch (NotASymlinkException) { }
                        if (CreateSymlink)
                        {
                            File.Delete(EdkrepoSymlinkPath);
                        }
                    }
                    if (CreateSymlink)
                    {
                        InstallLogger.Log("Creating Symbolic Link for edkrepo.exe...");
                        WindowsHelpers.CreateSymbolicLink(EdkrepoSymlinkPath, EdkrepoScriptPath, WindowsHelpers.SYMBOLIC_LINK_FLAG.File);
                    }
                    string GitBashBinPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(GitPath)), "usr", "bin");
                    if (Directory.Exists(GitBashBinPath))
                    {
                        InstallLogger.Log("Creating edkrepo launcher in Git Bash...");
                        string EdkrepoBashScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoBashLauncherScript);
                        if (File.Exists(EdkrepoBashScriptPath))
                        {
                            File.Delete(EdkrepoBashScriptPath);
                        }
                        using (BinaryWriter writer = new BinaryWriter(File.Open(EdkrepoBashScriptPath, FileMode.Create)))
                        {
                            string sanitized = EdkrepoBashLauncher.Replace("\r\n", "\n");
                            writer.Write(Encoding.UTF8.GetBytes(sanitized));
                        }
                        CreatePythonLaunchers(GitPath, PythonVersions, (PythonVersion) EdkRepoPythonVersion);
                    }
                }
            }

            //
            // Step 11 - Copy edkrepo config file to the edkrepo global data directory
            //
            string EdkrepoCfg = Path.Combine(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()), InstallerStrings.EdkrepoCfg);
            if (File.Exists(EdkrepoCfg))
            {
                CreateEdkrepoGlobalDataDirectory();
                string EdkrepoCfgDir = Path.Combine(WindowsHelpers.GetAllUsersAppDataPath(), InstallerStrings.EdkrepoGlobalDirectoryName);
                string EdkrepoCfgTarget = Path.Combine(EdkrepoCfgDir, InstallerStrings.EdkrepoCfg);
                //Determine if the cfg file needs to be created or upgraded
                bool ReplaceCfgFile = false;
                if (!File.Exists(EdkrepoCfgTarget))
                {
                    ReplaceCfgFile = true;
                }
                else
                {
                    string NewCfgHash = ComputeSha256(ReadFile(EdkrepoCfg));
                    string OldCfgHash = ComputeSha256(ReadFile(EdkrepoCfgTarget));
                    if (NewCfgHash != OldCfgHash)
                    {
                        if (GetPreviousEdkrepoCfgFileHashes().Contains(OldCfgHash))
                        {
                            File.Delete(EdkrepoCfgTarget);
                            ReplaceCfgFile = true;
                        }
                        else
                        {
                            string EdkrepoCfgOldTargetPrefix = Path.Combine(EdkrepoCfgDir, InstallerStrings.EdkrepoCfgOld);
                            string EdkrepoCfgOldTarget = EdkrepoCfgOldTargetPrefix;
                            int FileIncrement = 1;
                            while (File.Exists(EdkrepoCfgOldTarget))
                            {
                                EdkrepoCfgOldTarget = string.Format("{0}{1}", EdkrepoCfgOldTargetPrefix, FileIncrement);
                                FileIncrement++;
                            }
                            InstallLogger.Log("WARNING: edkrepo configuration file has been customized. It is being replaced");
                            InstallLogger.Log(string.Format("Original file has been moved to {0}", EdkrepoCfgOldTarget));
                            File.Move(EdkrepoCfgTarget, EdkrepoCfgOldTarget);
                            ReplaceCfgFile = true;
                        }
                    }
                }
                if (ReplaceCfgFile)
                {
                    InstallLogger.Log("Creating edkrepo configuration file..");
                    File.Copy(EdkrepoCfg, EdkrepoCfgTarget);
                    DirectoryInfo info = new DirectoryInfo(EdkrepoCfgTarget);
                    DirectorySecurity security = info.GetAccessControl();
                    security.AddAccessRule(new FileSystemAccessRule(
                        new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                        FileSystemRights.FullControl,
                        InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                        PropagationFlags.NoPropagateInherit,
                        AccessControlType.Allow
                        ));
                    info.SetAccessControl(security);
                }
            }

            //
            // Step 12 - Invoke the Finish Install Event
            //
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance?.FinishInstallEvent(EdkrepoPythonPath, ReportFailure);
            }
            if (FailureReported)
            {
                ReportComplete(false, false);
                return;
            }

            //
            // Step 13 - Copy win_edkrepo_prompt.sh and generate edkrepo_completions.sh
            //
            string edkrepoPromptSource = Path.Combine(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()), InstallerStrings.EdkrepoPrompt);

            if (File.Exists(edkrepoPromptSource) && !string.IsNullOrEmpty(EdkrepoSymlinkPath))
            {
                string gitBashEtcPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(GitPath)), "etc");
                string gitBashEtcProfileDPath = Path.Combine(gitBashEtcPath, "profile.d");
                if (Directory.Exists(gitBashEtcPath) && Directory.Exists(gitBashEtcProfileDPath))
                {
                    InstallLogger.Log("Installing EdkRepo command completion...");

                    //Copy win_edkrepo_prompt.sh
                    string edkrepoPromptDest = Path.Combine(gitBashEtcProfileDPath, InstallerStrings.EdkrepoPrompt);
                    if (File.Exists(edkrepoPromptDest))
                    {
                        File.Delete(edkrepoPromptDest);
                    }
                    File.Copy(edkrepoPromptSource, edkrepoPromptDest);
                    DirectoryInfo info = new DirectoryInfo(edkrepoPromptDest);
                    DirectorySecurity security = info.GetAccessControl();
                    security.AddAccessRule(new FileSystemAccessRule(
                        new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                        FileSystemRights.FullControl,
                        InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                        PropagationFlags.NoPropagateInherit,
                        AccessControlType.Allow
                        ));
                    info.SetAccessControl(security);
                    InstallLogger.Log(string.Format("Copied {0}", InstallerStrings.EdkrepoPrompt));

                    //Generate edkrepo_completions.sh
                    string edkrepoCompletionDest = Path.Combine(gitBashEtcProfileDPath, InstallerStrings.EdkrepoCompletion);
                    if (File.Exists(edkrepoCompletionDest))
                    {
                        File.Delete(edkrepoCompletionDest);
                    }
                    dataCapture = new SilentProcess.StdoutDataCapture();
                    process = SilentProcess.StartConsoleProcessSilently(
                        EdkrepoSymlinkPath,
                        string.Format(
                            "generate-command-completion-script \"{0}\"",
                            edkrepoCompletionDest),
                        dataCapture.DataReceivedHandler);
                    process.WaitForExit();
                    InstallLogger.Log(EdkrepoSymlinkPath);
                    InstallLogger.Log(edkrepoCompletionDest);
                    InstallLogger.Log(dataCapture.GetData().Trim());
                    if (process.ExitCode != 0)
                    {
                        throw new InvalidOperationException(string.Format("generate-command-completion-script failed with status {0}", process.ExitCode));
                    }
                    if (!File.Exists(edkrepoCompletionDest))
                    {
                        throw new InvalidOperationException(string.Format("generate-command-completion-script did not create {0}", InstallerStrings.EdkrepoCompletion));
                    }
                    info = new DirectoryInfo(edkrepoCompletionDest);
                    security = info.GetAccessControl();
                    security.AddAccessRule(new FileSystemAccessRule(
                        new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid, null),
                        FileSystemRights.FullControl,
                        InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                        PropagationFlags.NoPropagateInherit,
                        AccessControlType.Allow
                        ));
                    info.SetAccessControl(security);
                    InstallLogger.Log(string.Format("Generated {0}", InstallerStrings.EdkrepoCompletion));

                    //Call win_edkrepo_prompt.sh from bash.bashrc so edkrepo completions are available for "interactive non-login" bash shells
                    string bashrcPath = Path.Combine(gitBashEtcPath, "bash.bashrc");
                    if (File.Exists(bashrcPath))
                    {
                        string bashrc = Encoding.UTF8.GetString(ReadFile(bashrcPath));
                        Match match = Regex.Match(bashrc, InstallerStrings.BashrcEdkrepoPromptCallPattern);
                        if (match.Success)
                        {
                            InstallLogger.Log("EdkRepo prompt is already in bash.bashrc");
                        }
                        else
                        {
                            bashrc = string.Format("{0}{1}", bashrc, InstallerStrings.BashrcEdkRepoPromptCall);
                            using (BinaryWriter writer = new BinaryWriter(File.Open(bashrcPath, FileMode.Truncate, FileAccess.Write)))
                            {
                                string sanitized = bashrc.Replace("\r\n", "\n");
                                writer.Write(Encoding.UTF8.GetBytes(sanitized));
                            }
                            InstallLogger.Log("EdkRepo prompt added to bash.bashrc");
                        }
                    }
                    else
                    {
                        InstallLogger.Log(string.Format("{0} not found", bashrcPath));
                    }
                }
                else
                {
                    InstallLogger.Log("Git for Windows /etc/profile.d not found");
                }
            }
            else
            {
                if (string.IsNullOrEmpty(EdkrepoSymlinkPath))
                {
                    InstallLogger.Log("EdkRepo symlink not found");
                }
                if (!File.Exists(edkrepoPromptSource))
                {
                    InstallLogger.Log(string.Format("{0} not found", InstallerStrings.EdkrepoPrompt));
                }
            }

            //
            // Step 14 - Create Programs and Features uninstall links
            //
            if (!string.IsNullOrEmpty(EdkrepoPythonPath))
            {
                string UninstallerPath = Path.Combine(Path.GetDirectoryName(EdkrepoPythonPath), "Lib", "site-packages");
                if(Directory.Exists(UninstallerPath))
                {
                    string VendorPluginPath = string.Empty;
                    if (VendorCustomizer.Instance != null)
                    {
                        VendorPluginPath = Path.Combine(UninstallerPath, Path.GetFileName(VendorCustomizer.VendorPluginPath));
                    }
                    UninstallerPath = Path.Combine(UninstallerPath, Path.GetFileName(WindowsHelpers.GetApplicationPath()));
                    if(File.Exists(UninstallerPath))
                    {
                        File.Delete(UninstallerPath);
                    }
                    File.Copy(WindowsHelpers.GetApplicationPath(), UninstallerPath);
                    if (VendorCustomizer.Instance != null)
                    {
                        if (File.Exists(VendorPluginPath))
                        {
                            File.Delete(VendorPluginPath);
                        }
                        File.Copy(VendorCustomizer.VendorPluginPath, VendorPluginPath);
                    }
                    RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
                    RegistryKey winUninstallRegistryKey = hklm.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", true);
                    RegistryKey edkrepoUninstallKey = winUninstallRegistryKey.OpenSubKey(InstallerStrings.ProductCode, true);
                    if(edkrepoUninstallKey == null)
                    {
                        edkrepoUninstallKey = winUninstallRegistryKey.CreateSubKey(InstallerStrings.ProductCode);
                    }
                    edkrepoUninstallKey.SetValue("DisplayName", InstallerStrings.UninstallDisplayName);
                    edkrepoUninstallKey.SetValue("UninstallString", string.Format("\"{0}\" /Uninstall", UninstallerPath));
                    edkrepoUninstallKey.SetValue("DisplayIcon", UninstallerPath);
                    edkrepoUninstallKey.SetValue("Publisher", InstallerStrings.UninstallPublisher);
                    edkrepoUninstallKey.SetValue("DisplayVersion", InstallerStrings.UninstallDisplayVersion);
                    edkrepoUninstallKey.SetValue("NoModify", 1);
                    edkrepoUninstallKey.SetValue("NoRepair", 1);
                    edkrepoUninstallKey.SetValue("EstimatedSize", InstallerStrings.UninstallEstimatedSize);
                }
            }
            foreach (PythonVersion PyVersion in ObsoletedPythonVersions)
            {
                InstallLogger.Log(string.Format("Note: Python {0} is no longer needed by {1}. You may uninstall if it is not otherwise used.", PyVersion, InstallerStrings.ProductName));
            }
            InstallLogger.Log("Installation Successful");
            ReportComplete(true, false);
        }

        public void PerformUninstall(Action<bool, bool> ReportComplete, Action<int> ReportProgress, Action<bool> AllowCancel, Func<bool> CancelPending)
        {
            Environment.SetEnvironmentVariable("PYTHONHOME", null);
            Environment.SetEnvironmentVariable("PYTHONPATH", null);
            bool FailureReported = false;
            Action ReportFailure = new Action(delegate () { FailureReported = true; });
            if (VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance.WriteToInstallLog = new Action<string>(InstallLogger.Log);
            }
            List<PythonVersion> PythonVersions = PythonOperations.GetInstalledPythonVersions();

            //
            // Step 1 - Determine the Git installation directory
            //
            string GitPath = PythonOperations.GetFullPath("git.exe");

            //
            // Step 2 - Delete symlink to edkrepo
            //
            string EdkrepoSymlinkPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), InstallerStrings.EdkrepoCliExecutable);
            if (File.Exists(EdkrepoSymlinkPath))
            {
                bool foundSymlink = true;
                try
                {
                    WindowsHelpers.GetSymlinkTarget(EdkrepoSymlinkPath);
                }
                catch (NotASymlinkException)
                {
                    foundSymlink = false;
                }
                if(foundSymlink)
                {
                    AllowCancel(false);
                    if (CancelPending())
                    {
                        ReportComplete(true, true);
                        return;
                    }
                    InstallLogger.Log("Deleting Symbolic Link for edkrepo.exe...");
                    File.Delete(EdkrepoSymlinkPath);
                }
            }

            //
            // Step 3 - Delete scripts to launch edkrepo and Python from git bash, and edkrepo command completion scripts
            //
            if (!string.IsNullOrWhiteSpace(GitPath))
            {
                string GitBashBinPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(GitPath)), "usr", "bin");
                if (Directory.Exists(GitBashBinPath))
                {
                    string EdkrepoBashScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoBashLauncherScript);
                    if (File.Exists(EdkrepoBashScriptPath))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        InstallLogger.Log("Deleting edkrepo launcher in Git Bash...");
                        File.Delete(EdkrepoBashScriptPath);
                    }
                    string EdkrepoPythonScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoPythonLauncherScript);
                    if (File.Exists(EdkrepoPythonScriptPath))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        InstallLogger.Log("Deleting python launcher in Git Bash...");
                        File.Delete(EdkrepoPythonScriptPath);
                    }
                    string EdkrepoPython3ScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoPython3LauncherScript);
                    if (File.Exists(EdkrepoPython3ScriptPath))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        InstallLogger.Log("Deleting python3 launcher in Git Bash...");
                        File.Delete(EdkrepoPython3ScriptPath);
                    }
                    string EdkrepoPython2ScriptPath = Path.Combine(GitBashBinPath, InstallerStrings.EdkrepoPython2LauncherScript);
                    if (File.Exists(EdkrepoPython2ScriptPath))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        InstallLogger.Log("Deleting python2 launcher in Git Bash...");
                        File.Delete(EdkrepoPython2ScriptPath);
                    }
                }
                string gitBashEtcPath = Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(GitPath)), "etc");
                string gitBashEtcProfileDPath = Path.Combine(gitBashEtcPath, "profile.d");
                if (Directory.Exists(gitBashEtcPath) && Directory.Exists(gitBashEtcProfileDPath))
                {
                    string edkrepoPromptDest = Path.Combine(gitBashEtcProfileDPath, InstallerStrings.EdkrepoPrompt);
                    if (File.Exists(edkrepoPromptDest))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        InstallLogger.Log(string.Format("Deleting {0}...", InstallerStrings.EdkrepoPrompt));
                        File.Delete(edkrepoPromptDest);
                    }

                    string edkrepoCompletionDest = Path.Combine(gitBashEtcProfileDPath, InstallerStrings.EdkrepoCompletion);
                    if (File.Exists(edkrepoCompletionDest))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        InstallLogger.Log(string.Format("Deleting {0}...", InstallerStrings.EdkrepoCompletion));
                        File.Delete(edkrepoCompletionDest);
                    }

                    //Remove call win_edkrepo_prompt.sh from bash.bashrc
                    string bashrcPath = Path.Combine(gitBashEtcPath, "bash.bashrc");
                    if (File.Exists(bashrcPath))
                    {
                        string original_bashrc = Encoding.UTF8.GetString(ReadFile(bashrcPath));

                        string new_bashrc = Regex.Replace(original_bashrc, InstallerStrings.BashrcEdkrepoPromptCommentPattern, "");
                        new_bashrc = Regex.Replace(new_bashrc, InstallerStrings.BashrcEdkrepoPromptCallPattern, "");
                        if (new_bashrc == original_bashrc)
                        {
                            InstallLogger.Log("EdkRepo not found in bash.bashrc");
                        }
                        else
                        {
                            new_bashrc = new_bashrc.TrimEnd();
                            using (BinaryWriter writer = new BinaryWriter(File.Open(bashrcPath, FileMode.Truncate, FileAccess.Write)))
                            {
                                string sanitized = new_bashrc.Replace("\r\n", "\n");
                                writer.Write(Encoding.UTF8.GetBytes(sanitized));
                            }
                            InstallLogger.Log("EdkRepo prompt removed from bash.bashrc");
                        }
                    }
                    else
                    {
                        InstallLogger.Log(string.Format("{0} not found", bashrcPath));
                    }
                }
            }

            //
            // Step 4 - Uninstall any instances of edkrepo
            //
            IEnumerable<string> PackagesToUninstall = GetPythonWheelsToUninstall();
            InstallLogger.Log("Determining currently installed Python packages...");
            bool FoundEdkrepo = false;
            List<Tuple<string, PythonVersion>> PythonPaths = new List<Tuple<string, PythonVersion>>();
            foreach (PythonVersion PyVersion in PythonVersions)
            {
                bool Has32Bit;
                bool Has64Bit;
                PythonOperations.GetPythonBitness(PyVersion.Major, PyVersion.Minor, out Has32Bit, out Has64Bit);
                string PythonPath = PythonOperations.FindPython(PyVersion.Major, PyVersion.Minor, false);
                PythonPaths.Add(new Tuple<string, PythonVersion>(PythonPath, PyVersion));
                if (Has32Bit && Has64Bit)
                {
                    PythonPath = PythonOperations.FindPython(PyVersion.Major, PyVersion.Minor, true);
                    PythonPaths.Add(new Tuple<string, PythonVersion>(PythonPath, PyVersion));
                }
                if (CancelPending())
                {
                    ReportComplete(true, true);
                    return;
                }
            }
            foreach (Tuple<string, PythonVersion> PythonPath in PythonPaths)
            {
                List<PythonPackage> InstalledPackages = PythonOperations.GetInstalledPythonPackages(PythonPath.Item1);
                foreach (PythonPackage Package in InstalledPackages)
                {
                    if (PackagesToUninstall.Contains(Package.Name))
                    {
                        AllowCancel(false);
                        if (CancelPending())
                        {
                            ReportComplete(true, true);
                            return;
                        }
                        FoundEdkrepo = true;
                        InstallLogger.Log(string.Format("Uninstalling current version of {0}", Package.Name));
                        PythonOperations.UninstallPythonPackage(PythonPath.Item1, Package.Name);
                    }
                }
            }
            if (!FoundEdkrepo)
            {
                InstallLogger.Log("No existing edkrepo installations found.");
            }

            //
            // Step 5 - Invoke the Finish Uninstall Event
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
            // Step 6 - Delete Programs and Feature uninstall link
            //
            RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey winUninstallRegistryKey = hklm.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", true);
            RegistryKey edkrepoUninstallKey = winUninstallRegistryKey.OpenSubKey(InstallerStrings.ProductCode, true);
            if (edkrepoUninstallKey != null)
            {
                edkrepoUninstallKey.Close();
                winUninstallRegistryKey.DeleteSubKey(InstallerStrings.ProductCode);
            }

            InstallLogger.Log("Uninstall Complete");
            ReportComplete(true, false);
        }

        private string EdkrepoBashLauncher = @"#!/usr/bin/env bash
# @file edkrepo
#  EdkRepo Source Code Management Tool
#
# @copyright
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
if [ -t 0 -a -t 1 ]; then
  winpty edkrepo.exe ""$@""
else
  edkrepo.exe ""$@""
fi
";

        private string EdkrepoPythonLauncher = @"#!/usr/bin/env bash
# @file python
#  EdkRepo Source Code Management Tool
#
# @copyright
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
if [ -t 0 -a -t 1 ]; then
  winpty py.exe ""$@""
else
  py.exe ""$@""
fi
";

        private string EdkrepoPython3Launcher = @"#!/usr/bin/env bash
# @file python3
#  EdkRepo Source Code Management Tool
#
# @copyright
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
if [ -t 0 -a -t 1 ]; then
  winpty py.exe -{0}.{1} ""$@""
else
  py.exe -{0}.{1} ""$@""
fi
";

        private string EdkrepoPython2Launcher = @"#!/usr/bin/env bash
# @file python2
#  EdkRepo Source Code Management Tool
#
# @copyright
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
if [ -t 0 -a -t 1 ]; then
  winpty py.exe -2 ""$@""
else
  py.exe -2 ""$@""
fi
";
    }
}
