/** @file
  VendorCustomizer.cs

@copyright
  Copyright 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;

namespace TianoCore.EdkRepoInstaller
{
    public class VendorCustomizer
    {
        private dynamic gVendorCustomizerObject = null;
        private static VendorCustomizer instance = null;
        private static readonly object padlock = new object();

        private VendorCustomizer(object VendorCustomizerObj)
        {
            gVendorCustomizerObject = VendorCustomizerObj;
        }
  
        public static VendorCustomizer Instance
        {
            get
            {
                lock(padlock)
                {
                    return instance;
                }
            }
        }

        public static object VendorCustomizerObject
        {
            set
            {
                lock(padlock)
                {
                    if (value != null)
                    {
                        instance = new VendorCustomizer(value);
                    }
                    else
                    {
                        instance = null;
                    }
                }
            }
        }

        public static string VendorPluginPath { get; set; }

        public Viewbox VendorLogo
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.VendorLogo;
                }
            }
        }

        public Viewbox WelcomeSplash
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.WelcomeSplash;
                }
            }
        }

        public string ProductName
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.ProductName;
                }
            }
        }

        public string InstallerName
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.InstallerName;
                }
            }
        }

        public string ProductCode
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.ProductCode;
                }
            }
        }

        public string UninstallDisplayName
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.UninstallDisplayName;
                }
            }
        }

        public string UninstallPublisher
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.UninstallPublisher;
                }
            }
        }

        public string UninstallDisplayVersion
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.UninstallDisplayVersion;
                }
            }
        }

        public int UninstallEstimatedSize
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.UninstallEstimatedSize;
                }
            }
        }

        public Action<string> WriteToInstallLog
        {
            set
            {
                lock (padlock)
                {
                    gVendorCustomizerObject.WriteToInstallLog = value;
                }
            }
        }

        public Func<EdkRepoConfig, List<PythonVersion>, Action, List<PythonInstance>> GetPythonWheelsToInstall
        {
            get
            {
                lock (padlock)
                {
                    Func<object, IEnumerable<object>, Action, IEnumerable<object>> function;
                    lock (padlock)
                    {
                        function = gVendorCustomizerObject.GetPythonWheelsToInstall;
                    }
                    if (function == null)
                    {
                        return null;
                    }
                    else
                    {
                        return delegate (EdkRepoConfig Config, List<PythonVersion> PythonVersions, Action ReportFailure)
                        {

                            Func<object, IEnumerable<object>, Action, IEnumerable<object>> getPythonWheelsToInstall;
                            lock (padlock)
                            {
                                getPythonWheelsToInstall = gVendorCustomizerObject.GetPythonWheelsToInstall;
                            }

                            IEnumerable<object> PythonWheelsToRunObject = getPythonWheelsToInstall(Config, PythonVersions.Cast<object>(), ReportFailure);
                            List<PythonInstance> PythonWheelsToRun = new List<PythonInstance>();
                            foreach (object PythonInstanceObject in PythonWheelsToRunObject)
                            {
                                PythonWheelsToRun.Add(new PythonInstance(PythonInstanceObject));
                            }
                            return PythonWheelsToRun;
                        };
                    }
                }
            }
        }
        public delegate void PreWheelInstallEventDelegate(List<PythonInstance> PythonWheelsToInstall,
                                                          ref List<PythonVersion> PythonVersions,
                                                          List<Tuple<string, PythonVersion>> ExclusivePackages,
                                                          Action ReportFailure,
                                                          ref List<PythonVersion> ObsoletedPythonVersions);

        public PreWheelInstallEventDelegate PreWheelInstallEvent
        {
            get
            {
                Func<IEnumerable<object>, IEnumerable<object>, IEnumerable<object>, Action, IEnumerable<object>, object> function;
                lock (padlock)
                {
                    function = gVendorCustomizerObject.PreWheelInstallEvent;
                }
                if (function == null)
                {
                    return null;
                }
                else
                {
                    return delegate (List<PythonInstance> PythonWheelsToInstall, ref List<PythonVersion> PythonVersions,
                                 List<Tuple<string, PythonVersion>> ExclusivePackages, Action ReportFailure,
                                 ref List<PythonVersion> ObsoletedPythonVersions)
                    {
                        Func<IEnumerable<object>, IEnumerable<object>, IEnumerable<object>, Action, IEnumerable<object>, object> preWheelInstallEvent;
                        lock (padlock)
                        {
                            preWheelInstallEvent = gVendorCustomizerObject.PreWheelInstallEvent;
                        }
                        dynamic ReturnData = preWheelInstallEvent(PythonWheelsToInstall, PythonVersions.Cast<object>(), ExclusivePackages, ReportFailure, ObsoletedPythonVersions.Cast<object>());
                        List<PythonVersion> NewPythonVersions = new List<PythonVersion>();
                        List<PythonVersion> NewObsoletedPythonVersions = new List<PythonVersion>();
                        foreach (object version in ReturnData.PythonVersions)
                        {
                            NewPythonVersions.Add(new PythonVersion(version));
                        }
                        foreach (object version in ReturnData.ObsoletedPythonVersions)
                        {
                            NewObsoletedPythonVersions.Add(new PythonVersion(version));
                        }
                        PythonVersions = NewPythonVersions;
                        ObsoletedPythonVersions = NewPythonVersions;
                    };
                }
            }
        }

        public Action<string, Action> FinishInstallEvent
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.FinishInstallEvent;
                }
            }
        }

        public Func<IEnumerable<string>> GetPythonWheelsToUninstall
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.GetPythonWheelsToUninstall;
                }
            }
        }

        public Action<Action> FinishUninstallEvent
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.FinishUninstallEvent;
                }
            }
        }
    }
}
