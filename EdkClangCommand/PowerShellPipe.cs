/** @file
  PowerShellPipe.cs

  Changes environment variables of a running PowerShell process through its
  host pipe, using the same the mechanism as Enter-PSHostProcess.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Runtime.CompilerServices;
using System.Threading;

namespace TianoCore.EdkClang
{
    internal static class PowerShellPipe
    {
        //
        // Prevent the .Net JIT compiler from attempting to resolve the System.Management.Automation assembly unless a
        // PowerShell session has to be changed. This assembly is absent on machines without Windows PowerShell 5.1.
        //
        [MethodImpl(MethodImplOptions.NoInlining)]
        public static void ApplyEnvironment(int processId, IEnumerable<KeyValuePair<string, string>> changes)
        {
            NamedPipeConnectionInfo connection = new NamedPipeConnectionInfo(processId);
            connection.OpenTimeout = 5000;
            using (Runspace runspace = RunspaceFactory.CreateRunspace(connection))
            {
                runspace.Open();
                foreach (KeyValuePair<string, string> change in changes)
                {
                    using (PowerShell shell = PowerShell.Create())
                    {
                        shell.Runspace = runspace;
                        shell.AddCommand("Set-Item")
                             .AddParameter("LiteralPath", "Env:" + change.Key)
                             .AddParameter("Value", change.Value);
                        shell.Invoke();
                        if (shell.HadErrors)
                        {
                            throw new InvalidOperationException(shell.Streams.Error[0].ToString());
                        }
                    }
                }

                using (PowerShell shell = PowerShell.Create())
                {
                    shell.Runspace = runspace;
                    shell.AddScript(ResetServerSideScript);
                    shell.Invoke();
                }
            }

            // Let the session finish so the reset loop has cleared the IsServerSide flag before we return.
            Thread.Sleep(300);
        }

        //
        // Establishing a pipe connection causes PowerShell to set the NativeCommandProcessor.IsServerSide internal
        // flag. When the pipe connection is closed, PowerShell will asynchronously set
        // NativeCommandProcessor.IsServerSide flag again during the pipe cleanup routine. While IsServerSide == true,
        // PowerShell captures stderr from every native command. If stderr is not empty, then PowerShell throws a
        // NativeCommandError. This code snippet clears IsServerSide repeatedly for a 3 seconds using a local
        // runspace in the target PowerShell process.
        //
        private const string ResetServerSideScript =
            "try {" +
            " $d = [AppDomain]::CurrentDomain; $p = $d.GetData('EdkClangReset');" +
            " if (-not $p) { $r = [runspacefactory]::CreateRunspace(); $r.Open(); $p = [powershell]::Create(); $p.Runspace = $r; $d.SetData('EdkClangReset', $p) }" +
            " if ($p.InvocationStateInfo.State -eq 'Running') { $p.Stop() }" +
            " $p.Commands.Clear();" +
            " [void]$p.AddScript(\"`$f = [psobject].Assembly.GetType('System.Management.Automation.NativeCommandProcessor').GetProperty('IsServerSide', [Reflection.BindingFlags]'NonPublic,Public,Static');" +
            " 1..60 | ForEach-Object { `$f.SetValue(`$null, `$false); Start-Sleep -Milliseconds 50 }\");" +
            " [void]$p.BeginInvoke()" +
            " } catch { }";
    }
}
