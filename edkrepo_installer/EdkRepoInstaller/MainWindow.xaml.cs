/** @file
  MainWindow.xaml.cs

@copyright
  Copyright 2016 - 2019 Intel Corporation. All rights reserved.<BR>
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

namespace TianoCore.EdkRepoInstaller
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            Viewbox WelcomeSplash = null;
            if (VendorCustomizer.Instance != null)
            {
                WelcomeSplash = VendorCustomizer.Instance.WelcomeSplash;
            }
            if (WelcomeSplash == null)
            {
                TianoCoreBranding TianoBranding = new TianoCoreBranding();
                TianoBranding.Children.Remove(TianoBranding.WelcomeSplash);
                WelcomeSplash = TianoBranding.WelcomeSplash;
            }
            RootGrid.Children.Add(WelcomeSplash);
            Title = string.Format("{0} Installer", InstallerStrings.ProductName);
        }

        private void cmdInstall_Click(object sender, RoutedEventArgs e)
        {
            ProgressWindow progressWindow = new ProgressWindow();
            progressWindow.Show();
            this.Close();
        }

        private void cmdCancel_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }
    }
}
