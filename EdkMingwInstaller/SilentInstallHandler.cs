/** @file
  SilentInstallHandler.cs

@copyright
  Copyright 2025 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TianoCore.EdkMingwInstaller
{
    public class SilentInstallHandler
    {
        private bool uninstall = false;

        internal void UpdateLog(string text)
        {
            if (!string.IsNullOrEmpty(text))
            {
                Console.WriteLine(text);
            }
        }
        private void WorkerComplete(bool Successful, bool Cancelled)
        {
            if (Successful)
            {
                if (uninstall)
                {
                    SilentProcess.StartConsoleProcessSilently(
                        "cmd.exe",
                        string.Format("/c choice /d y /t 3 > nul & rmdir /S /Q \"{0}\"",
                        System.IO.Path.GetDirectoryName(WindowsHelpers.GetApplicationPath())));
                }
                System.Windows.Application.Current.Shutdown(0);
            }
            else
            {
                if (uninstall)
                {
                    InstallLogger.Log("Uninstallation Failed.");
                }
                else
                {
                    InstallLogger.Log("Installation Failed.");
                }
                System.Windows.Application.Current.Shutdown(1);
            }
        }
        private void WorkerProgress(int PercentComplete)
        {
        }
        private void WorkerAllowCancel(bool AllowCancel)
        {
        }
        private bool WorkerCancelPending()
        {
            return false;
        }

        public void PerformInstall()
        {
            try
            {
                InstallWorker.SilentMode = true;
                InstallWorker installWorker = new InstallWorker();
                installWorker.PerformInstall(WorkerComplete, WorkerProgress, WorkerAllowCancel, WorkerCancelPending);
            }
            catch (Exception e)
            {
                InstallLogger.Log(string.Format("Installation Error:\n{0}", e.ToString()));
                WorkerComplete(false, false);
            }
        }

        public void PerformUninstall()
        {
            uninstall = true;
            try
            {
                Console.WriteLine(InstallerStrings.InstallerName);
                string publisher = InstallerStrings.UninstallPublisher;
                if (publisher == "TianoCore")
                    publisher = "The TianoCore Contributors";
                Console.WriteLine(string.Format("Copyright (c) {0}", publisher));
                Console.WriteLine(string.Format("Please wait while we uninstall {0}...", InstallerStrings.ProductName));
                Console.WriteLine();
                InstallLogger.SetLogHook(UpdateLog);
                InstallWorker.SilentMode = true;
                InstallWorker installWorker = new InstallWorker();
                installWorker.PerformUninstall(WorkerComplete, WorkerProgress, WorkerAllowCancel, WorkerCancelPending);
            }
            catch (Exception e)
            {
                InstallLogger.Log(string.Format("Uninstallation Error:\n{0}", e.ToString()));
                WorkerComplete(false, false);
            }
        }
    }
}
