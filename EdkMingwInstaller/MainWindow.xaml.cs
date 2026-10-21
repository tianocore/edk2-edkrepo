/** @file
  MainWindow.xaml.cs

@copyright
  Copyright 2025 - 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace TianoCore.EdkMingwInstaller
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Wpf.Ui.Controls.FluentWindow
    {
        private Viewbox currentSplash;

        public MainWindow()
        {
            InitializeComponent();
            currentSplash = VendorCustomizer.GetWelcomeSplash(ThemeHelper.IsDarkTheme());
            ContentGrid.Children.Insert(0, currentSplash);
            Title = string.Format("{0} Installer", InstallerStrings.ProductName);

            Wpf.Ui.Appearance.ApplicationThemeManager.Changed += OnApplicationThemeChanged;
            Closing += delegate
            {
                Wpf.Ui.Appearance.SystemThemeWatcher.UnWatch(this);
            };
            Closed += delegate
            {
                Wpf.Ui.Appearance.ApplicationThemeManager.Changed -= OnApplicationThemeChanged;
            };
            bool chooseDefault = false;
            try
            {
                chooseDefault = InstallWorker.GetVersionsAfterInstall(InstallWorker.GetDefaultInstallRoot()).Count > 1;
            }
            catch (Exception ex)
            {
                InstallLogger.Log(string.Format("Could not list the installed versions: {0}", ex.Message));
            }
            if (chooseDefault) {
                cmdInstall.Content = "Next";
            }
        }

        private void MainWindow_SourceInitialized(object sender, EventArgs e)
        {
            Wpf.Ui.Appearance.SystemThemeWatcher.Watch(this, Wpf.Ui.Controls.WindowBackdropType.None, true);
        }

        private void OnApplicationThemeChanged(Wpf.Ui.Appearance.ApplicationTheme currentApplicationTheme, Color systemAccent)
        {
            Dispatcher.Invoke(delegate
            {
                ContentGrid.Children.Remove(currentSplash);
                currentSplash = VendorCustomizer.GetWelcomeSplash(ThemeHelper.IsDarkTheme());
                ContentGrid.Children.Insert(0, currentSplash);
            });
        }

        private void cmdInstall_Click(object sender, RoutedEventArgs e)
        {
            // The options page only matters when there is a choice of default version.
            bool chooseDefault = false;
            try
            {
                chooseDefault = InstallWorker.GetVersionsAfterInstall(InstallWorker.GetDefaultInstallRoot()).Count > 1;
            }
            catch (Exception ex)
            {
                InstallLogger.Log(string.Format("Could not list the installed versions: {0}", ex.Message));
            }
            Window next = chooseDefault ? (Window)new OptionsWindow() : new ProgressWindow();
            next.Show();
            this.Close();
        }

        private void cmdCancel_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }

        private void RootGrid_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            try
            {
                DragMove();
            }
            catch (InvalidOperationException)
            {
            }
        }
    }
}
