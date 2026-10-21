/** @file
  OptionsWindow.xaml.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace TianoCore.EdkMingwInstaller
{
    /// <summary>
    /// Shown between the welcome page and the progress window when another version is installed, so the
    /// user can pick the system default version and whether older versions of the same major release are removed.
    /// </summary>
    public partial class OptionsWindow : Wpf.Ui.Controls.FluentWindow
    {
        private sealed class VersionItem
        {
            public string Version { get; set; }
            public string Label { get; set; }
        }

        private Viewbox currentLogo;
        private readonly string root;
        private readonly string newVersion;
        private readonly string currentDefault;
        private readonly string preselected;
        private readonly List<string> olderVersions;

        public OptionsWindow()
        {
            InitializeComponent();
            Title = string.Format("{0} Installer", InstallerStrings.ProductName);
            SetLogo();

            root = InstallWorker.GetDefaultInstallRoot();
            newVersion = InstallWorker.ToolchainVersion;
            currentDefault = InstallWorker.GetCurrentSystemDefaultVersion(root);
            preselected = InstallWorker.ChooseDefaultAutomatically(root, newVersion);
            olderVersions = InstallWorker.GetOlderSameMajorVersions(root, newVersion);

            if (olderVersions.Count > 0)
            {
                string olderList = string.Join(", ", olderVersions);
                Version parsed = Version.Parse(newVersion);
                OlderVersionsText.Text = string.Format(
                    "{0} is already installed. {1} is a newer release of the {2}.x series.",
                    olderList, newVersion, parsed.Major);
                UninstallOlderRadio.Content = string.Format("Uninstall {0} (recommended)", olderList);
                KeepOlderRadio.Content = string.Format("Keep {0}", olderList);
                OlderVersionsPanel.Visibility = Visibility.Visible;
                DescriptionText.Text = "Choose what happens to the older version, and which version is used by default in new terminals.";
                MinHeight = MaxHeight = Height = 500;
            }
            else
            {
                DescriptionText.Text = string.Format(
                    "More than one version of {0} will be installed. Choose which version is used by default in new terminals.",
                    InstallerStrings.ProductName);
            }

            RebuildVersionList();
            UninstallOlderRadio.Checked += delegate { RebuildVersionList(); };
            KeepOlderRadio.Checked += delegate { RebuildVersionList(); };

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

        private bool RemoveOlderVersions
        {
            get { return olderVersions.Count > 0 && UninstallOlderRadio.IsChecked == true; }
        }

        // The default can only be a version that still exists after the install.
        private void RebuildVersionList()
        {
            VersionItem previous = VersionComboBox.SelectedItem as VersionItem;
            List<VersionItem> items = new List<VersionItem>();
            foreach (string version in InstallWorker.GetVersionsAfterInstall(root, RemoveOlderVersions))
            {
                List<string> notes = new List<string>();
                if (version == newVersion)
                {
                    notes.Add("new");
                }
                if (version == currentDefault)
                {
                    notes.Add("current default");
                }
                items.Add(new VersionItem
                {
                    Version = version,
                    Label = notes.Count == 0 ? version : string.Format("{0} ({1})", version, string.Join(", ", notes))
                });
            }
            VersionComboBox.ItemsSource = items;
            VersionComboBox.SelectedItem =
                (previous == null ? null : items.Find(i => i.Version == previous.Version)) ??
                items.Find(i => i.Version == preselected) ??
                items[0];
            VersionComboBox.IsEnabled = items.Count > 1;
            HintText.Text = items.Count > 1
                ? "You can switch versions later with the edkclang command."
                : string.Format("Only {0} will be installed, so it is the default.", items[0].Version);
        }

        private void SetLogo()
        {
            if (currentLogo != null)
            {
                HeaderGrid.Children.Remove(currentLogo);
            }
            currentLogo = VendorCustomizer.GetLogo(ThemeHelper.IsDarkTheme());
            double ratio = currentLogo.Width / currentLogo.Height;
            currentLogo.Height = 48;
            currentLogo.Width = ratio * 48;
            currentLogo.HorizontalAlignment = HorizontalAlignment.Right;
            currentLogo.VerticalAlignment = VerticalAlignment.Center;
            Grid.SetColumn(currentLogo, 1);
            HeaderGrid.Children.Add(currentLogo);
        }

        private void OnApplicationThemeChanged(Wpf.Ui.Appearance.ApplicationTheme currentApplicationTheme, Color systemAccent)
        {
            Dispatcher.Invoke(delegate
            {
                WindowsHelpers.SetTitleBarTheme(this, ThemeHelper.IsDarkTheme());
                SetLogo();
            });
        }

        private void Window_SourceInitialized(object sender, EventArgs e)
        {
            Wpf.Ui.Appearance.SystemThemeWatcher.Watch(this, Wpf.Ui.Controls.WindowBackdropType.None, true);
            WindowsHelpers.SetTitleBarTheme(this, ThemeHelper.IsDarkTheme());
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

        private void cmdInstall_Click(object sender, RoutedEventArgs e)
        {
            ProgressWindow progressWindow = new ProgressWindow();
            progressWindow.SelectedDefaultVersion = ((VersionItem)VersionComboBox.SelectedItem).Version;
            progressWindow.RemoveOlderSameMajorVersions = RemoveOlderVersions || olderVersions.Count == 0;
            progressWindow.Show();
            Close();
        }

        private void cmdCancel_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }
    }
}
