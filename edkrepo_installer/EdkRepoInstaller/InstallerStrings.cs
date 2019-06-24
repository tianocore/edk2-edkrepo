/** @file
  InstallerStrings.cs

@copyright
  Copyright 2016 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TianoCore.EdkRepoInstaller
{
    public class InstallerStrings
    {
        public static string ProductName
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.ProductName;
                }
                else
                {
                    return "EdkRepo";
                }
            }
        }

        public static string XmlConfigFileName
        {
            get
            {
                return "EdkRepoInstallerConfig.xml";
            }
        }

        public static string EdkrepoPackageName
        { 
            get
            {
                return "edkrepo";
            }
        }

        public static string EdkrepoCliExecutable
        {
            get
            {
                return "edkrepo.exe";
            }
        }

        public static string EdkrepoBashLauncherScript
        {
            get
            {
                return "edkrepo";
            }
        }

        public static string EdkrepoGlobalDirectoryName
        {
            get
            {
                return "edkrepo";
            }
        }

        public static string EdkrepoPythonLauncherScript
        {
            get
            {
                return "python";
            }
        }

        public static string EdkrepoPython3LauncherScript
        {
            get
            {
                return "python3";
            }
        }

        public static string EdkrepoPython2LauncherScript
        {
            get
            {
                return "python2";
            }
        }
        public static string EdkrepoCfg
        {
            get
            {
                return "edkrepo.cfg";
            }
        }

        public static string EdkrepoCfgOld
        {
            get
            {
                return "edkrepo.cfg.old";
            }
        }

        public static string InstallerName
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.InstallerName;
                }
                else
                {
                    return "EdkRepo Installer";
                }
            }
        }

        public static string UninstallQuestion
        {
            get
            {
                return "Are you sure you wish to uninstall {0}?";
            }
        }

        public static string[] KnownVendorProductCodes
        {
            get
            {
                return new string[] { "{AC6D5513-8A33-4B5F-ADA0-AACF2135B760}", "{494DB015-D682-458B-B5F1-3678F0C04D5E}" };
            }
        }
        public static string ProductCode
        {
            get
            {
                string VendorProductCode = string.Empty;
                if (VendorCustomizer.Instance != null)
                {
                    VendorProductCode = VendorCustomizer.Instance.ProductCode;
                }
                if(!string.IsNullOrWhiteSpace(VendorProductCode))
                {
                    return VendorProductCode;
                }
                else
                {
                    return "{AC6D5513-8A33-4B5F-ADA0-AACF2135B760}";
                }
            }
        }

        public static string UninstallDisplayName
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.UninstallDisplayName;
                }
                else
                {
                    return "EdkRepo";
                }
            }
        }

        public static string UninstallPublisher
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.UninstallPublisher;
                }
                else
                {
                    return "TianoCore";
                }
            }
        }

        public static string UninstallDisplayVersion
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.UninstallDisplayVersion;
                }
                else
                {
                    return System.Diagnostics.FileVersionInfo.GetVersionInfo(
                        System.Reflection.Assembly.GetExecutingAssembly().Location).FileVersion.ToString();
                }
            }
        }

        public static int UninstallEstimatedSize
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.UninstallEstimatedSize;
                }
                else
                {
                    return 0x1400;
                }
            }
        }
    }
}
