/** @file
  Program.cs

  Lists the installed edk2-clang versions and switches between them.
  Intended to be run through edkclang.cmd, which applies the environment changes
  to the active session.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Principal;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace TianoCore.EdkClang
{
    internal static class Program
    {
        private const string WriteSystemDefaultSwitch = "--write-system-default";
        private const int ErrorCancelled = 1223;

        // A major version (20) or major.minor version (20.1), which selects the newest installed version it matches.
        private static readonly Regex PartialVersionPattern = new Regex(@"^\d+(\.\d+)?$", RegexOptions.CultureInvariant);

        // Emit the tagged protocol to stdout for edkclang.cmd to interpret, see TaggedWriter for details.
        private static bool emitForCmd;

        private static TextWriter stdout;
        private static TextWriter stderr;

        // True if the --json argument is specified
        private static bool json;
        private static readonly JsonObject result = new JsonObject();

        // The max line length for cmd.exe is 8191 characters so long JSON strings must be broken into multiple lines.
        private const int MaxCmdJsonLength = 6000;

        private static int Main(string[] args)
        {
            List<string> arguments = new List<string>(args);
            if (arguments.Count > 0 && arguments[0].Equals("--emit-cmd", StringComparison.OrdinalIgnoreCase))
            {
                emitForCmd = true;
                arguments.RemoveAt(0);
            }
            json = arguments.RemoveAll(a => IsOption(a, "json")) > 0;
            if (json)
            {
                stderr = new StringWriter();
                stdout = stderr;
            }
            else if (emitForCmd)
            {
                stdout = new TaggedWriter("#OUT:");
                stderr = new TaggedWriter("#ERR:");
            }
            else
            {
                stdout = Console.Out;
                stderr = Console.Error;
            }

            int exitCode;
            try
            {
                exitCode = Run(arguments);
            }
            catch (Exception e)
            {
                stderr.WriteLine("edkclang: " + e.Message);
                exitCode = 1;
            }
            stdout.Flush();
            stderr.Flush();
            if (json)
            {
                WriteJson(exitCode);
            }
            if (emitForCmd)
            {
                Console.Out.WriteLine("#EXIT:" + exitCode);
            }
            return exitCode;
        }

        //
        // Implements the tagged protocol that edkclang.cmd uses to process the output of edkclang-core.exe. Every line
        // printed to stdout in --emit-cmd mode must use this protocol.
        //
        // The syntax for the tagged protocol is "TAG:text", where TAG tells edkclang.cmd what action to take:
        //
        //   Tag                 Wrapper action
        //   #OUT:text           echo to stdout
        //   #ERR:text           echo to stderr
        //   #OUTNL: / #ERRNL:   blank line, since for /f skips empty lines
        //   #ENV:NAME=VALUE     set "NAME=VALUE" (generic, not just BASETOOLS_MINGW_PATH)
        //   #SUBST:OLD|NEW      PATH / CLANG_BIN rewrite
        //   #EXIT:n             exit code
        //
        private sealed class TaggedWriter : TextWriter
        {
            private readonly string tag;
            private readonly System.Text.StringBuilder line = new System.Text.StringBuilder();

            public TaggedWriter(string tag)
            {
                this.tag = tag;
            }

            public override System.Text.Encoding Encoding
            {
                get { return Console.Out.Encoding; }
            }

            public override void Write(char value)
            {
                if (value == '\n')
                {
                    Emit();
                }
                else if (value != '\r')
                {
                    line.Append(value);
                }
            }

            public override void Flush()
            {
                if (line.Length > 0)
                {
                    Emit();
                }
            }

            private void Emit()
            {
                Console.Out.WriteLine(line.Length == 0 ? tag.TrimEnd(':') + "NL:" : tag + line);
                line.Clear();
            }
        }

        private static bool IsOption(string argument, string name)
        {
            return (argument.StartsWith("-", StringComparison.Ordinal) || argument.StartsWith("/", StringComparison.Ordinal))
                && argument.TrimStart('-', '/').Equals(name, StringComparison.OrdinalIgnoreCase);
        }

        private static void Info(string text)
        {
            if (!json)
            {
                stdout.WriteLine(text);
            }
        }

        private static void WriteJson(int exitCode)
        {
            List<string> lines = stderr.ToString()
                .Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries).ToList();

            JsonObject document = new JsonObject();
            document.Add("exitCode", exitCode);
            foreach (KeyValuePair<string, object> entry in result)
            {
                document.Add(entry.Key, entry.Value);
            }
            if (exitCode != 0)
            {
                string first = lines.Count > 0 ? lines[0] : "edkclang failed.";
                document.Add("error", first.StartsWith("edkclang: ", StringComparison.Ordinal) ? first.Substring(10) : first);
            }
            document.Add("messages", lines);

            string text = document.ToJson(false);
            if (emitForCmd && text.Length > MaxCmdJsonLength)
            {
                text = document.ToJson(true);
            }
            TextWriter destination = emitForCmd ? new TaggedWriter("#OUT:") : Console.Out;
            destination.WriteLine(text);
            destination.Flush();
        }

        private sealed class JsonObject : List<KeyValuePair<string, object>>
        {
            public void Add(string key, object value)
            {
                Add(new KeyValuePair<string, object>(key, value));
            }

            public string ToJson(bool indent)
            {
                System.Text.StringBuilder builder = new System.Text.StringBuilder();
                AppendValue(builder, this, indent, 0);
                return builder.ToString();
            }

            private static void AppendBreak(System.Text.StringBuilder builder, bool indent, int level)
            {
                if (indent)
                {
                    builder.Append('\n').Append(' ', level * 2);
                }
            }

            private static void AppendValue(System.Text.StringBuilder builder, object value, bool indent, int level)
            {
                if (value == null)
                {
                    builder.Append("null");
                }
                else if (value is string)
                {
                    AppendString(builder, (string)value);
                }
                else if (value is bool)
                {
                    builder.Append((bool)value ? "true" : "false");
                }
                else if (value is int)
                {
                    builder.Append(((int)value).ToString(System.Globalization.CultureInfo.InvariantCulture));
                }
                else if (value is JsonObject)
                {
                    builder.Append('{');
                    bool first = true;
                    foreach (KeyValuePair<string, object> entry in (JsonObject)value)
                    {
                        builder.Append(first ? "" : ",");
                        first = false;
                        AppendBreak(builder, indent, level + 1);
                        AppendString(builder, entry.Key);
                        builder.Append(indent ? ": " : ":");
                        AppendValue(builder, entry.Value, indent, level + 1);
                    }
                    if (!first)
                    {
                        AppendBreak(builder, indent, level);
                    }
                    builder.Append('}');
                }
                else
                {
                    builder.Append('[');
                    bool first = true;
                    foreach (object item in (System.Collections.IEnumerable)value)
                    {
                        builder.Append(first ? "" : ",");
                        first = false;
                        AppendBreak(builder, indent, level + 1);
                        AppendValue(builder, item, indent, level + 1);
                    }
                    if (!first)
                    {
                        AppendBreak(builder, indent, level);
                    }
                    builder.Append(']');
                }
            }

            // Non-ASCII characters are escaped so the text works with any console code page.
            private static void AppendString(System.Text.StringBuilder builder, string text)
            {
                builder.Append('"');
                foreach (char c in text)
                {
                    switch (c)
                    {
                        case '"': builder.Append("\\\""); break;
                        case '\\': builder.Append("\\\\"); break;
                        case '\n': builder.Append("\\n"); break;
                        case '\r': builder.Append("\\r"); break;
                        case '\t': builder.Append("\\t"); break;
                        default:
                            if (c < 0x20 || c > 0x7E)
                            {
                                builder.Append("\\u").Append(((int)c).ToString("x4", System.Globalization.CultureInfo.InvariantCulture));
                            }
                            else
                            {
                                builder.Append(c);
                            }
                            break;
                    }
                }
                builder.Append('"');
            }
        }

        private static int Run(List<string> arguments)
        {
            string exePath = Assembly.GetExecutingAssembly().Location;
            string toolsDirectory = Path.GetDirectoryName(exePath);
            if (!Path.GetFileName(toolsDirectory).Equals(EdkClangLayout.ToolsDirectoryName, StringComparison.OrdinalIgnoreCase))
            {
                stderr.WriteLine("edkclang: this program must run from the 'tools' folder of an edk2-clang installation.");
                return 1;
            }
            string root = Path.GetDirectoryName(toolsDirectory);

            if (arguments.Count == 2 && arguments[0] == WriteSystemDefaultSwitch)
            {
                return WriteSystemDefault(root, arguments[1]);
            }

            string version = null;
            bool list = arguments.Count == 0;
            bool global = false;
            bool system = false;
            bool clearGlobal = false;
            foreach (string argument in arguments)
            {
                if (argument.StartsWith("-", StringComparison.Ordinal) || argument.StartsWith("/", StringComparison.Ordinal))
                {
                    switch (argument.TrimStart('-', '/').ToLowerInvariant())
                    {
                        case "global":
                        case "g":
                            global = true;
                            break;
                        case "system":
                        case "s":
                            system = true;
                            break;
                        case "clear-global":
                            clearGlobal = true;
                            break;
                        case "list":
                        case "l":
                            list = true;
                            break;
                        case "help":
                        case "h":
                        case "?":
                            result.Add("command", "help");
                            PrintUsage(stdout);
                            return 0;
                        default:
                            stderr.WriteLine("edkclang: unknown option '" + argument + "'.");
                            PrintUsage(stderr);
                            return 1;
                    }
                }
                else if (argument.Equals("list", StringComparison.OrdinalIgnoreCase))
                {
                    list = true;
                }
                else if (version == null)
                {
                    version = argument;
                }
                else
                {
                    stderr.WriteLine("edkclang: unexpected argument '" + argument + "'.");
                    PrintUsage(stderr);
                    return 1;
                }
            }

            if (clearGlobal && global)
            {
                stderr.WriteLine("edkclang: --clear-global cannot be combined with --global.");
                return 1;
            }
            if (version == null)
            {
                if (global || system)
                {
                    stderr.WriteLine("edkclang: --global and --system need a version, for example: edkclang 20.1.8 --global");
                    return 1;
                }
                if (clearGlobal)
                {
                    if (list)
                    {
                        stderr.WriteLine("edkclang: 'list' cannot be combined with --clear-global.");
                        return 1;
                    }
                    result.Add("command", "clear-global");
                    ClearUserDefault(root);
                    return 0;
                }
                return ListVersions(root);
            }
            if (list)
            {
                stderr.WriteLine("edkclang: 'list' cannot be combined with a version.");
                return 1;
            }
            return SwitchVersion(root, exePath, version, global, system, clearGlobal);
        }

        private static void PrintUsage(TextWriter writer)
        {
            writer.WriteLine("Usage:");
            writer.WriteLine("  edkclang                       List the installed edk2-clang versions.");
            writer.WriteLine("  edkclang <version>             Use <version> in the current shell session.");
            writer.WriteLine("                                 A major version such as 20 selects the newest installed 20.x.y.");
            writer.WriteLine("  edkclang <version> --global    Also make <version> the current user's default.");
            writer.WriteLine("  edkclang <version> --system    Also make <version> the default for all users (admin rights needed).");
            writer.WriteLine("  edkclang --clear-global        Remove the current user's default, new shells use the system default.");
            writer.WriteLine("  edkclang ... --json            Print the results as JSON.");
        }

        // Removes the current user's override so new shells fall back to the system default; this shell is not changed.
        private static void ClearUserDefault(string root)
        {
            bool cleared = false;
            using (RegistryKey key = EdkClangLayout.OpenCurrentUserEnvironment(true))
            {
                if (key != null && EdkClangLayout.GetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName) != null)
                {
                    EdkClangLayout.DeleteEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
                    cleared = true;
                }
            }
            if (cleared)
            {
                EdkClangLayout.BroadcastEnvironmentChange();
            }

            string systemValue;
            using (RegistryKey key = EdkClangLayout.OpenMachineEnvironment(false))
            {
                systemValue = key == null ? null : EdkClangLayout.GetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
            }
            string systemVersion;
            if (!EdkClangLayout.TryGetVersionName(systemValue, root, out systemVersion))
            {
                systemVersion = null;
            }

            SetResult("userDefaultCleared", cleared);
            SetResult("systemDefault", systemValue);
            SetResult("systemDefaultVersion", systemVersion);
            Info(cleared ? "Current user's default edk2-clang version was removed." : "The current user does not have a default edk2-clang version set.");
            Info(systemValue == null
                ? "There is no system default either, so new shells will not have " + EdkClangLayout.BaseToolsMingwPathName + " set."
                : "New shells will use the system default" + (systemVersion == null ? " (" + systemValue + ")." : ", " + systemVersion + "."));
        }

        private static int ListVersions(string root)
        {
            List<InstalledVersion> versions = EdkClangLayout.EnumerateInstalledVersions(root);
            if (versions.Count == 0)
            {
                stderr.WriteLine("No edk2-clang versions are installed in " + root + ".");
                return 1;
            }

            string shellValue = Environment.GetEnvironmentVariable(EdkClangLayout.BaseToolsMingwPathName);
            string userValue;
            using (RegistryKey key = EdkClangLayout.OpenCurrentUserEnvironment(false))
            {
                userValue = key == null ? null : EdkClangLayout.GetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
            }
            string systemValue;
            using (RegistryKey key = EdkClangLayout.OpenMachineEnvironment(false))
            {
                systemValue = key == null ? null : EdkClangLayout.GetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName);
            }

            Info("Installed edk2-clang versions in " + root + ":");
            JsonObject[] entries = new JsonObject[versions.Count];
            int entryIndex = 0;
            foreach (InstalledVersion v in Enumerable.Reverse(versions))
            {
                List<string> tags = new List<string>();
                if (EdkClangLayout.IsSamePath(shellValue, v.FullPath))
                {
                    tags.Add("this shell");
                }
                if (EdkClangLayout.IsSamePath(userValue, v.FullPath))
                {
                    tags.Add("user default");
                }
                if (EdkClangLayout.IsSamePath(systemValue, v.FullPath))
                {
                    tags.Add("system default");
                }
                if (!v.IsComplete)
                {
                    tags.Add("incomplete");
                }
                Info(string.Format("  {0} {1}{2}",
                    tags.Contains("this shell") ? "*" : " ",
                    v.Name.PadRight(12),
                    tags.Count == 0 ? string.Empty : "(" + string.Join(", ", tags) + ")"));

                JsonObject entry = new JsonObject();
                entry.Add("version", v.Name);
                entry.Add("path", v.FullPath);
                entry.Add("complete", v.IsComplete);
                entry.Add("thisShell", tags.Contains("this shell"));
                entry.Add("userDefault", tags.Contains("user default"));
                entry.Add("systemDefault", tags.Contains("system default"));
                entries[entryIndex++] = entry;
            }

            List<string> warnings = new List<string>();
            string unused;
            if (!string.IsNullOrEmpty(userValue) && !EdkClangLayout.TryGetVersionName(userValue, root, out unused))
            {
                warnings.Add("Your user-level " + EdkClangLayout.BaseToolsMingwPathName + " is '" + userValue + "', which is not an installed version. It overrides the system default in every new shell.");
            }
            foreach (string warning in warnings)
            {
                Info(string.Empty);
                Info("Warning: " + warning);
            }

            result.Add("command", "list");
            result.Add("root", root);
            result.Add("versions", entries);
            result.Add("shellPath", shellValue);
            result.Add("userDefaultPath", userValue);
            result.Add("systemDefaultPath", systemValue);
            result.Add("warnings", warnings);
            return 0;
        }

        private static int SwitchVersion(string root, string exePath, string version, bool global, bool system, bool clearGlobal)
        {
            if (!EdkClangLayout.IsVersionName(version) && !PartialVersionPattern.IsMatch(version))
            {
                stderr.WriteLine("edkclang: '" + version + "' is not a version number such as 20.1.8, or a major version such as 20.");
                return 1;
            }
            InstalledVersion target = EdkClangLayout.EnumerateInstalledVersions(root)
                .Where(v => v.IsComplete && (v.Name == version || v.Name.StartsWith(version + ".", StringComparison.Ordinal)))
                .OrderByDescending(v => v.Version)
                .FirstOrDefault();
            if (target == null)
            {
                stderr.WriteLine("edkclang: version " + version + " is not installed. Run 'edkclang' to list the installed versions.");
                return 1;
            }
            version = target.Name;

            result.Add("command", "switch");
            result.Add("version", version);
            result.Add("path", target.FullPath);
            result.Add("userDefaultSet", false);
            result.Add("userDefaultCleared", false);
            result.Add("systemDefaultSet", false);
            result.Add("shellChanged", false);

            if (clearGlobal)
            {
                ClearUserDefault(root);
            }
            if (global)
            {
                using (RegistryKey key = EdkClangLayout.OpenCurrentUserEnvironment(true))
                {
                    EdkClangLayout.SetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName, target.FullPath);
                }
                EdkClangLayout.BroadcastEnvironmentChange();
                SetResult("userDefaultSet", true);
                Info("Your default edk2-clang is now " + version + ". New shells will use this version.");
            }
            if (system)
            {
                int systemResult = SetSystemDefault(root, exePath, version);
                if (systemResult != 0)
                {
                    return systemResult;
                }
                SetResult("systemDefaultSet", true);
            }

            int shellResult = ApplyToShell(root, target.FullPath);
            if (shellResult == 0)
            {
                SetResult("shellChanged", true);
                Info("This shell is now using edk2-clang " + version + ".");
            }
            return shellResult;
        }

        private static void SetResult(string key, object value)
        {
            int index = result.FindIndex(e => e.Key == key);
            if (index < 0)
            {
                result.Add(key, value);
                return;
            }
            result[index] = new KeyValuePair<string, object>(key, value);
        }

        private static int SetSystemDefault(string root, string exePath, string version)
        {
            if (IsElevated())
            {
                if (WriteSystemDefault(root, version) != 0)
                {
                    stderr.WriteLine("edkclang: version " + version + " is not installed.");
                    return 1;
                }
            }
            else
            {
                ProcessStartInfo start = new ProcessStartInfo(exePath, WriteSystemDefaultSwitch + " " + version)
                {
                    UseShellExecute = true,
                    Verb = "runas",
                    WindowStyle = ProcessWindowStyle.Hidden
                };
                try
                {
                    using (Process elevated = Process.Start(start))
                    {
                        elevated.WaitForExit();
                        if (elevated.ExitCode != 0)
                        {
                            stderr.WriteLine("edkclang: could not change the system default (exit code " + elevated.ExitCode + ").");
                            return 1;
                        }
                    }
                }
                catch (Win32Exception e)
                {
                    stderr.WriteLine(e.NativeErrorCode == ErrorCancelled
                        ? "edkclang: the system default was not changed because administrator approval was declined."
                        : "edkclang: could not start the elevated helper: " + e.Message);
                    return 1;
                }
            }
            Info("The system default edk2-clang is now " + version + ". New shells will use it.");
            return 0;
        }

        // Runs elevated. Re-validates the version because the argument crossed a process boundary.
        private static int WriteSystemDefault(string root, string version)
        {
            if (!EdkClangLayout.IsVersionName(version))
            {
                return 2;
            }
            InstalledVersion target = EdkClangLayout.EnumerateInstalledVersions(root).FirstOrDefault(v => v.Name == version);
            if (target == null || !target.IsComplete)
            {
                return 2;
            }
            using (RegistryKey key = EdkClangLayout.OpenMachineEnvironment(true))
            {
                EdkClangLayout.SetEnvironmentValue(key, EdkClangLayout.BaseToolsMingwPathName, target.FullPath);
            }
            EdkClangLayout.BroadcastEnvironmentChange();
            return 0;
        }

        private static bool IsElevated()
        {
            using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
            {
                return new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator);
            }
        }

        private static int ApplyToShell(string root, string versionDir)
        {
            ShellInfo shell = ShellDetector.FindControllingShell();
            if (shell.Kind == ShellKind.PowerShell)
            {
                return ApplyToPowerShell(shell, root, versionDir);
            }
            if (emitForCmd)
            {
                return EmitForCmd(root, versionDir) ? 0 : 1;
            }
            stderr.WriteLine("edkclang: shell was not changed. Run 'edkclang' from cmd.exe, PowerShell, or Git Bash.");
            return 0;
        }

        //
        // cmd.exe cannot handle Unicode, so only pass plain ASCII paths.
        //
        private static bool EmitForCmd(string root, string versionDir)
        {
            if (versionDir.Any(c => c > 0x7E || c < 0x20 || c == '"' || c == '%' || c == '=' || c == '|'))
            {
                stderr.WriteLine("edkclang: '" + versionDir + "' contains non-ASCII characters, which is unsupported by shell integration.");
                return false;
            }
            Console.Out.WriteLine("#ENV:" + EdkClangLayout.BaseToolsMingwPathName + "=" + versionDir);

            string currentVersion;
            string current = Environment.GetEnvironmentVariable(EdkClangLayout.BaseToolsMingwPathName);
            if (EdkClangLayout.TryGetVersionName(current, root, out currentVersion))
            {
                string from = Path.Combine(EdkClangLayout.NormalizePath(root), currentVersion);
                if (!EdkClangLayout.IsSamePath(from, versionDir))
                {
                    Console.Out.WriteLine("#SUBST:" + from + "|" + versionDir);
                }
            }
            return true;
        }

        private static int ApplyToPowerShell(ShellInfo shell, string root, string versionDir)
        {
            List<KeyValuePair<string, string>> changes =
                EdkClangLayout.ComputeShellEnvironment(root, versionDir, Environment.GetEnvironmentVariable);
            try
            {
                PowerShellPipe.ApplyEnvironment(shell.ProcessId, changes);
                return 0;
            }
            catch (Exception e)
            {
                string reason = e.Message.Split('\r', '\n')[0];
                stderr.WriteLine("edkclang: could not change this PowerShell session (" + reason + ").");
                stderr.WriteLine("Run edkclang from cmd.exe instead. Any --global or --system change above did take effect.");
                return 1;
            }
        }
    }
}
