/** @file
  MainWindow.xaml.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using TianoCore.EdkClang;
using TianoCore.EdkMingwInstaller;

namespace TianoCore.EdkClangSettings
{
    public partial class MainWindow : Wpf.Ui.Controls.FluentWindow
    {
        private sealed class ChoiceItem
        {
            // Null for "use the system default".
            public string Version { get; set; }
            public string Label { get; set; }

            // Screen readers use this as the name of the item.
            public override string ToString()
            {
                return Label;
            }
        }

        private sealed class VersionRow
        {
            public string Version { get; set; }
            public string Detail { get; set; }
            public string ButtonText { get; set; }
            public bool IsInstalled { get; set; }
            public AvailableVersion Available { get; set; }
        }

        private readonly InstallRoot root;
        private List<InstalledVersion> installed = new List<InstalledVersion>();
        private List<AvailableVersion> available;
        private string feedError;
        private bool loadingDefaults;
        // What the combo boxes showed when the saved defaults were last read. Null if the saved value is not an installed version.
        private ChoiceItem loadedUser;
        private ChoiceItem loadedSystem;
        private CancellationTokenSource cancellation;

        internal MainWindow(InstallRoot root)
        {
            this.root = root;
            InitializeComponent();

            ImageSource shield = ShieldIcon.Load();
            if (shield == null)
            {
                ShieldImage.Visibility = Visibility.Collapsed;
            }
            else
            {
                ShieldImage.Source = shield;
                ApplyShield.Source = shield;
            }

            Wpf.Ui.Appearance.ApplicationThemeManager.Changed += OnApplicationThemeChanged;
            Closing += delegate
            {
                if (cancellation != null)
                {
                    cancellation.Cancel();
                }
                if (IsLoaded)
                {
                    Wpf.Ui.Appearance.SystemThemeWatcher.UnWatch(this);
                }
            };
            Closed += delegate
            {
                Wpf.Ui.Appearance.ApplicationThemeManager.Changed -= OnApplicationThemeChanged;
            };
        }

        private void Window_SourceInitialized(object sender, EventArgs e)
        {
            Wpf.Ui.Appearance.SystemThemeWatcher.Watch(this, Wpf.Ui.Controls.WindowBackdropType.None, true);
            WindowsHelpers.SetTitleBarTheme(this, ThemeHelper.IsDarkTheme());
        }

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
            await RefreshAsync();
        }

        private void OnApplicationThemeChanged(Wpf.Ui.Appearance.ApplicationTheme currentApplicationTheme, Color systemAccent)
        {
            Dispatcher.Invoke(delegate
            {
                WindowsHelpers.SetTitleBarTheme(this, ThemeHelper.IsDarkTheme());
            });
        }

        private void ShowStatus(Wpf.Ui.Controls.InfoBarSeverity severity, string title, string message)
        {
            StatusInfoBar.Severity = severity;
            StatusInfoBar.Title = title;
            StatusInfoBar.Message = message;
            StatusInfoBar.IsOpen = true;
        }

        private void SetBusy(bool busy)
        {
            DefaultsCard.IsEnabled = !busy;
            VersionsList.IsEnabled = !busy;
            RefreshButton.IsEnabled = !busy;
        }

        //
        // Reloads everything that is shown. The list of versions on GitHub is only fetched when this is not a vendor
        // variant, because a vendor variant is not published there.
        //
        private async Task RefreshAsync()
        {
            installed = EdkClangLayout.EnumerateInstalledVersions(root.Root);
            LoadDefaults();
            BuildRows();

            available = null;
            feedError = null;
            RefreshButton.Visibility = Visibility.Collapsed;
            if (root.IsVendorVariant)
            {
                ShowFeedText("Versions that are not installed are not listed for a vendor-customized installation.");
                return;
            }

            ShowFeedText("Checking GitHub for other versions...");
            CancellationTokenSource feedCancellation = new CancellationTokenSource();
            cancellation = feedCancellation;
            try
            {
                available = await ReleaseFeed.FetchAsync(feedCancellation.Token);
                FeedTextVisible(false);
            }
            catch (OperationCanceledException)
            {
                return;
            }
            catch (Exception e)
            {
                feedError = e.Message;
                ShowFeedText("Could not check GitHub for other versions: " + e.Message);
                RefreshButton.Visibility = Visibility.Visible;
            }
            finally
            {
                cancellation = null;
            }
            BuildRows();
        }

        private void ShowFeedText(string text)
        {
            FeedText.Text = text;
            FeedTextVisible(true);
        }

        private void FeedTextVisible(bool visible)
        {
            FeedText.Visibility = visible ? Visibility.Visible : Visibility.Collapsed;
        }

        private static string VersionOf(string value, string rootPath, IEnumerable<InstalledVersion> versions)
        {
            string name;
            return EdkClangLayout.TryGetVersionName(value, rootPath, out name) &&
                versions.Any(v => v.IsComplete && v.Name == name)
                ? name
                : null;
        }

        private void LoadDefaults()
        {
            loadingDefaults = true;
            try
            {
                string userValue = DefaultVersions.ReadUser();
                string systemValue = DefaultVersions.ReadSystem();
                string userVersion = VersionOf(userValue, root.Root, installed);
                string systemVersion = VersionOf(systemValue, root.Root, installed);

                List<InstalledVersion> complete = installed.Where(v => v.IsComplete).OrderByDescending(v => v.Version).ToList();
                List<ChoiceItem> versionItems = complete.Select(v => new ChoiceItem { Version = v.Name, Label = v.Name }).ToList();

                List<ChoiceItem> userItems = new List<ChoiceItem>
                {
                    new ChoiceItem
                    {
                        Version = null,
                        Label = systemVersion == null ? "Use the system default" : "Use the system default (" + systemVersion + ")"
                    }
                };
                userItems.AddRange(versionItems);
                UserCombo.ItemsSource = userItems;
                UserCombo.SelectedItem = string.IsNullOrEmpty(userValue)
                    ? userItems[0]
                    : userItems.FirstOrDefault(i => i.Version != null && i.Version == userVersion);

                SystemCombo.ItemsSource = versionItems;
                SystemCombo.SelectedItem = versionItems.FirstOrDefault(i => i.Version == systemVersion);

                UserCombo.IsEnabled = SystemCombo.IsEnabled = complete.Count > 0;

                List<string> notes = new List<string>();
                if (!string.IsNullOrEmpty(userValue) && userVersion == null)
                {
                    notes.Add("Your own default points to " + userValue + ", which is not an installed version. It overrides the system default in your new terminals, so pick a version above.");
                }
                if (!string.IsNullOrEmpty(systemValue) && systemVersion == null)
                {
                    notes.Add("The system default points to " + systemValue + ", which is not an installed version.");
                }
                else if (string.IsNullOrEmpty(systemValue) && complete.Count > 0)
                {
                    notes.Add("There is no system default.");
                }
                DefaultsNote.Text = string.Join(" ", notes);
                DefaultsNote.Visibility = notes.Count == 0 ? Visibility.Collapsed : Visibility.Visible;

                loadedUser = UserCombo.SelectedItem as ChoiceItem;
                loadedSystem = SystemCombo.SelectedItem as ChoiceItem;
            }
            finally
            {
                loadingDefaults = false;
            }
            UpdateApplyState();
        }

        private void BuildRows()
        {
            string userValue = DefaultVersions.ReadUser();
            string systemValue = DefaultVersions.ReadSystem();
            List<Tuple<Version, VersionRow>> rows = new List<Tuple<Version, VersionRow>>();

            foreach (InstalledVersion version in installed)
            {
                string detail;
                if (!version.IsComplete)
                {
                    detail = "Incomplete installation. Uninstall it to clean up.";
                }
                else
                {
                    List<string> tags = new List<string>();
                    if (EdkClangLayout.IsSamePath(userValue, version.FullPath))
                    {
                        tags.Add("your default");
                    }
                    if (EdkClangLayout.IsSamePath(systemValue, version.FullPath))
                    {
                        tags.Add("system default");
                    }
                    detail = tags.Count == 0 ? "Installed" : "Installed - " + string.Join(", ", tags);
                }
                rows.Add(Tuple.Create(version.Version, new VersionRow
                {
                    Version = version.Name,
                    Detail = detail,
                    ButtonText = "Uninstall",
                    IsInstalled = true
                }));
            }

            if (available != null)
            {
                foreach (AvailableVersion version in available.Where(a => !installed.Any(i => i.Name == a.Version)))
                {
                    string detail = "Available from GitHub";
                    if (version.Size > 0)
                    {
                        detail += string.Format(" - {0:0} MB", version.Size / (1024.0 * 1024.0));
                    }
                    if (version.Sha256 == null)
                    {
                        detail += " - cannot be verified";
                    }
                    rows.Add(Tuple.Create(version.Parsed, new VersionRow
                    {
                        Version = version.Version,
                        Detail = detail,
                        ButtonText = "Install",
                        Available = version
                    }));
                }
            }

            VersionsList.ItemsSource = rows.OrderByDescending(r => r.Item1).Select(r => r.Item2).ToList();
        }

        private void Combo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (!loadingDefaults)
            {
                UpdateApplyState();
            }
        }

        // Nothing is written until Apply is clicked, so Apply is only available when a selection differs from what is saved.
        private void UpdateApplyState()
        {
            ChoiceItem user = UserCombo.SelectedItem as ChoiceItem;
            ChoiceItem system = SystemCombo.SelectedItem as ChoiceItem;
            ApplyButton.IsEnabled = (user != null && user != loadedUser) || (system != null && system != loadedSystem);
            // Only a change to the system default needs administrator approval.
            ApplyShield.Visibility = ApplyShield.Source != null && system != null && system != loadedSystem
                ? Visibility.Visible
                : Visibility.Collapsed;
        }

        private async void ApplyButton_Click(object sender, RoutedEventArgs e)
        {
            ChoiceItem user = UserCombo.SelectedItem as ChoiceItem;
            ChoiceItem system = SystemCombo.SelectedItem as ChoiceItem;
            List<string> done = new List<string>();
            List<string> problems = new List<string>();
            bool failed = false;
            int changes = 0;
            bool userDefaultCleared = false;

            if (user != null && user != loadedUser)
            {
                try
                {
                    if (user.Version == null)
                    {
                        DefaultVersions.ClearUser();
                        done.Add("Your own default was removed, so your new terminals use the system default.");
                        changes++;
                        userDefaultCleared = true;
                    }
                    else
                    {
                        DefaultVersions.SetUser(root, user.Version);
                        done.Add("Your default is now " + user.Version + ".");
                        changes++;
                    }
                }
                catch (Exception ex)
                {
                    failed = true;
                    problems.Add("Could not change your default: " + ex.Message);
                }
            }

            if (system != null && system != loadedSystem)
            {
                SetBusy(true);
                string error = null;
                ChangeResult result;
                try
                {
                    result = await Task.Run(() =>
                    {
                        string message;
                        ChangeResult outcome = DefaultVersions.SetSystem(root, system.Version, out message);
                        error = message;
                        return outcome;
                    });
                }
                finally
                {
                    SetBusy(false);
                }

                switch (result)
                {
                    case ChangeResult.Success:
                        done.Add("The system default is now " + system.Version + ".");
                        if (!string.IsNullOrEmpty(DefaultVersions.ReadUser()))
                        {
                            done.Add("Your own default still takes priority in your new terminals.");
                        }
                        changes++;
                        break;
                    case ChangeResult.Declined:
                        problems.Add("The system default was not changed because administrator approval was declined.");
                        break;
                    default:
                        failed = true;
                        problems.Add("Could not change the system default: " + error);
                        break;
                }
            }

            if (problems.Count == 0)
            {
                ShowStatus(
                    Wpf.Ui.Controls.InfoBarSeverity.Success,
                    "Defaults applied",
                    string.Join(" ", done) + ((userDefaultCleared && changes == 1) ?
                        "" :
                        " Open a new terminal to " + (changes == 1 ? "use it." : "use them.")));
            }
            else
            {
                ShowStatus(
                    failed ? Wpf.Ui.Controls.InfoBarSeverity.Error : Wpf.Ui.Controls.InfoBarSeverity.Warning,
                    "Some changes were not applied",
                    string.Join(" ", problems.Concat(done)));
            }
            LoadDefaults();
            BuildRows();
        }

        private async void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            await RefreshAsync();
        }

        private void RowButton_Click(object sender, RoutedEventArgs e)
        {
            VersionRow row = (VersionRow)((FrameworkElement)sender).DataContext;
            if (row.IsInstalled)
            {
                Uninstall(row.Version);
            }
            else
            {
                Install(row.Available);
            }
        }

        private void CancelDownloadButton_Click(object sender, RoutedEventArgs e)
        {
            if (cancellation != null)
            {
                cancellation.Cancel();
            }
        }

        //
        // Both operations replace or delete files that this program uses. They end by starting the helper and
        // exiting, see HelperMode.
        //
        private void Uninstall(string version)
        {
            bool isLast = !installed.Any(v => v.IsComplete && v.Name != version);
            string message = isLast
                ? string.Format("{0} is the only installed version. Uninstalling it will remove the edkclang command and this setting pane.\r\n\r\nUninstall?", version)
                : string.Format("Uninstall the {0} release?", version);
            if (!FluentDialogs.AskYesNo("Uninstall " + version, message))
            {
                return;
            }
            string uninstaller = root.FindUninstaller(version);
            if (uninstaller == null)
            {
                ShowStatus(Wpf.Ui.Controls.InfoBarSeverity.Error, "Could not uninstall " + version, "The uninstaller was not found in " + root.Root + ".");
                return;
            }
            string workDirectory = HelperMode.CreateWorkDirectory();
            try
            {
                HelperMode.Launch(uninstaller, "/Uninstall /Version " + version + " /Passive", null, workDirectory);
            }
            catch (Exception e)
            {
                HelperMode.TryDeleteWorkDirectory(workDirectory);
                ShowStatus(Wpf.Ui.Controls.InfoBarSeverity.Error, "Could not uninstall " + version, e.Message);
                return;
            }
            Application.Current.Shutdown();
        }

        private async void Install(AvailableVersion version)
        {
            List<string> older = installed
                .Where(v => v.IsComplete && EdkClangLayout.IsOlderSameMajor(v.Version, version.Parsed))
                .Select(v => v.Name)
                .ToList();
            string intro = string.Format(
                "This action will download {0}{1} from GitHub and run its installer, which asks for administrator approval.",
                version.Version,
                version.Size > 0 ? string.Format(" ({0:0} MB)", version.Size / (1024.0 * 1024.0)) : string.Empty);

            string installerArguments = "/Passive";
            if (older.Count > 0)
            {
                string list = string.Join(", ", older);
                FluentDialogs.Choice choice = FluentDialogs.AskThreeWay(
                    "Install " + version.Version,
                    string.Format("{0}\r\n\r\n{1} is an older release in the {2}.x series. In addition to installing the new version, would you like to remove the old version?", intro, list, version.Parsed.Major),
                    "Remove " + list,
                    "Keep " + list,
                    "Cancel");
                if (choice == FluentDialogs.Choice.Cancel)
                {
                    return;
                }
                if (choice == FluentDialogs.Choice.Secondary)
                {
                    installerArguments += " /KeepOldVersions";
                }
            }
            else if (!FluentDialogs.AskYesNo("Install " + version.Version, intro + "\r\n\r\nContinue?"))
            {
                return;
            }

            string workDirectory = HelperMode.CreateWorkDirectory();
            string file = Path.Combine(workDirectory, version.AssetName);
            CancellationTokenSource downloadCancellation = new CancellationTokenSource();
            cancellation = downloadCancellation;
            StatusInfoBar.IsOpen = false;
            SetBusy(true);
            DownloadProgress.IsIndeterminate = false;
            DownloadProgress.Value = 0;
            ProgressText.Text = "Downloading " + version.AssetName + "...";
            CancelDownloadButton.IsEnabled = true;
            ProgressPanel.Visibility = Visibility.Visible;
            bool launched = false;
            try
            {
                Progress<Tuple<long, long>> progress = new Progress<Tuple<long, long>>(delegate (Tuple<long, long> value)
                {
                    if (value.Item2 > 0)
                    {
                        DownloadProgress.Value = 100.0 * value.Item1 / value.Item2;
                    }
                });
                await ReleaseFeed.DownloadAsync(version, file, progress, downloadCancellation.Token);

                CancelDownloadButton.IsEnabled = false;
                DownloadProgress.IsIndeterminate = true;
                ProgressText.Text = "Checking the digital signature...";
                int trust = await Task.Run(() => Authenticode.Verify(file));
                if (trust != 0)
                {
                    throw new InvalidDataException(string.Format(
                        "The downloaded installer does not have a valid digital signature from a trusted publisher (0x{0:X8}), so it was not run.", trust));
                }

                HelperMode.Launch(file, installerArguments, version.Sha256, workDirectory);
                launched = true;
            }
            catch (OperationCanceledException)
            {
                ShowStatus(Wpf.Ui.Controls.InfoBarSeverity.Informational, "Download cancelled", "Nothing was installed.");
            }
            catch (Exception e)
            {
                ShowStatus(Wpf.Ui.Controls.InfoBarSeverity.Error, "Could not install " + version.Version, e.Message);
            }
            finally
            {
                cancellation = null;
                if (!launched)
                {
                    HelperMode.TryDeleteWorkDirectory(workDirectory);
                    ProgressPanel.Visibility = Visibility.Collapsed;
                    SetBusy(false);
                }
            }
            if (launched)
            {
                Application.Current.Shutdown();
            }
        }
    }
}
