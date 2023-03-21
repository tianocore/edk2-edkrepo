/** @file
  ProgressWindow.xaml.cs

@copyright
  Copyright 2016 - 2023 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;

namespace TianoCore.EdkRepoInstaller
{
    /// <summary>
    /// Interaction logic for ProgressWindow.xaml
    /// </summary>
    public partial class ProgressWindow : Window
    {
        private bool AllowClose = false;
        private bool FirstLoad = true;
        private bool InstallDone = false;
        private bool uninstallMode = false;
        private StringBuilder logString = new StringBuilder();
        private Thread workerThread = null;
        private readonly object CancelPendingLock = new object();
        private bool CancelPending = false;
        private int ExitCode = 0;

        public ProgressWindow()
        {
            PassiveMode = false;
            InitializeComponent();
            InitializeComponent();
            Viewbox VendorLogo = null;
            if (VendorCustomizer.Instance != null)
            {
                VendorLogo = VendorCustomizer.Instance.VendorLogo;
            }
            if (VendorLogo == null)
            {
                TianoCoreBranding TianoBranding = new TianoCoreBranding();
                TianoBranding.Children.Remove(TianoBranding.TianoCoreLogo);
                VendorLogo = TianoBranding.TianoCoreLogo;
            }
            double Ratio = VendorLogo.Width / VendorLogo.Height;
            VendorLogo.Height = 48;
            VendorLogo.Width = Ratio * 48;
            VendorLogo.HorizontalAlignment = HorizontalAlignment.Right;
            VendorLogo.VerticalAlignment = VerticalAlignment.Top;
            VendorLogo.Margin = new Thickness(0, 5, 11, 0);
            RootGrid.Children.Add(VendorLogo);
            string ProductName = InstallerStrings.ProductName;
            Title = string.Format("{0} Installer", ProductName);
            InstallingLabel.Content = string.Format("Installing {0}", ProductName);
            ActionLabel.Content = string.Format("Please wait while the Setup Wizard installs {0}.", ProductName);
        }

        public bool PassiveMode { get; set; }
        public bool UninstallMode
        {
            get
            {
                return uninstallMode;
            }
            set
            {
                string ProductName = InstallerStrings.ProductName;
                if (value)
                {
                    lock (CancelPendingLock)
                    {
                        uninstallMode = true;
                    }
                    InstallingLabel.Content = string.Format("Uninstalling {0}", ProductName);
                    ActionLabel.Content = string.Format("Please wait while the Setup Wizard uninstalls {0}.", ProductName);
                }
                else
                {
                    lock (CancelPendingLock)
                    {
                        uninstallMode = false;
                    }
                    InstallingLabel.Content = string.Format("Installing {0}", ProductName);
                    ActionLabel.Content = string.Format("Please wait while the Setup Wizard installs {0}.", ProductName);
                }
            }
        }

        private void CancelButton_Click(object sender, RoutedEventArgs e)
        {
            if (!InstallDone)
            {
                lock (CancelPendingLock)
                {
                    CancelPending = true;
                }
                CancelButton.IsEnabled = false;
            }
            else
            {
                CloseWindow();
            }
        }
        private void NextButton_Click(object sender, RoutedEventArgs e)
        {
            if(InstallDone)
            {
                CloseWindow();
            }
        }

        private void Window_SourceInitialized(object sender, EventArgs e)
        {
            HwndSource HwndSource = PresentationSource.FromVisual(this) as HwndSource;
            if (HwndSource != null)
            {
                HwndSource.AddHook(new HwndSourceHook(this.HwndSourceHook));
            }
        }

        private IntPtr HwndSourceHook (IntPtr Hwnd, int Msg, IntPtr wParam, IntPtr lParam, ref bool Handled)
        {
            if (Msg == WM_SHOWWINDOW)
            {
                IntPtr hMenu = GetSystemMenu(Hwnd, false);
                if(hMenu != IntPtr.Zero)
                {
                    EnableMenuItem(hMenu, SC_CLOSE, MF_BYCOMMAND | MF_GRAYED);
                }
            }
            else if (Msg == WM_CLOSE)
            {
                if (!AllowClose)
                {
                    Handled = true;
                }
            }
            return IntPtr.Zero;
        }

        //
        // Copied from P/Invoke.net
        //
        private const int WM_SHOWWINDOW = 0x18;
        private const int WM_CLOSE = 0x10;
        private const uint SC_CLOSE = 0xF060;
        private const uint MF_BYCOMMAND = 0x0;
        private const uint MF_ENABLED = 0x0;
        private const uint MF_GRAYED = 0x1;
        [DllImport("user32.dll")]
        private static extern IntPtr GetSystemMenu(IntPtr hWnd, bool bRevert);
        [DllImport("user32.dll")]
        private static extern bool EnableMenuItem(IntPtr hMenu, uint uIDEnableItem, uint uEnable);

        private void CloseWindow()
        {
            if(UninstallMode && InstallDone)
            {
                if(VendorCustomizer.Instance != null)
                {
                    SilentProcess.StartConsoleProcessSilently(
                        "cmd.exe",
                        string.Format("/c choice /d y /t 3 > nul & del \"{0}\"", VendorCustomizer.VendorPluginPath));
                }
                SilentProcess.StartConsoleProcessSilently(
                    "cmd.exe",
                    string.Format("/c choice /d y /t 3 > nul & del \"{0}\"", WindowsHelpers.GetApplicationPath()));
            }
            AllowClose = true;
            Close();
            Environment.ExitCode = ExitCode;
        }
        private void Window_ContentRendered(object sender, EventArgs e)
        {
            if (FirstLoad)
            {
                FirstLoad = false;
                InstallLogger.SetLogHook(new LogHook(this.UpdateLog));
                workerThread = new Thread(new ThreadStart(WorkerThread));
                workerThread.Start();
            }
        }

        private void UpdateLog(string text)
        {
            Dispatcher.BeginInvoke(new Action<string>(delegate(string delegateText)
                {
                    if (!string.IsNullOrEmpty(delegateText))
                    {
                        logString.Append(delegateText);
                        logString.Append("\r\n");
                        ProgressTextBox.Text = logString.ToString();
                        ProgressTextBox.ScrollToEnd();
                    }
                }), text);
        }

        private void WorkerThreadComplete(bool Successful, bool Cancelled)
        {
            if (Successful)
            {
                if (Cancelled)
                {
                    Dispatcher.BeginInvoke(new Action(delegate()
                    {
                        CloseWindow();
                    }));
                }
                else
                {
                    Dispatcher.BeginInvoke(new Action(delegate()
                        {
                            InstallDone = true;
                            InstallProgress.IsIndeterminate = false;
                            InstallProgress.Value = 100;
                            FrameworkElement animation = InstallProgress.Template.FindName("PART_GlowRect", InstallProgress) as FrameworkElement;
                            if (animation != null) animation.Visibility = Visibility.Hidden;
                            if (PassiveMode)
                            {
                                CloseWindow();
                            }
                            else
                            {
                                NextButton.Content = "Finish";
                                NextButton.IsEnabled = true;
                                CancelButton.IsEnabled = false;
                            }
                        }));
                }
            }
            else
            {
                WorkerThreadFailed();
            }
        }

        private void WorkerThreadFailed()
        {
            bool uninstall;
            lock (CancelPendingLock)
            {
                uninstall = uninstallMode;
            }
            if (uninstall)
            {
                InstallLogger.Log("Uninstallation Failed.");
            }
            else
            {
                InstallLogger.Log("Installation Failed.");
            }
            Dispatcher.BeginInvoke(new Action(delegate()
                {
                    ExitCode = 1;
                    InstallDone = true;
                    InstallProgress.IsIndeterminate = false;
                    InstallProgress.Value = 0;
                    if (PassiveMode)
                    {
                        CloseWindow();
                    }
                    else
                    {
                        if (uninstall)
                        {
                            MessageBox.Show("Uninstallation Failed.", "Uninstallation Error", MessageBoxButton.OK, MessageBoxImage.Error);
                        }
                        else
                        {
                            MessageBox.Show("Installation Failed.", "Installation Error", MessageBoxButton.OK, MessageBoxImage.Error);
                        }
                        CancelButton.IsEnabled = true;
                    }
                }));
        }

        private void WorkerThreadProgress(int PercentComplete)
        {
            Dispatcher.BeginInvoke(new Action(delegate()
                {
                    InstallProgress.IsIndeterminate = false;
                    InstallProgress.Value = PercentComplete;
                }));
        }

        private void WorkerThreadAllowCancel(bool AllowCancel)
        {
            Dispatcher.Invoke(new Action(delegate()
            {
                CancelButton.IsEnabled = AllowCancel;
            }));
        }

        private bool WorkerThreadCancelPending()
        {
            lock (CancelPendingLock)
            {
                return CancelPending;
            }
        }

        private void WorkerThread()
        {
            try
            {
                bool uninstall;
                lock (CancelPendingLock)
                {
                    uninstall = uninstallMode;
                }
                InstallWorker installWorker = new InstallWorker();
                if (uninstall)
                {
                    installWorker.PerformUninstall(WorkerThreadComplete, WorkerThreadProgress, WorkerThreadAllowCancel, WorkerThreadCancelPending);
                }
                else
                {
                    installWorker.PerformInstall(WorkerThreadComplete, WorkerThreadProgress, WorkerThreadAllowCancel, WorkerThreadCancelPending);
                }
            }
            catch(Exception e)
            {
                if (e is PythonPackageInstallException || e is PythonPackageUninstallException)
                {
                    InstallLogger.Log(e.Message);
                }
                else
                {
                    InstallLogger.Log(string.Format("Installation Error:\n{0}", e.ToString()));
                }
                WorkerThreadFailed();
            }
        }
    }
}
