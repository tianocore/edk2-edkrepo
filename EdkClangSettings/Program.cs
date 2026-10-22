/** @file
  Program.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.IO;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Threading;

namespace TianoCore.EdkClangSettings
{
    public static class Program
    {
        [STAThread]
        public static int Main(string[] args)
        {
            if (args.Length > 0 && string.Equals(args[0], HelperMode.Switch, StringComparison.Ordinal))
            {
                return HelperMode.Run(args);
            }
            try
            {
                return RunApplication();
            }
            catch (Exception e)
            {
                Report(e);
                return 1;
            }
        }

        // Without the WPF-UI DLLs next to the exe, a failure would otherwise be a silent crash.
        private static void Report(Exception exception)
        {
            Exception root = exception.GetBaseException();
            bool missingFile = root is FileNotFoundException || root is FileLoadException || root is BadImageFormatException;
            MessageBox.Show(
                missingFile
                    ? "EDK II Clang Settings could not start. It needs the DLLs that are installed next to it in the tools folder.\r\n\r\n" + root.Message
                    : exception.ToString(),
                "EDK II Clang Settings",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }

        private static void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            Report(e.Exception);
            e.Handled = true;
            Application.Current.Shutdown(1);
        }

        // The helper copy runs without the WPF-UI files next to it, so App must not be loaded until it is needed.
        [MethodImpl(MethodImplOptions.NoInlining)]
        private static int RunApplication()
        {
            App app = new App();
            // Registered here rather than in App, because App cannot run when its own startup code fails to load.
            app.DispatcherUnhandledException += OnDispatcherUnhandledException;
            app.InitializeComponent();
            return app.Run();
        }
    }
}
