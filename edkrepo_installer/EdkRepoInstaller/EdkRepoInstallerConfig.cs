/** @file
  EdkRepoInstallerConfig.cs

@copyright
  Copyright 2017 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace TianoCore.EdkRepoInstaller
{
    public class EdkRepoConfig
    {
        public IEnumerable<SubstitutablePythons> Pythons { get; set; }

        public IEnumerable<PythonWheel> GetWheels (PythonVersion PyVersion, CpuArchitecture CpuArch)
        {
            foreach (SubstitutablePythons SubPyInstaller in Pythons)
            {
                foreach (PythonInstance PyInstaller in SubPyInstaller.PythonInstances)
                {
                    if((PyInstaller.Version == PyVersion) && (PyInstaller.Architecture == CpuArch))
                    {
                        return PyInstaller.Wheels;
                    }
                }
            }
            throw new ArgumentException("Python Version not found");
        }
    }

    public struct PythonVersion
    {
        public int Major;
        public int Minor;
        public int Bugfix;

        public PythonVersion(int major, int minor, int bugfix)
        {
            Major = major;
            Minor = minor;
            Bugfix = bugfix;
        }

        public PythonVersion(PythonVersion PyVersion)
        {
            Major = PyVersion.Major;
            Minor = PyVersion.Minor;
            Bugfix = PyVersion.Bugfix;
        }

        public PythonVersion(string VersionString)
        {
            string pattern = @"(\d+)\.(\d+)\.(\d+)";
            Match match = Regex.Match(VersionString, pattern);
            if (match.Success)
            {
                Major = Int32.Parse(match.Groups[1].Value);
                Minor = Int32.Parse(match.Groups[2].Value);
                Bugfix = Int32.Parse(match.Groups[3].Value);
            }
            else
            {
                throw new ArgumentException("String is not in Python version number format");
            }
        }

        public PythonVersion(dynamic PyVersion)
        {
            Major = PyVersion.Major;
            Minor = PyVersion.Minor;
            Bugfix = PyVersion.Bugfix;
        }

        public bool Equals(PythonVersion other)
        {
            return Equals(other, this);
        }
        public override bool Equals(object obj)
        {
            if (obj is PythonVersion)
            {
                PythonVersion ver = (PythonVersion)obj;
                return (ver.Major == this.Major) && (ver.Minor == this.Minor) && (ver.Bugfix == this.Bugfix);
            }
            else
            {
                return false;
            }
        }

        public override int GetHashCode()
        {
            return (Major + Minor + Bugfix).GetHashCode();
        }

        public override string ToString()
        {
            return string.Format("{0}.{1}.{2}", Major, Minor, Bugfix);
        }

        public static bool operator ==(PythonVersion Ver1, PythonVersion Ver2)
        {
            return Ver1.Equals(Ver2);
        }

        public static bool operator !=(PythonVersion Ver1, PythonVersion Ver2)
        {
            return !Ver1.Equals(Ver2);
        }

        public static bool operator <(PythonVersion Ver1, PythonVersion Ver2)
        {
            if (Ver1.Major < Ver2.Major)
            {
                return true;
            }
            if (Ver1.Major == Ver2.Major)
            {
                if(Ver1.Minor < Ver2.Minor)
                {
                    return true;
                }
                if (Ver1.Minor == Ver2.Minor)
                {
                    if (Ver1.Bugfix < Ver2.Bugfix)
                    {
                        return true;
                    }
                }
            }
            return false;
        }

        public static bool operator >(PythonVersion Ver1, PythonVersion Ver2)
        {
            return (!(Ver1 < Ver2)) && (Ver1 != Ver2);
        }

        public static bool operator <=(PythonVersion Ver1, PythonVersion Ver2)
        {
            return (Ver1 == Ver2) || (Ver1 < Ver2);
        }

        public static bool operator >= (PythonVersion Ver1, PythonVersion Ver2)
        {
            return (Ver1 == Ver2) || (Ver1 > Ver2);
        }
    }

    public class SubstitutablePythons
    {
        public IEnumerable<PythonInstance> PythonInstances { get; set; }

        public PythonVersion MinVersion { get; set; }

        public PythonVersion MaxVersion { get; set; }
    }

    public class PythonInstance
    {
        public PythonVersion Version { get; set; }
        public CpuArchitecture Architecture { get; set; }
        public IEnumerable<PythonWheel> Wheels { get; set; }

        public PythonInstance() { }

        public PythonInstance(dynamic PyInstance)
        {
            Version = new PythonVersion(PyInstance.Version);
            Architecture = (CpuArchitecture)Enum.Parse(typeof(CpuArchitecture), PyInstance.Architecture.ToString(), true);
            List<PythonWheel> newWheels = new List<PythonWheel>();
            dynamic wheels = PyInstance.Wheels;
            foreach(dynamic wheel in wheels)
            {
                newWheels.Add(new PythonWheel(wheel));
            }
            Wheels = newWheels;
        }

        public override string ToString()
        {
            return string.Format("{0} {1} {2}", Version, Architecture);
        }
    }

    public class PythonWheel
    {
        public PythonWheel()
        {
            Package = new PythonPackage();
            Path = string.Empty;
            UninstallAllOtherCopies = false;
        }
        public PythonWheel(dynamic PyWheel)
        {
            Package = new PythonPackage(PyWheel.Package);
            Path = PyWheel.Path;
            UninstallAllOtherCopies = PyWheel.UninstallAllOtherCopies;
        }
        public PythonPackage Package { get; set; }
        public string Path { get; set; }
        public bool UninstallAllOtherCopies { get; set; }

        public override string ToString()
        {
            return Package.ToString();
        }
    }

    public class PythonPackage
    {
        public PythonVersion Version { get; set; }
        public string Name { get; set; }

        public PythonPackage()
        {
            Name = string.Empty;
        }
        public PythonPackage(dynamic PyPackage)
        {
            Version = new PythonVersion(PyPackage.Version);
            Name = PyPackage.Name;
        }

        public override string ToString()
        {
            return string.Format("{0}({1})", Name, Version);
        }
    }
}
