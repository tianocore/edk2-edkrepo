/** @file
  FluentDialogs.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/
using System;
using System.Windows;
using System.Windows.Threading;

namespace TianoCore.EdkMingwInstaller
{
    internal static class FluentDialogs
    {
        //
        // This function is safe to call from any thread. It marshals onto the UI thread
        // and blocks the caller until the user responds or timeout elapses.
        //
        public static bool AskYesNo(string title, string message, TimeSpan? timeout = null)
        {
            return Application.Current.Dispatcher.Invoke(delegate
            {
                Wpf.Ui.Controls.MessageBox messageBox = new Wpf.Ui.Controls.MessageBox
                {
                    Title = title,
                    Content = message,
                    PrimaryButtonText = "Yes",
                    CloseButtonText = "No",
                    Topmost = true,
                };

                DispatcherTimer timer = null;
                if (timeout.HasValue)
                {
                    timer = new DispatcherTimer { Interval = timeout.Value };
                    timer.Tick += delegate
                    {
                        timer.Stop();
                        // MessageBox hides Window.Close(). Therefore, Window.Close()
                        // must be called explicitly to dismiss the dialog.
                        ((Window)messageBox).Close();
                    };
                    timer.Start();
                }

                Wpf.Ui.Controls.MessageBoxResult result = messageBox.ShowDialogAsync().GetAwaiter().GetResult();
                timer?.Stop();
                return result == Wpf.Ui.Controls.MessageBoxResult.Primary;
            });
        }
    }
}
