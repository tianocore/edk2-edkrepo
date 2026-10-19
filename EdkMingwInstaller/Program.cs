/** @file
  Program.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Windows;
using Microsoft.Win32;

namespace TianoCore.EdkMingwInstaller
{
    public static class Program
    {
        //
        // "Release" DWORD value for .NET Framework 4.6.2, see:
        // https://learn.microsoft.com/dotnet/framework/migration-guide/how-to-determine-which-versions-are-installed
        //
        private const int NetFramework462ReleaseKey = 394802;

        private static readonly object AssemblyCacheLock = new object();
        private static readonly Dictionary<string, Assembly> AssemblyCache = new Dictionary<string, Assembly>();

        [STAThread]
        public static int Main()
        {
            if (!IsNetFramework462OrNewer())
            {
                ReportMissingNetFramework();
                return 1;
            }

            //
            // Must be registered before anything touches the WPF-UI assemblies embedded below.
            //
            AppDomain.CurrentDomain.AssemblyResolve += ResolveEmbeddedAssembly;
            return RunApplication();
        }

        //
        // Not in Main() so JIT does not load App (and its WPF-UI references) until after the resolver is registered.
        //
        [MethodImpl(MethodImplOptions.NoInlining)]
        private static int RunApplication()
        {
            App app = new App();
            app.InitializeComponent();
            return app.Run();
        }

        private static Assembly ResolveEmbeddedAssembly(object sender, ResolveEventArgs args)
        {
            string simpleName = new AssemblyName(args.Name).Name;
            if (simpleName.EndsWith(".resources", StringComparison.OrdinalIgnoreCase))
            {
                return null;
            }
            lock (AssemblyCacheLock)
            {
                Assembly cached;
                if (AssemblyCache.TryGetValue(simpleName, out cached))
                {
                    return cached;
                }
                string resourceName = string.Format("EmbeddedAssemblies.{0}.dll", simpleName);
                using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName))
                {
                    if (stream == null)
                    {
                        return null;
                    }
                    byte[] assemblyBytes = new byte[stream.Length];
                    stream.Read(assemblyBytes, 0, assemblyBytes.Length);
                    Assembly loaded = Assembly.Load(assemblyBytes);
                    AssemblyCache[simpleName] = loaded;
                    return loaded;
                }
            }
        }

        private static bool IsNetFramework462OrNewer()
        {
            using (RegistryKey key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\"))
            {
                if (key == null)
                {
                    return false;
                }
                object release = key.GetValue("Release");
                return release is int && (int)release >= NetFramework462ReleaseKey;
            }
        }

        private static void ReportMissingNetFramework()
        {
            bool silent = false;
            foreach (string arg in Environment.GetCommandLineArgs())
            {
                if ((string.Compare(arg, "/silent", StringComparison.OrdinalIgnoreCase) == 0) ||
                    (string.Compare(arg, "-silent", StringComparison.OrdinalIgnoreCase) == 0) ||
                    (string.Compare(arg, "--silent", StringComparison.OrdinalIgnoreCase) == 0))
                {
                    silent = true;
                }
            }
            string message = string.Format("{0} requires .NET Framework 4.6.2 or newer. Please update Windows and try again.", InstallerStrings.ProductName);
            if (silent)
            {
                Console.WriteLine(message);
            }
            else
            {
                MessageBox.Show(message, InstallerStrings.InstallerName, MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
