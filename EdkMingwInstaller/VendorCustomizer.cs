/** @file
  VendorCustomizer.cs

@copyright
  Copyright 2025 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;

namespace TianoCore.EdkMingwInstaller
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

        public string InstallationDirectory
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.InstallationDirectory;
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

        public bool SilentMode
        {
            set
            {
                gVendorCustomizerObject.SilentMode = value;
            }
        }

        public Func<string, Action, string> PreInstallEvent
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.PreInstallEvent;
                }
            }
        }

        public Action<Action> PreCopyEvent
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.PreCopyEvent;
                }
            }
        }

        public Action<Action> FinishInstallEvent
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.FinishInstallEvent;
                }
            }
        }

        public Func<string, Action, string> PreUninstallEvent
        {
            get
            {
                lock (padlock)
                {
                    return gVendorCustomizerObject.PreUninstallEvent;
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
