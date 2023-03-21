/** @file
  InstallLogger.cs

@copyright
  Copyright 2016 - 2023 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace TianoCore.EdkRepoInstaller
{
    public delegate void LogHook(string LogMessage);
    public class InstallLogger
    {
        private static readonly object LogMutex = new object();
        private static LogHook LogHook = null;
        private static string LogFilePath = null;
        private static bool SilentMode = false;

        public static void SetLogHook(LogHook hook)
        {
            lock (LogMutex)
            {
                LogHook = hook;
            }
        }
        public static void SetSilentMode(bool silentMode)
        {
            lock (LogMutex)
            {
                SilentMode = silentMode;
            }
        }
        public static void Log(string LogMessage)
        {
            lock (LogMutex)
            {
                if (LogFilePath == null)
                {
                    LogFilePath = Path.Combine(
                        Environment.GetEnvironmentVariable("temp"),
                        string.Format("EdkRepoInstaller-{0}.log", Guid.NewGuid().ToString()));
                }
                string[] lines = LogMessage.Split('\n');
                List<string> trimmedLines = new List<string>();
                foreach (string line in lines)
                {
                    string trimmedLine = line.Trim();
                    if(!string.IsNullOrEmpty(trimmedLine))
                    {
                        trimmedLines.Add(trimmedLine);
                    }
                }
                try
                {
                    FileStream stream = null;
                    stream = File.Open(LogFilePath, FileMode.OpenOrCreate, FileAccess.Write, FileShare.ReadWrite);
                    stream.Seek(0, SeekOrigin.End);
                    StreamWriter writer = new StreamWriter(stream);
                    foreach (string line in trimmedLines)
                    {
                        writer.WriteLine(line);
                    }
                    writer.Flush();
                    writer.Close();
                }
                catch(Exception e)
                {
                    if (LogHook != null)
                    {
                        LogHook(string.Format("Warning: Writing to log file failed: {0}\n", e.ToString()));
                    }
                    else
                    {
                        if (SilentMode)
                        {
                            Console.WriteLine(string.Format("Warning: Writing to log file failed: {0}\n", e.ToString()));
                        }
                        else
                        {
                            MessageBox.Show(
                                string.Format("Warning: Writing to log file failed: {0}\n", e.ToString()),
                                "Installer Error",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning
                                );
                        }
                    }
                }

                if (LogHook != null)
                {
                    foreach (string line in trimmedLines)
                    {
                        LogHook(line);
                    }
                }
            }
        }
    }
}
