/** @file
  InstallerStrings.cs

@copyright
  Copyright 2025 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

namespace TianoCore.EdkMingwInstaller
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
                    return "EDK II Clang Mingw-w64";
                }
            }
        }

        public static string InstallationDirectory
        {
            get
            {
                if (VendorCustomizer.Instance != null)
                {
                    return VendorCustomizer.Instance.InstallationDirectory;
                }
                else
                {
                    return "edk2-clang";
                }
            }
        }

        public static string SourceDirectory
        {
            get
            {
                return "clang64";
            }
        }

        public static string BaseToolsMingwPath
        {
            get
            {
                return "BASETOOLS_MINGW_PATH";
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
                    return "EDK II Clang Mingw-w64 for Windows Installer";
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
                return new string[] { "{2570F552-A15E-4E97-98B2-BA3D274B7474}" };
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
                    return "{2570F552-A15E-4E97-98B2-BA3D274B7474}";
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
                    return "EDK II Clang Mingw-w64";
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
                    return 0x1B80FE;
                }
            }
        }
    }
}
