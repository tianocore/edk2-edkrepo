/** @file
  App.xaml.cs

@copyright
  Copyright 2017 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Windows;

namespace TianoCore.EdkRepoInstaller
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        private void Application_Startup(object sender, StartupEventArgs e)
        {
            bool uninstall = false;
            bool passive = false;
            foreach (string arg in Environment.GetCommandLineArgs())
            {
                if ((string.Compare(arg,"/uninstall",true) == 0) ||
                    (string.Compare(arg,"-uninstall",true) == 0) ||
                    (string.Compare(arg,"--uninstall",true) == 0))
                {
                    uninstall = true;
                }
                if ((string.Compare(arg, "/passive", true) == 0) ||
                    (string.Compare(arg, "-passive", true) == 0) ||
                    (string.Compare(arg, "--passive", true) == 0))
                {
                    passive = true;
                }
            }
            LoadVendorCustomizer(passive);
            if (uninstall)
            {
                if (passive)
                {
                    ProgressWindow progressWindow = new ProgressWindow();
                    progressWindow.UninstallMode = true;
                    progressWindow.PassiveMode = true;
                    progressWindow.Show();
                }
                else
                {
                    MessageBoxResult Confirm = MessageBox.Show(
                        string.Format(InstallerStrings.UninstallQuestion, InstallerStrings.ProductName),
                        InstallerStrings.InstallerName,
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Question
                        );
                    if (Confirm == MessageBoxResult.Yes)
                    {
                        ProgressWindow progressWindow = new ProgressWindow();
                        progressWindow.UninstallMode = true;
                        progressWindow.Show();
                    }
                    else
                    {
                        Application.Current.Shutdown(0);
                    }
                }
            }
            else if (passive)
            {
                CheckForVendorCustomizedEdkRepoAlreadyInstalled(passive);
                ProgressWindow progressWindow = new ProgressWindow();
                progressWindow.PassiveMode = true;
                progressWindow.Show();
            }
            else
            {
                CheckForVendorCustomizedEdkRepoAlreadyInstalled(passive);
                new MainWindow().Show();
            }
        }

        //
        // Note: If one creates a custom version of EdkRepo using this mechanism,
        // be sure to make a new ProductCode and add it to InstallerStrings.KnownVendorCustomizerProductCodes
        //
        private void LoadVendorCustomizer(bool Passive)
        {
            string path = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            Assembly VendorPlugin = null;
            string VendorPluginPath = string.Empty;

            foreach (string file in Directory.GetFiles(path))
            {
                if(Path.GetFileName(file).Equals("TianoCore.EdkRepoInstaller.VendorCustomizer.dll",
                                                StringComparison.OrdinalIgnoreCase))
                {
                    try
                    {
                        VendorPlugin = Assembly.LoadFile(file);
                        VendorPluginPath = file;
                    }
                    catch(Exception e)
                    {
                        VendorPlugin = null;
                        InstallLogger.Log(string.Format("Unable to load vendor customizer: {0}\r\n{1}", file, e.ToString()));
                        if (!Passive)
                        {
                            MessageBox.Show(
                                string.Format("Unable to load vendor customizer: {0}\r\n{1}", file, e.ToString()),
                                InstallerStrings.InstallerName,
                                MessageBoxButton.OK,
                                MessageBoxImage.Error
                                );
                        }
                        Application.Current.Shutdown(1);
                    }
                    break;
                }
            }
            if(VendorPlugin != null)
            {
                try
                {
                    bool ObjectCreated = false;
                    foreach (Type t in VendorPlugin.GetExportedTypes())
                    {
                        IEnumerable<object> attributes = t.GetCustomAttributes(true);
                        foreach (object attribute in attributes)
                        {
                            if (attribute.GetType().Name == "EdkRepoInstallerVendorCustomizerAttribute")
                            {
                                VendorCustomizer.VendorCustomizerObject = Activator.CreateInstance(t);
                                ObjectCreated = true;
                                if (string.IsNullOrEmpty(VendorPluginPath))
                                {
                                    throw new ArgumentException("VendorPluginPath is empty");
                                }
                                VendorCustomizer.VendorPluginPath = VendorPluginPath;
                                break;
                            }
                        }
                        if (ObjectCreated)
                        {
                            break;
                        }
                    }
                }
                catch (Exception e)
                {
                    VendorPlugin = null;
                    InstallLogger.Log(string.Format("Unable to load vendor customizer\r\n{0}", e.ToString()));
                    if (!Passive)
                    {
                        MessageBox.Show(
                            string.Format("Unable to load vendor customizer\r\n{0}", e.ToString()),
                            InstallerStrings.InstallerName,
                            MessageBoxButton.OK,
                            MessageBoxImage.Error
                            );
                    }
                    Application.Current.Shutdown(1);
                }
            }
        }

        private void CheckForVendorCustomizedEdkRepoAlreadyInstalled(bool Passive)
        {
            RegistryKey VendorUninstallKey;
            if (FoundVendorCustomizedEdkRepoAlreadyInstalled(out VendorUninstallKey))
            {
                string ProductName = InstallerStrings.ProductName;
                string DisplayName = VendorUninstallKey.GetValue("DisplayName").ToString();
                string UninstallString = string.Format("{0} /Passive", VendorUninstallKey.GetValue("UninstallString"));
                if (Passive)
                {
                    InstallLogger.Log(string.Format("{0} is a third party version of {1}. {0} is already installed.", DisplayName, ProductName));
                    InstallLogger.Log(string.Format("To install this version of {1}, {0} must be uninstalled first.", DisplayName, ProductName));
                    SilentProcess p = SilentProcess.StartConsoleProcessSilently("cmd.exe", string.Format("/c \"{0}\"", UninstallString));
                    p.WaitForExit();
                    Thread.Sleep(4000);
                }
                else
                {
                    MessageBoxResult Uninstall = MessageBox.Show(
                        string.Format("{0} is a third party version of {1}, {0} is already installed. To install this version of {1}, {0} must be uninstalled first.\r\n\r\nUninstall {0} now?", DisplayName, ProductName),
                        InstallerStrings.InstallerName,
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Exclamation,
                        MessageBoxResult.No
                        );
                    if (Uninstall == MessageBoxResult.Yes)
                    {
                        SilentProcess p = SilentProcess.StartConsoleProcessSilently("cmd.exe", string.Format("/c \"{0}\"", UninstallString));
                        p.WaitForExit();
                        Thread.Sleep(1000);
                    }
                    else
                    {
                        Application.Current.Shutdown(0);
                    }
                }
            }
        }

        private bool FoundVendorCustomizedEdkRepoAlreadyInstalled(out RegistryKey FoundVendorUninstallKey)
        {
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
            foreach (string VendorCustomizerProductCode in InstallerStrings.KnownVendorProductCodes)
            {
                if(!string.IsNullOrWhiteSpace(ProductCode) && string.Compare(VendorCustomizerProductCode, ProductCode, true) == 0)
                {
                    continue;
                }
                RegistryKey vendorUninstallKey = winUninstallRegistryKey.OpenSubKey(VendorCustomizerProductCode, true);
                if (vendorUninstallKey != null)
                {
                    FoundVendorUninstallKey = vendorUninstallKey;
                    return true;
                }
            }
            FoundVendorUninstallKey = null;
            return false;
        }
    }
}
