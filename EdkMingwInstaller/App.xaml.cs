/** @file
  App.xaml.cs

@copyright
  Copyright 2025 - 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Threading;
using TianoCore.EdkClang;

namespace TianoCore.EdkMingwInstaller
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool AttachConsole(uint dwProcessId);

        private void Application_Startup(object sender, StartupEventArgs e)
        {
            DispatcherUnhandledException += App_DispatcherUnhandledException;
            AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;

            // Prevent any dialogs shown before the first window from queuing an implicit shutdown.
            ShutdownMode = ShutdownMode.OnExplicitShutdown;

            Wpf.Ui.Appearance.ApplicationThemeManager.ApplySystemTheme();

            bool uninstall = false;
            bool passive = false;
            bool silent = false;
            bool keepOldVersions = false;
            string requestedVersion = null;
            string[] commandLine = Environment.GetCommandLineArgs();
            for (int i = 0; i < commandLine.Length; i++)
            {
                string arg = commandLine[i];
                if ((string.Compare(arg,"/uninstall",true) == 0) ||
                    (string.Compare(arg,"-uninstall",true) == 0) ||
                    (string.Compare(arg,"--uninstall",true) == 0))
                {
                    uninstall = true;
                }
                if ((string.Compare(arg, "/version", true) == 0) ||
                    (string.Compare(arg, "-version", true) == 0) ||
                    (string.Compare(arg, "--version", true) == 0))
                {
                    if (i + 1 < commandLine.Length)
                    {
                        requestedVersion = commandLine[++i];
                    }
                }
                if ((string.Compare(arg, "/passive", true) == 0) ||
                    (string.Compare(arg, "-passive", true) == 0) ||
                    (string.Compare(arg, "--passive", true) == 0))
                {
                    passive = true;
                }
                if ((string.Compare(arg, "/silent", true) == 0) ||
                    (string.Compare(arg, "-silent", true) == 0) ||
                    (string.Compare(arg, "--silent", true) == 0))
                {
                    silent = true;
                    passive = true;
                }
                if ((string.Compare(arg, "/keepoldversions", true) == 0) ||
                    (string.Compare(arg, "-keepoldversions", true) == 0) ||
                    (string.Compare(arg, "--keepoldversions", true) == 0))
                {
                    keepOldVersions = true;
                }
            }
            if(silent)
            {
                AttachConsole(0xffffffff);
                InstallLogger.SetSilentMode(true);
            }

            LoadVendorCustomizer(passive, silent);
            if (silent && VendorCustomizer.Instance != null)
            {
                VendorCustomizer.Instance.SilentMode = true;
            }
            if (uninstall)
            {
                string uninstallVersion;
                if (!ResolveUninstallVersion(requestedVersion, silent, passive, out uninstallVersion))
                {
                    return;
                }
                InstallWorker.UninstallVersion = uninstallVersion;
                if (silent)
                {
                    SilentInstallHandler silentInstallHandler = new SilentInstallHandler();
                    silentInstallHandler.PerformUninstall();
                }
                else if (passive)
                {
                    ProgressWindow progressWindow = new ProgressWindow();
                    progressWindow.UninstallMode = true;
                    progressWindow.PassiveMode = true;
                    progressWindow.Show();
                }
                else
                {
                    bool confirmed = FluentDialogs.AskYesNo(
                        InstallerStrings.InstallerName,
                        string.Format(
                            InstallerStrings.UninstallQuestion,
                            uninstallVersion == null ? InstallerStrings.ProductName : InstallerStrings.VersionDisplayName(uninstallVersion)));
                    if (confirmed)
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
            else //Install
            {
                SilentInstallHandler silentInstallHandler = null;
                if(silent)
                {
                    Console.WriteLine(InstallerStrings.InstallerName);
                    string publisher = InstallerStrings.UninstallPublisher;
                    if (publisher == "TianoCore")
                        publisher = "The TianoCore Contributors";
                    Console.WriteLine(string.Format("Copyright (c) {0}", publisher));
                    Console.WriteLine(string.Format("Please wait while we install {0}...", InstallerStrings.ProductName));
                    Console.WriteLine();
                    silentInstallHandler = new SilentInstallHandler();
                    silentInstallHandler.RemoveOlderSameMajorVersions = !keepOldVersions;
                    InstallLogger.SetLogHook(silentInstallHandler.UpdateLog);
                }
                CheckForVendorCustomizedEdkRepoAlreadyInstalled(passive);
                if (silent)
                {
                    silentInstallHandler.PerformInstall();
                }
                else if (passive)
                {
                    ProgressWindow progressWindow = new ProgressWindow();
                    progressWindow.PassiveMode = true;
                    progressWindow.RemoveOlderSameMajorVersions = !keepOldVersions;
                    progressWindow.Show();
                }
                else
                {
                    new MainWindow().Show();
                }
            }
            ShutdownMode = ShutdownMode.OnLastWindowClose;
        }

        //
        // Note: If one creates a custom version of EdkRepo using this mechanism,
        // be sure to make a new ProductCode and add it to InstallerStrings.KnownVendorCustomizerProductCodes
        //
        private void LoadVendorCustomizer(bool Passive, bool Silent)
        {
            string path = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            Assembly VendorPlugin = null;
            string VendorPluginPath = string.Empty;

            foreach (string file in Directory.GetFiles(path))
            {
                if(Path.GetFileName(file).Equals("TianoCore.EdkMingwInstaller.VendorCustomizer.dll",
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
                        if(Silent)
                        {
                            Console.WriteLine(string.Format("Unable to load vendor customizer: {0}\r\n{1}", file, e.ToString()));
                        }
                        else if (!Passive)
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
                        if (Silent)
                        {
                            Console.WriteLine(string.Format("Unable to load vendor customizer\r\n{0}", e.ToString()));
                        }
                        else
                        {
                            MessageBox.Show(
                                string.Format("Unable to load vendor customizer\r\n{0}", e.ToString()),
                                InstallerStrings.InstallerName,
                                MessageBoxButton.OK,
                                MessageBoxImage.Error
                                );
                        }
                    }
                    Application.Current.Shutdown(1);
                }
            }
        }

        private sealed class OtherVariantInstall
        {
            public string DisplayName;
            public string UninstallString;
        }

        private static bool IsKnownVendorProductCode(string productCode)
        {
            foreach (string known in InstallerStrings.KnownVendorProductCodes)
            {
                if (string.Compare(known, productCode, true) == 0)
                {
                    return true;
                }
            }
            return false;
        }

        //
        // Every installed version of another product variant. Older variants wrote a single entry named after
        // their ProductCode, newer ones write one entry per version, each recording the ProductCode it derives from.
        //
        private List<OtherVariantInstall> FindOtherVariantInstalls()
        {
            List<OtherVariantInstall> found = new List<OtherVariantInstall>();
            string ourProductCode = InstallerStrings.ProductCode;
            using (RegistryKey hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
            using (RegistryKey uninstall = hklm.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"))
            {
                if (uninstall == null)
                {
                    return found;
                }
                foreach (string subKeyName in uninstall.GetSubKeyNames())
                {
                    using (RegistryKey key = uninstall.OpenSubKey(subKeyName))
                    {
                        if (key == null)
                        {
                            continue;
                        }
                        string baseProductCode = key.GetValue("EdkClangBaseProductCode") as string ?? subKeyName;
                        if (string.Compare(baseProductCode, ourProductCode, true) == 0 || !IsKnownVendorProductCode(baseProductCode))
                        {
                            continue;
                        }
                        string uninstallString = key.GetValue("UninstallString") as string;
                        if (string.IsNullOrWhiteSpace(uninstallString))
                        {
                            continue;
                        }
                        found.Add(new OtherVariantInstall
                        {
                            DisplayName = key.GetValue("DisplayName") as string ?? subKeyName,
                            UninstallString = uninstallString
                        });
                    }
                }
            }
            return found;
        }

        private void UninstallOtherVariants(List<OtherVariantInstall> others, int settleMilliseconds)
        {
            foreach (OtherVariantInstall other in others)
            {
                string uninstallString = string.Format("{0} /Passive", other.UninstallString);
                SilentProcess p = SilentProcess.StartConsoleProcessSilently("cmd.exe", string.Format("/S /C \"{0}\"", uninstallString));
                p.WaitForExit();
                Thread.Sleep(settleMilliseconds);
                InstallLogger.Log(string.Format("{0} uninstalled.", other.DisplayName));
            }
        }

        private void CheckForVendorCustomizedEdkRepoAlreadyInstalled(bool Passive)
        {
            List<OtherVariantInstall> others = FindOtherVariantInstalls();
            if (others.Count == 0)
            {
                return;
            }
            string ProductName = InstallerStrings.ProductName;
            string DisplayName = others.Count == 1
                ? others[0].DisplayName
                : string.Format("{0} (and {1} more)", others[0].DisplayName, others.Count - 1);
            if (Passive)
            {
                InstallLogger.Log(string.Format("{0} is a third party version of {1}. {0} is already installed.", DisplayName, ProductName));
                InstallLogger.Log(string.Format("To install this version of {1}, {0} will be uninstalled first.", DisplayName, ProductName));
                UninstallOtherVariants(others, 4000);
            }
            else
            {
                bool uninstall = FluentDialogs.AskYesNo(
                    InstallerStrings.InstallerName,
                    string.Format("{0} is a third party version of {1}, {0} is already installed. To install this version of {1}, {0} must be uninstalled first.\r\n\r\nUninstall {0} now?", DisplayName, ProductName));
                if (uninstall)
                {
                    InstallLogger.Log(string.Format("{0} is a third party version of {1}. {0} is already installed.", DisplayName, ProductName));
                    InstallLogger.Log(string.Format("To install this version of {1}, {0} will be uninstalled first.", DisplayName, ProductName));
                    UninstallOtherVariants(others, 1000);
                }
                else
                {
                    Application.Current.Shutdown(0);
                }
            }
        }

        //
        // Decides which version of EDK II Clang to uninstall. If the /Version argument is not specified then there can
        // only be one EDK II Clang version currently installed. If there are multiple versions of EDK II Clang
        // installed then the /Version argument is mandatory.
        //
        private bool ResolveUninstallVersion(string requested, bool silent, bool passive, out string version)
        {
            version = requested;
            string error = null;
            if (requested != null && !EdkClangLayout.IsVersionName(requested))
            {
                error = string.Format("'{0}' is not a version number such as 20.1.8.", requested);
            }
            else if (requested == null)
            {
                List<InstalledVersion> installed =
                    EdkClangLayout.EnumerateInstalledVersions(Path.GetDirectoryName(WindowsHelpers.GetApplicationPath()));
                if (installed.Count > 1)
                {
                    error = string.Format(
                        "More than one version of {0} is installed ({1}). Uninstall a version from Settings > Apps, or run EdkMingwInstaller.exe /Uninstall /Version <version>.",
                        InstallerStrings.ProductName,
                        string.Join(", ", installed.ConvertAll(v => v.Name)));
                }
                else if (installed.Count == 1)
                {
                    version = installed[0].Name;
                }
            }
            if (error == null)
            {
                return true;
            }
            InstallLogger.Log(error);
            if (silent)
            {
                Console.WriteLine(error);
            }
            else if (!passive)
            {
                MessageBox.Show(error, InstallerStrings.InstallerName, MessageBoxButton.OK, MessageBoxImage.Error);
            }
            Application.Current.Shutdown(1);
            return false;
        }

        private void App_DispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            LogUnhandledException("UI thread", e.Exception);
        }

        private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            LogUnhandledException("background thread", e.ExceptionObject as Exception);
        }

        // InstallLogger may be nonfunctional depending on what crashed, so also
        // write directly to a standalone crash log that doesn't depend on any
        // other part of the app still working.
        private static void LogUnhandledException(string origin, Exception ex)
        {
            string details = string.Format("Unhandled exception on {0}:\n{1}", origin, ex != null ? ex.ToString() : "(no exception object)");
            try
            {
                InstallLogger.Log(details);
            }
            catch
            {
            }
            try
            {
                string crashLogPath = Path.Combine(Path.GetTempPath(), string.Format("EdkMingwInstaller-crash-{0}.log", Guid.NewGuid()));
                File.WriteAllText(crashLogPath, details);
            }
            catch
            {
            }
        }
    }
}
