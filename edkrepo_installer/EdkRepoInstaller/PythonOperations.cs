/** @file
  PythonOperations.cs

@copyright
  Copyright 2017 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

using SimpleJSON;

namespace TianoCore.EdkRepoInstaller
{
    public static class PythonOperations
    {
        public static string GetFullPath(string FileName)
        {
            if (File.Exists (FileName))
            {
                return FileName;
            }
            List<string> Paths = new List<string>(Environment.GetEnvironmentVariable("PATH").Split(';'));
            if (!Paths.Contains(Environment.GetFolderPath(Environment.SpecialFolder.Windows)))
            {
                Paths.Add(Environment.GetFolderPath(Environment.SpecialFolder.Windows));
            }
            foreach (string path in Paths)
            {
                string FullPath = string.Empty;
                try
                {
                    FullPath = Path.Combine(path.Replace("\"", ""), FileName);
                }
                catch(ArgumentException)
                {
                    //If there are invalid characters in the user's path string,
                    //then ignore that path string and try the next one
                    continue;
                }
                if(File.Exists(FullPath))
                {
                    return FullPath;
                }
            }
            return null;
        }

        private static List<Tuple<int, int>> EnumeratePythonVersionsInRegistry()
        {
            List<Tuple<int, int>> PythonVersions = new List<Tuple<int, int>>();
            List<RegistryKey> KeysToSearch = new List<RegistryKey>();

            RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey pythonRegistryKey = hklm.OpenSubKey(@"SOFTWARE\Python\PythonCore");
            if (pythonRegistryKey != null)
            {
                KeysToSearch.Add(pythonRegistryKey);
            }
            pythonRegistryKey = hklm.OpenSubKey(@"SOFTWARE\Wow6432Node\Python\PythonCore");
            if (pythonRegistryKey != null)
            {
                KeysToSearch.Add(pythonRegistryKey);
            }
            foreach(RegistryKey key in KeysToSearch)
            {
                foreach (string subkey in key.GetSubKeyNames())
                {
                    string pattern = @"(\d+)\.(\d+)";
                    Match match = Regex.Match(subkey, pattern);
                    if (match.Success)
                    {
                        int FoundMajorVersion = Int32.Parse(match.Groups[1].Value);
                        int FoundMinorVersion = Int32.Parse(match.Groups[2].Value);
                        RegistryKey InstallPath = key.OpenSubKey(string.Format(@"{0}.{1}\InstallPath", FoundMajorVersion, FoundMinorVersion));
                        if (InstallPath == null)
                        {
                            continue;
                        }
                        if((InstallPath.GetValue(null) as string) == null)
                        {
                            continue;
                        }
                        if((InstallPath.GetValue("ExecutablePath") as string)!= null)
                        {
                            if (!File.Exists((string)InstallPath.GetValue("ExecutablePath")))
                            {
                                continue;
                            }
                        }
                        else
                        {
                            if(!File.Exists(Path.Combine((string)InstallPath.GetValue(null), "python.exe")))
                            {
                                continue;
                            }
                        }
                        bool AddNewVersionToList = true;
                        foreach(Tuple<int, int> existingVersion in PythonVersions)
                        {
                            if((existingVersion.Item1 == FoundMajorVersion) && (existingVersion.Item2 == FoundMinorVersion))
                            {
                                AddNewVersionToList = false;
                                break;
                            }
                        }
                        if(AddNewVersionToList)
                        {
                            PythonVersions.Add(new Tuple<int,int>(FoundMajorVersion, FoundMinorVersion));
                        }
                    }
                }
            }
            return PythonVersions;
        }

        private static string FindPythonInRegistry(int MajorVersion, int MinorVersion, bool Force32Bit)
        {
            CpuArchitecture WindowsArch = WindowsHelpers.GetWindowsOsArchitecture();
            RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64);
            RegistryKey pythonRegistryKey = null;
            if (!Force32Bit || WindowsArch != CpuArchitecture.X64)
            {
                pythonRegistryKey = hklm.OpenSubKey(string.Format(@"SOFTWARE\Python\PythonCore\{0}.{1}\InstallPath", MajorVersion, MinorVersion));
            }
            if (pythonRegistryKey == null)
            {
                pythonRegistryKey = hklm.OpenSubKey(string.Format(@"SOFTWARE\Wow6432Node\Python\PythonCore\{0}.{1}\InstallPath", MajorVersion, MinorVersion));
                if (pythonRegistryKey == null)
                {
                    pythonRegistryKey = hklm.OpenSubKey(string.Format(@"SOFTWARE\Wow6432Node\Python\PythonCore\{0}.{1}-32\InstallPath", MajorVersion, MinorVersion));
                    if (pythonRegistryKey == null)
                    {
                        return null;
                    }
                }
            }
            string executablePath = pythonRegistryKey.GetValue("ExecutablePath") as string;
            if (executablePath != null)
            {
                return executablePath;
            }
            string installPath = pythonRegistryKey.GetValue(null) as string;
            if (installPath == null)
            {
                return null;
            }
            executablePath = Path.Combine(installPath, "python.exe");
            if (!File.Exists(executablePath))
            {
                return null;
            }
            return executablePath;
        }

        private static string FindPythonUsingPyLauncher(string PyLauncherPath, int MajorVersion, int MinorVersion, bool Force32Bit)
        {
            string PyArgs;

            if (Force32Bit)
            {
                PyArgs = string.Format("-{0}.{1}-32 -c \"import sys; print(sys.executable)\"", MajorVersion, MinorVersion);
            }
            else
            {
                PyArgs = string.Format("-{0}.{1} -c \"import sys; print(sys.executable)\"", MajorVersion, MinorVersion);
            }
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(PyLauncherPath, PyArgs, dataCapture.DataReceivedHandler);
            process.WaitForExit();
            if (process.ExitCode == 0)
            {
                return dataCapture.GetData().Trim();
            }
            else
            {
                throw new InvalidOperationException(string.Format("Python.exe failed with status {0}", process.ExitCode));
            }
        }

        private static List<PythonVersion> EnumeratePythonVersionsUsingPyLauncher(string PyLauncherPath)
        {
            int MajorVersion;
            int MinorVersion;
            int Bugfix;
            int LatestMajorVersion;
            int LatestMinorVersion;
            List<PythonVersion> PythonVersions = new List<PythonVersion>();

            if (DetectPythonVersionUsingPyLauncher(PyLauncherPath, null, null, false, out MajorVersion, out MinorVersion, out Bugfix))
            {
                LatestMajorVersion = MajorVersion;
                //Older versions of the Python Launcher (Python 3.5 and earlier) default to the newest version of Python 2.x
                //instead of the newest Python version in general. Check if we get a 3.x version by explicitly requesting it
                if (MajorVersion == 2)
                {
                    if (DetectPythonVersionUsingPyLauncher(PyLauncherPath, 3, null, false, out MajorVersion, out MinorVersion, out Bugfix))
                    {
                        LatestMajorVersion = MajorVersion;
                    }
                }
                for (int Major = LatestMajorVersion; Major > 0; Major--)
                {
                    //Get Latest Minor version in the series
                    if (DetectPythonVersionUsingPyLauncher(PyLauncherPath, Major, null, false, out MajorVersion, out MinorVersion, out Bugfix))
                    {
                        LatestMinorVersion = MinorVersion;
                    }
                    else
                    {
                        continue;
                    }
                    for (int Minor = LatestMinorVersion; Minor >= 0; Minor--)
                    {
                        if (DetectPythonVersionUsingPyLauncher(PyLauncherPath, Major, Minor, false, out MajorVersion, out MinorVersion, out Bugfix))
                        {
                            if (!PythonVersions.Contains(new PythonVersion(MajorVersion, MinorVersion, Bugfix)))
                            {
                                PythonVersions.Add(new PythonVersion(MajorVersion, MinorVersion, Bugfix));
                            }
                        }
                    }
                }
            }
            return PythonVersions;
        }

        private static void GetPythonVersionFromPythonPath(string PythonPath, out int FoundMajorVersion, out int FoundMinorVersion, out int FoundBugfix)
        {
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(PythonPath, "--version", dataCapture.DataReceivedHandler);
            process.WaitForExit();
            if (process.ExitCode == 0)
            {
                string versionString = dataCapture.GetData();
                string pattern = @"Python (\d+)\.(\d+)\.(\d+)";
                Match match = Regex.Match(versionString, pattern);
                if (match.Success)
                {
                    FoundMajorVersion = Int32.Parse(match.Groups[1].Value);
                    FoundMinorVersion = Int32.Parse(match.Groups[2].Value);
                    FoundBugfix = Int32.Parse(match.Groups[3].Value);
                }
                else
                {
                    throw new InvalidOperationException("Python version string did not match expected format");
                }
            }
            else
            {
                throw new InvalidOperationException(string.Format("Python.exe failed with status {0}", process.ExitCode));
            }
        }

        private static bool DetectPythonVersionUsingPyLauncher(string PyLauncherPath, int? MajorVersion, int? MinorVersion, bool Force32Bit, out int FoundMajorVersion, out int FoundMinorVersion, out int FoundBugfix)
        {
            int foundMajorVersion;
            int foundMinorVersion;
            int foundBugFix;
            string PyArgs;

            //Try to find Python using the launcher
            if (MajorVersion == null && MinorVersion == null)
            {
                PyArgs = "--version";
            }
            else if (MajorVersion != null && MinorVersion == null)
            {
                PyArgs = string.Format("-{0} --version", MajorVersion.Value);
            }
            else if(MajorVersion != null && MinorVersion != null)
            {
                if(Force32Bit)
                {
                    PyArgs = string.Format("-{0}.{1}-32 --version", MajorVersion.Value, MinorVersion.Value);
                }
                else
                {
                    PyArgs = string.Format("-{0}.{1} --version", MajorVersion.Value, MinorVersion.Value);
                }
            }
            else
            {
                FoundMajorVersion = 0;
                FoundMinorVersion = 0;
                FoundBugfix = 0;
                return false;
            }
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(PyLauncherPath, PyArgs, dataCapture.DataReceivedHandler);
            process.WaitForExit();
            if (process.ExitCode == 0)
            {
                string versionString = dataCapture.GetData();
                string pattern = @"Python (\d+)\.(\d+)\.(\d+)";
                Match match = Regex.Match(versionString, pattern);
                if (match.Success)
                {
                    foundMajorVersion = Int32.Parse(match.Groups[1].Value);
                    foundMinorVersion = Int32.Parse(match.Groups[2].Value);
                    foundBugFix       = Int32.Parse(match.Groups[3].Value);
                    if(MajorVersion != null && MinorVersion != null)
                    {
                        if (MajorVersion.Value == foundMajorVersion && MinorVersion.Value == foundMinorVersion)
                        {
                            FoundMajorVersion = foundMajorVersion;
                            FoundMinorVersion = foundMinorVersion;
                            FoundBugfix = foundBugFix;
                            return true;
                        }
                        else
                        {
                            FoundMajorVersion = 0;
                            FoundMinorVersion = 0;
                            FoundBugfix = 0;
                            return false;
                        }
                    }
                    else if (MajorVersion != null && MinorVersion == null)
                    {
                        if (MajorVersion.Value == foundMajorVersion)
                        {
                            FoundMajorVersion = foundMajorVersion;
                            FoundMinorVersion = foundMinorVersion;
                            FoundBugfix = foundBugFix;
                            return true;
                        }
                        else
                        {
                            FoundMajorVersion = 0;
                            FoundMinorVersion = 0;
                            FoundBugfix = 0;
                            return false;
                        }
                    }
                    else
                    {
                        FoundMajorVersion = foundMajorVersion;
                        FoundMinorVersion = foundMinorVersion;
                        FoundBugfix = foundBugFix;
                        return true;
                    }
                }
                else
                {
                    //Regex didn't match... probably because an error message of some kind was returned
                    FoundMajorVersion = 0;
                    FoundMinorVersion = 0;
                    FoundBugfix = 0;
                    return false;
                }
            }
            //Process returned an error
            FoundMajorVersion = 0;
            FoundMinorVersion = 0;
            FoundBugfix = 0;
            return false;
        }

        public static List<PythonVersion> GetInstalledPythonVersions()
        {
            List<PythonVersion> PythonVersions = new List<PythonVersion>();
            List<Tuple<int, int>> RegistryPythonVersions = EnumeratePythonVersionsInRegistry();
            string pyLauncherPath = GetFullPath("py.exe");
            if (pyLauncherPath != null)
            {
                PythonVersions.AddRange(EnumeratePythonVersionsUsingPyLauncher(pyLauncherPath));
            }
            foreach (Tuple<int, int> RegistryPyVersion in RegistryPythonVersions)
            {
                bool FoundVersion = false;
                foreach (PythonVersion PyVersion in PythonVersions)
                {
                    if ((PyVersion.Major == RegistryPyVersion.Item1) && (PyVersion.Minor == RegistryPyVersion.Item2))
                    {
                        FoundVersion = true;
                        break;
                    }
                }
                if(!FoundVersion)
                {
                    try
                    {
                        int Major;
                        int Minor;
                        int Bugfix;
                        GetPythonVersionFromPythonPath(FindPythonInRegistry(RegistryPyVersion.Item1, RegistryPyVersion.Item2, false), out Major, out Minor, out Bugfix);
                        PythonVersions.Add(new PythonVersion(Major, Minor, Bugfix));
                    }
                    catch (Exception e)
                    {
                        InstallLogger.Log(string.Format("Unable to detect bugfix number for Python version {0}.{1}:\n{2}", RegistryPyVersion.Item1, RegistryPyVersion.Item2, e.ToString()));
                    }
                }
            }
            foreach (PythonVersion pythonVersion in PythonVersions)
            {
                InstallLogger.Log(string.Format("Found Python {0}", pythonVersion));
            }
            return PythonVersions;
        }

        public static string FindPython(int MajorVersion, int MinorVersion, bool Force32Bit)
        {
            string pyPath;
            string pyLauncherPath = GetFullPath("py.exe");
            if (pyLauncherPath != null)
            {
                try
                {
                    pyPath = FindPythonUsingPyLauncher(pyLauncherPath, MajorVersion, MinorVersion, Force32Bit);
                    if (File.Exists(pyPath))
                    {
                        return pyPath;
                    }
                }
                catch { }
            }
            pyPath = FindPythonInRegistry(MajorVersion, MinorVersion, Force32Bit);
            if (pyPath != null && File.Exists(pyPath))
            {
                return pyPath;
            }
            throw new InvalidOperationException("Python location not found");
        }

        public static void GetPythonBitness(int MajorVersion, int MinorVersion, out bool Has32Bit, out bool Has64Bit)
        {
            Has64Bit = false;
            Has32Bit = false;
            string PythonPath = FindPython(MajorVersion, MinorVersion, false);
            string PyArgs = "-c \"import platform; print(platform.architecture()[0])\"";
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(PythonPath, PyArgs, dataCapture.DataReceivedHandler);
            process.WaitForExit();
            if (process.ExitCode == 0)
            {
                string bitnessString = dataCapture.GetData();
                string pattern = @"(\d+)bit";
                Match match = Regex.Match(bitnessString, pattern);
                if (match.Success)
                {
                    if (match.Groups[1].Value == "64")
                    {
                        Has64Bit = true;
                    }
                    else if (match.Groups[1].Value == "32")
                    {
                        Has32Bit = true;
                    }
                }
            }
            if (Has64Bit && !Has32Bit)
            {
                PythonPath = null;
                try { PythonPath = FindPython(MajorVersion, MinorVersion, true); }
                catch { }
                if (PythonPath != null)
                {
                    dataCapture = new SilentProcess.StdoutDataCapture();
                    process = SilentProcess.StartConsoleProcessSilently(PythonPath, PyArgs, dataCapture.DataReceivedHandler);
                    process.WaitForExit();
                    if (process.ExitCode == 0)
                    {
                        string bitnessString = dataCapture.GetData();
                        string pattern = @"(\d+)bit";
                        Match match = Regex.Match(bitnessString, pattern);
                        if (match.Success)
                        {
                            if (match.Groups[1].Value == "64")
                            {
                                Has64Bit = true;
                            }
                            else if (match.Groups[1].Value == "32")
                            {
                                Has32Bit = true;
                            }
                        }
                    }
                }
            }
        }

        private static List<PythonPackage> ParseJsonPipList(string PipJsonList)
        {
            List<PythonPackage> PythonPackages = new List<PythonPackage>();
            JSONNode json = JSON.Parse(PipJsonList);
            if (json == null)
            {
                throw new ArgumentException("Pip list JSON failed to parse.");
            }
            if (!json.IsArray)
            {
                throw new ArgumentException(string.Format("Pip list root JSON type is not list type"));
            }
            JSONArray array = json.AsArray;
            foreach (JSONNode node in array)
            {
                if(!node.IsObject)
                {
                    InstallLogger.Log(string.Format("Found unexpected json node {0}", node.Value));
                    continue;
                }
                Dictionary<string, JSONNode> jsonObject = node.Linq.ToDictionary(x => x.Key, x => x.Value);
                if (!jsonObject.ContainsKey("name") ||
                    !jsonObject.ContainsKey("version"))
                {
                    InstallLogger.Log(string.Format("Found unexpected json node {0}", node.Value));
                    continue;
                }
                string versionString = jsonObject["version"].Value;
                PythonVersion version = new PythonVersion(0, 0, 0);
                string pattern = @"(\d+)\.(\d+)\.(\d+)";
                Match match = Regex.Match(versionString, pattern);
                if (match.Success)
                {
                    version = new PythonVersion(Int32.Parse(match.Groups[1].Value), Int32.Parse(match.Groups[2].Value), Int32.Parse(match.Groups[3].Value));
                }
                else
                {
                    pattern = @"(\d+)\.(\d+)";
                    match = Regex.Match(versionString, pattern);
                    if (match.Success)
                    {
                        version = new PythonVersion(Int32.Parse(match.Groups[1].Value), Int32.Parse(match.Groups[2].Value), 0);
                    }
                    else
                    {
                        pattern = @"(\d+)";
                        match = Regex.Match(versionString, pattern);
                        if (match.Success)
                        {
                            version = new PythonVersion(Int32.Parse(match.Groups[1].Value), 0, 0);
                        }
                    }
                }
                PythonPackage package = new PythonPackage();
                package.Name = jsonObject["name"].Value;
                package.Version = version;
                PythonPackages.Add(package);
            }

            return PythonPackages;
        }

        private static List<PythonPackage> ParseLegacyPipList (string PipLegacyList)
        {
            List<PythonPackage> PythonPackages = new List<PythonPackage>();
            IEnumerable<string> packageStrings = PipLegacyList.SplitLines();
            foreach (string packageString in packageStrings)
            {
                string pattern = @"(\S+)\s*\((\S+)\)";
                Match match = Regex.Match(packageString, pattern);
                if (match.Success)
                {
                    string packageName = match.Groups[1].Value;
                    string versionString = match.Groups[2].Value;
                    PythonVersion version = new PythonVersion(0, 0, 0);
                    pattern = @"(\d+)\.(\d+)\.(\d+)";
                    match = Regex.Match(versionString, pattern);
                    if (match.Success)
                    {
                        version = new PythonVersion(Int32.Parse(match.Groups[1].Value), Int32.Parse(match.Groups[2].Value), Int32.Parse(match.Groups[3].Value));
                    }
                    else
                    {
                        pattern = @"(\d+)\.(\d+)";
                        match = Regex.Match(versionString, pattern);
                        if (match.Success)
                        {
                            version = new PythonVersion(Int32.Parse(match.Groups[1].Value), Int32.Parse(match.Groups[2].Value), 0);
                        }
                        else
                        {
                            pattern = @"(\d+)";
                            match = Regex.Match(versionString, pattern);
                            if (match.Success)
                            {
                                version = new PythonVersion(Int32.Parse(match.Groups[1].Value), 0, 0);
                            }
                        }
                    }
                    PythonPackage package = new PythonPackage();
                    package.Name = packageName;
                    package.Version = version;
                    PythonPackages.Add(package);
                }
            }
            return PythonPackages;
        }

        private static string SanitizePipOutput(string PipOutput)
        {
            StringBuilder Sanitized = new StringBuilder();
            IEnumerable<string> PipLines = PipOutput.SplitLines();
            foreach(string line in PipLines)
            {
                if(line.StartsWith("DEPRECATION:"))
                {
                    continue;
                }
                if (string.IsNullOrWhiteSpace(line))
                {
                    continue;
                }
                Sanitized.Append(line.Trim());
                Sanitized.Append("\r\n");
            }
            return Sanitized.ToString().Trim();
        }

        public static List<PythonPackage> GetInstalledPythonPackages(string PythonPath)
        {
            List<PythonPackage> PythonPackages = new List<PythonPackage>();
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(PythonPath, "-m pip list --format=\"json\" --no-index", dataCapture.DataReceivedHandler);
            process.WaitForExit();
            bool TryLegacy = true;
            if (process.ExitCode == 0)
            {
                try
                {
                    PythonPackages = ParseJsonPipList(SanitizePipOutput(dataCapture.GetData()));
                    TryLegacy = false;
                }
                catch(Exception e)
                {
                    InstallLogger.Log("Error occurred while trying to parse pip JSON:");
                    InstallLogger.Log(e.ToString());
                    InstallLogger.Log("Falling back to legacy mode");
                }
            }
            if(TryLegacy)
            {
                //
                // Older versions of pip don't support the --format flag, parse the legacy format
                //
                dataCapture = new SilentProcess.StdoutDataCapture();
                process = SilentProcess.StartConsoleProcessSilently(PythonPath, "-m pip list --no-index", dataCapture.DataReceivedHandler);
                process.WaitForExit();
                if (process.ExitCode == 0)
                {
                    PythonPackages = ParseLegacyPipList(SanitizePipOutput(dataCapture.GetData()));
                }
            }
            return PythonPackages;
        }

        public static void UninstallPythonPackage(string PythonPath, string PackageName)
        {
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(
                PythonPath,
                string.Format("-m pip uninstall -y {0}", PackageName),
                dataCapture.DataReceivedHandler
                );
            process.WaitForExit();
            if (process.ExitCode != 0)
            {
                InstallLogger.Log(dataCapture.GetData());
                throw new PythonPackageUninstallException(string.Format("Uninstall of package {0} failed", PackageName));
            }
        }

        public static void InstallPythonPackage(string PythonPath, string PackagePath)
        {
            string packagePath = PackagePath;
            if (!File.Exists(packagePath))
            {
                packagePath = Path.Combine(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()), packagePath);
                if (!File.Exists(packagePath))
                {
                    throw new InvalidOperationException(string.Format("Python Package {0} not found", PackagePath));
                }
            }
            SilentProcess.StdoutDataCapture dataCapture = new SilentProcess.StdoutDataCapture();
            SilentProcess process = SilentProcess.StartConsoleProcessSilently(
                PythonPath,
                string.Format("-m pip install --no-index {0}", packagePath),
                dataCapture.DataReceivedHandler
                );
            process.WaitForExit();
            if (process.ExitCode != 0)
            {
                InstallLogger.Log(dataCapture.GetData());
                throw new PythonPackageInstallException(string.Format("Install of package {0} failed", PackagePath));
            }
        }

        public static IEnumerable<string> SplitLines(this string str)
        {
            using(StringReader reader = new StringReader(str))
            {
                string line = string.Empty;
                while(line != null)
                {
                    line = reader.ReadLine();
                    if(!string.IsNullOrEmpty(line))
                    {
                        yield return line.Trim();
                    }
                }
            }
        }
    }

    public class PythonPackageUninstallException : Exception
    {
        public PythonPackageUninstallException()
        {
        }

        public PythonPackageUninstallException(string message)
            : base(message)
        {
        }

        public PythonPackageUninstallException(string message, Exception inner)
            : base(message, inner)
        {
        }
    }

    public class PythonPackageInstallException : Exception
    {
        public PythonPackageInstallException()
        {
        }

        public PythonPackageInstallException(string message)
            : base(message)
        {
        }

        public PythonPackageInstallException(string message, Exception inner)
            : base(message, inner)
        {
        }
    }
}
