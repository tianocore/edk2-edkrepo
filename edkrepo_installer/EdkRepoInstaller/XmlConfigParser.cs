/** @file
  XmlConfigParser.cs

@copyright
  Copyright 2017 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml;

namespace TianoCore.EdkRepoInstaller
{
    public class XmlConfigParser
    {
        public static EdkRepoConfig ParseEdkRepoInstallerConfig()
        {
            string XmlFilePath = Path.Combine(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()), InstallerStrings.XmlConfigFileName);
            if (!File.Exists(XmlFilePath))
            {
                throw new InvalidOperationException(string.Format("Required XML file does not exist: {0}", XmlFilePath));
            }
            return ParseEdkRepoInstallerConfig(XmlFilePath);
        }
        public static EdkRepoConfig ParseEdkRepoInstallerConfig(string XmlFilePath)
        {
            XmlDocument Xml = new XmlDocument();
            Xml.Load(XmlFilePath);
            return ParseXml(Xml);
        }

        public static EdkRepoConfig ParseEdkRepoInstallerConfigFromXmlString(string Xml)
        {
            XmlDocument xml = new XmlDocument();
            xml.LoadXml(Xml);
            return ParseXml(xml);
        }

        private static EdkRepoConfig ParseXml(XmlDocument Xml)
        {
            EdkRepoConfig config = new EdkRepoConfig();
            List<SubstitutablePythons> Pythons = new List<SubstitutablePythons>();
            config.Pythons = Pythons;
            SubstitutablePythons SubPy;
            foreach (XmlNode node in Xml.DocumentElement)
            {
                switch(node.Name)
                {
                    //
                    // The use case for SubstitutablePythons is to allow a different set of
                    // Python wheels to be installed on a IA32 vs. X64 version of the Python interperter.
                    //
                    // If all wheels work universally regardless of machine architecture Then just use a <Python> tag
                    //
                    case "SubstitutablePythons":
                        List<PythonInstance> InnerPyInstances = new List<PythonInstance>();
                        if (node.Attributes["MinVersion"] == null)
                        {
                            throw new ArgumentException("Required attribute \"MinVersion\" is missing from SubstitutablePythons element in configuration XML");
                        }
                        foreach(XmlNode innerNode in node)
                        {
                            if (innerNode.Name == "Python")
                            {
                                InnerPyInstances.Add(ParsePythonNode(innerNode));
                            }
                        }
                        SubPy = new SubstitutablePythons();
                        SubPy.PythonInstances = InnerPyInstances;
                        SubPy.MinVersion = new PythonVersion(node.Attributes["MinVersion"].Value);
                        if (node.Attributes["MaxVersion"] != null)
                        {
                            SubPy.MaxVersion = new PythonVersion(node.Attributes["MaxVersion"].Value);
                        }
                        else
                        {
                            SubPy.MaxVersion = new PythonVersion(-1, -1, -1);
                        }
                        Pythons.Add(SubPy);
                        break;
                    case "Python":
                        if (node.Attributes["MinVersion"] == null)
                        {
                            throw new ArgumentException("Required attribute \"MinVersion\" is missing from Python element in configuration XML");
                        }
                        PythonInstance PyInstaller = ParsePythonNode(node);
                        SubPy = new SubstitutablePythons();
                        SubPy.PythonInstances = new PythonInstance[] { PyInstaller };
                        SubPy.MinVersion = new PythonVersion(node.Attributes["MinVersion"].Value);
                        if (node.Attributes["MaxVersion"] != null)
                        {
                            SubPy.MaxVersion = new PythonVersion(node.Attributes["MaxVersion"].Value);
                        }
                        else
                        {
                            SubPy.MaxVersion = new PythonVersion(-1, -1, -1);
                        }
                        Pythons.Add(SubPy);
                        break;
                }
            }
            ValidateConfig(config);
            return config;
        }

        private static PythonInstance ParsePythonNode(XmlNode Node)
        {
            PythonInstance PyInstance = new PythonInstance();
            if (Node.Attributes["Architecture"] != null)
            {
                PyInstance.Architecture = (CpuArchitecture)Enum.Parse(typeof(CpuArchitecture),
                                                                        Node.Attributes["Architecture"].Value, true);
                if(PyInstance.Architecture == CpuArchitecture.Unknown)
                {
                    throw new ArgumentException("Python architecture must not be unknown");
                }
            }
            else
            {
                PyInstance.Architecture = CpuArchitecture.Unknown;
            }
            List<PythonWheel> Wheels = new List<PythonWheel>();
            PyInstance.Wheels = Wheels;
            foreach (XmlNode node in Node)
            {
                switch(node.Name)
                {
                    case "Wheel":
                        PythonWheel wheel = new PythonWheel();
                        if (node.Attributes["Name"] == null)
                        {
                            throw new ArgumentException("Required attribute \"Name\" is missing from Wheel element in configuration XML");
                        }
                        if (node.Attributes["Path"] == null)
                        {
                            throw new ArgumentException("Required attribute \"Path\" is missing from Wheel element in configuration XML");
                        }
                        if (node.Attributes["Version"] == null)
                        {
                            throw new ArgumentException("Required attribute \"Version\" is missing from Wheel element in configuration XML");
                        }
                        wheel.Package.Name = node.Attributes["Name"].Value;
                        wheel.Path = node.Attributes["Path"].Value;
                        wheel.Package.Version = new PythonVersion(node.Attributes["Version"].Value);
                        if (node.Attributes["UninstallAllOtherCopies"] != null)
                        {
                            wheel.UninstallAllOtherCopies = StringToBool(node.Attributes["UninstallAllOtherCopies"].Value);
                        }
                        else
                        {
                            wheel.UninstallAllOtherCopies = false;
                        }
                        Wheels.Add(wheel);
                        break;
                }
            }
            return PyInstance;
        }

        private static void ValidateConfig(EdkRepoConfig Config)
        {
            //1. SubstitutablePythons should have a different machine architecture
            bool FoundFirstPython;
            List<CpuArchitecture> CpuArchitectureList = new List<CpuArchitecture>();
            foreach (SubstitutablePythons SubPyInstaller in Config.Pythons)
            {
                FoundFirstPython = false;
                CpuArchitectureList.Clear();
                foreach (PythonInstance PyInstance in SubPyInstaller.PythonInstances)
                {
                    if (!FoundFirstPython)
                    {
                        CpuArchitectureList.Add(PyInstance.Architecture);
                        FoundFirstPython = true;
                    }
                    else
                    {
                        if(CpuArchitectureList.Contains(PyInstance.Architecture))
                        {
                            throw new ArgumentException("Substitutable Python instances must all have different machine architectures for each instance");
                        }
                        CpuArchitectureList.Add(PyInstance.Architecture);
                    }
                }
            }

            //2. Only one entry for a min/max version of Python
            Tuple<PythonVersion, PythonVersion> PyVersionPair;
            List<Tuple<PythonVersion, PythonVersion>> PyVersionList = new List<Tuple<PythonVersion, PythonVersion>>();
            foreach (SubstitutablePythons SubPython in Config.Pythons)
            {
                PyVersionPair = new Tuple<PythonVersion, PythonVersion>(SubPython.MinVersion, SubPython.MaxVersion);
                foreach(Tuple<PythonVersion, PythonVersion> Version in PyVersionList)
                {
                    if (Version.Item1 == PyVersionPair.Item1 && Version.Item2 == PyVersionPair.Item2)
                    {
                        throw new ArgumentException("There must be only one Python or SubstitutablePythons element for each min/max version of Python");
                    }
                }
                PyVersionList.Add(PyVersionPair);
            }
            //3. If a wheel has UninstallAllOtherCopies == true, then there should be no other copies of that wheel under different Python versions
            List<string> ExclusiveWheels = new List<string>();
            List<string> CandidateExclusiveWheels = new List<string>();
            foreach (SubstitutablePythons SubPython in Config.Pythons)
            {
                CandidateExclusiveWheels.Clear();
                foreach(PythonInstance PyInstance in SubPython.PythonInstances)
                {
                    foreach(PythonWheel Wheel in PyInstance.Wheels)
                    {
                        if (Wheel.UninstallAllOtherCopies)
                        {
                            if (!CandidateExclusiveWheels.Contains(Wheel.Package.Name))
                            {
                                CandidateExclusiveWheels.Add(Wheel.Package.Name);
                            }
                        }
                    }
                }
                foreach(string WheelName in CandidateExclusiveWheels)
                {
                    if (!ExclusiveWheels.Contains(WheelName))
                    {
                        ExclusiveWheels.Add(WheelName);
                    }
                }
            }
            foreach (string WheelName in ExclusiveWheels)
            {
                bool FoundWheel = false;
                foreach (SubstitutablePythons SubPython in Config.Pythons)
                {
                    bool ContinueSearch = true;
                    foreach (PythonInstance PyInstance in SubPython.PythonInstances)
                    {
                        foreach (PythonWheel Wheel in PyInstance.Wheels)
                        {
                            if (Wheel.Package.Name == WheelName)
                            {
                                if (FoundWheel)
                                {
                                    throw new ArgumentException(string.Format("More than one version of Python contains the wheel {0} when only one copy of this wheel should be installed on the system", WheelName));
                                }
                                else
                                {
                                    FoundWheel = true;
                                }
                                ContinueSearch = false;
                                break;
                            }
                        }
                        if(!ContinueSearch)
                        {
                            break;
                        }
                    }
                }
            }
        }

        public static bool StringToBool(string teststr)
        {

            if (string.Compare(teststr, "true", true) == 0)
            {
                return true;
            }
            else if (string.Compare(teststr, "false", true) == 0)
            {
                return false;
            }
            else
            {
                int value;
                if (int.TryParse(teststr, out value))
                {
                    return value != 0;
                }
                return Convert.ToBoolean(teststr);
            }
        }
    }
}
