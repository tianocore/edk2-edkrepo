/** @file
  App.xaml.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Windows;

namespace TianoCore.EdkClangSettings
{
    public partial class App : Application
    {
        internal const string Caption = "EDK II Clang Settings";

        private void Application_Startup(object sender, StartupEventArgs e)
        {
            Wpf.Ui.Appearance.ApplicationThemeManager.ApplySystemTheme();

            InstallRoot root;
            string error;
            if (!InstallRoot.TryLocate(e.Args, out root, out error))
            {
                MessageBox.Show(error, Caption, MessageBoxButton.OK, MessageBoxImage.Error);
                Shutdown(1);
                return;
            }
            new MainWindow(root).Show();
        }
    }
}
