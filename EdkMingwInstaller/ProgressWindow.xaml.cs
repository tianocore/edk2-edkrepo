/** @file
  ProgressWindow.xaml.cs

@copyright
  Copyright 2025 - 2026 Intel Corporation. All rights reserved.<BR>
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

namespace TianoCore.EdkMingwInstaller
{
    /// <summary>
    /// Interaction logic for ProgressWindow.xaml
    /// </summary>
    public partial class ProgressWindow : Wpf.Ui.Controls.FluentWindow
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
        private Viewbox currentLogo;

        public ProgressWindow()
        {
            PassiveMode = false;
            InitializeComponent();
            currentLogo = VendorCustomizer.GetLogo(ThemeHelper.IsDarkTheme());
            double Ratio = currentLogo.Width / currentLogo.Height;
            currentLogo.Height = 48;
            currentLogo.Width = Ratio * 48;
            currentLogo.HorizontalAlignment = HorizontalAlignment.Right;
            currentLogo.VerticalAlignment = VerticalAlignment.Center;
            Grid.SetColumn(currentLogo, 1);
            HeaderGrid.Children.Add(currentLogo);
            string ProductName = InstallerStrings.ProductName;
            Title = string.Format("{0} Installer", ProductName);
            InstallingLabel.Text = string.Format("Installing {0}", ProductName);

            Wpf.Ui.Appearance.ApplicationThemeManager.Changed += OnApplicationThemeChanged;
            Closing += delegate
            {
                Wpf.Ui.Appearance.SystemThemeWatcher.UnWatch(this);
            };
            Closed += delegate
            {
                Wpf.Ui.Appearance.ApplicationThemeManager.Changed -= OnApplicationThemeChanged;
            };
        }

        private void OnApplicationThemeChanged(Wpf.Ui.Appearance.ApplicationTheme currentApplicationTheme, Color systemAccent)
        {
            Dispatcher.Invoke(delegate
            {
                WindowsHelpers.SetTitleBarTheme(this, ThemeHelper.IsDarkTheme());
                HeaderGrid.Children.Remove(currentLogo);
                currentLogo = VendorCustomizer.GetLogo(ThemeHelper.IsDarkTheme());
                double Ratio = currentLogo.Width / currentLogo.Height;
                currentLogo.Height = 48;
                currentLogo.Width = Ratio * 48;
                currentLogo.HorizontalAlignment = HorizontalAlignment.Right;
                currentLogo.VerticalAlignment = VerticalAlignment.Center;
                Grid.SetColumn(currentLogo, 1);
                HeaderGrid.Children.Add(currentLogo);
            });
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
                    InstallingLabel.Text = string.Format("Uninstalling {0}", ProductName);
                }
                else
                {
                    lock (CancelPendingLock)
                    {
                        uninstallMode = false;
                    }
                    InstallingLabel.Text = string.Format("Installing {0}", ProductName);
                }
            }
        }

        private void ActionButton_Click(object sender, RoutedEventArgs e)
        {
            if (InstallDone)
            {
                CloseWindow();
            }
            else
            {
                lock (CancelPendingLock)
                {
                    CancelPending = true;
                }
                ActionButton.IsEnabled = false;
            }
        }

        private void HeaderGrid_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            try
            {
                DragMove();
            }
            catch (InvalidOperationException)
            {
                // The left button event can already be triggered by the time DragMove() checks it on a fast click.
            }
        }

        private void Window_SourceInitialized(object sender, EventArgs e)
        {
            HwndSource HwndSource = PresentationSource.FromVisual(this) as HwndSource;
            if (HwndSource != null)
            {
                HwndSource.AddHook(new HwndSourceHook(this.HwndSourceHook));
            }
            Wpf.Ui.Appearance.SystemThemeWatcher.Watch(this, Wpf.Ui.Controls.WindowBackdropType.None, true);
            WindowsHelpers.SetTitleBarTheme(this, ThemeHelper.IsDarkTheme());
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
                SilentProcess.StartConsoleProcessSilently(
                    "cmd.exe",
                    string.Format("/c choice /d y /t 3 > nul & rmdir /S /Q \"{0}\"",
                    System.IO.Path.GetDirectoryName(WindowsHelpers.GetApplicationPath())));
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
                        ProgressTextScrollViewer.ScrollToEnd();
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
                            if (PassiveMode)
                            {
                                CloseWindow();
                            }
                            else
                            {
                                ResultInfoBar.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                                ResultInfoBar.Title = UninstallMode ? "Uninstallation Successful" : "Installation Successful";
                                ResultInfoBar.Message = string.Empty;
                                InstallProgress.Visibility = Visibility.Collapsed;
                                ResultInfoBar.IsOpen = true;
                                ActionButton.Content = "Finish";
                                ActionButton.Appearance = Wpf.Ui.Controls.ControlAppearance.Primary;
                                ActionButton.IsDefault = true;
                                ActionButton.IsEnabled = true;
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
                        ResultInfoBar.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                        ResultInfoBar.Title = uninstall ? "Uninstallation failed" : "Installation failed";
                        ResultInfoBar.Message = "See details below.";
                        InstallProgress.Visibility = Visibility.Collapsed;
                        ResultInfoBar.IsOpen = true;
                        ActionButton.Content = "Close";
                        ActionButton.IsEnabled = true;
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
                ActionButton.IsEnabled = AllowCancel;
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
                InstallWorker.SilentMode = false;
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
                InstallLogger.Log(string.Format("Installation Error:\n{0}", e.ToString()));
                WorkerThreadFailed();
            }
        }
    }
}
