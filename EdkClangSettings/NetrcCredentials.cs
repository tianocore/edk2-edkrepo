/** @file
  NetrcCredentials.cs

  Reads a GitHub personal access token from the user's _netrc or .netrc file.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace TianoCore.EdkClangSettings
{
    internal static class NetrcCredentials
    {
        // The token is only ever sent to the first host, but a github.com entry is accepted as well.
        private static readonly string[] Machines = { "api.github.com", "github.com" };
        private static readonly string[] FileNames = { ".netrc", "_netrc" };
        private const long MaxFileSize = 1024 * 1024;

        // Returns the password of the first matching machine entry, or null if there is none.
        public static string FindGitHubToken()
        {
            foreach (string directory in GetDirectories())
            {
                foreach (string name in FileNames)
                {
                    string token = ReadToken(Path.Combine(directory, name));
                    if (token != null)
                    {
                        return token;
                    }
                }
            }
            return null;
        }

        private static IEnumerable<string> GetDirectories()
        {
            HashSet<string> seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (string directory in new[]
            {
                Environment.GetEnvironmentVariable("HOME"),
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)
            })
            {
                if (!string.IsNullOrEmpty(directory) && seen.Add(directory))
                {
                    yield return directory;
                }
            }
        }

        private static string ReadToken(string path)
        {
            string text;
            try
            {
                FileInfo info = new FileInfo(path);
                if (!info.Exists || info.Length > MaxFileSize)
                {
                    return null;
                }
                text = File.ReadAllText(path);
            }
            catch (IOException)
            {
                return null;
            }
            catch (UnauthorizedAccessException)
            {
                return null;
            }
            catch (ArgumentException)
            {
                return null;
            }
            catch (NotSupportedException)
            {
                return null;
            }
            return ParseToken(text);
        }

        public static string ParseToken(string text)
        {
            string[] tokens = RemoveMacros(text).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
            for (int i = 0; i < tokens.Length; i++)
            {
                if (tokens[i] != "machine" || i + 1 >= tokens.Length ||
                    Array.FindIndex(Machines, m => string.Equals(m, tokens[i + 1], StringComparison.OrdinalIgnoreCase)) < 0)
                {
                    continue;
                }

                // The entry runs until the next machine, default or macdef keyword.
                for (int j = i + 2; j + 1 < tokens.Length; j += 2)
                {
                    if (tokens[j] == "machine" || tokens[j] == "default" || tokens[j] == "macdef")
                    {
                        break;
                    }
                    if (tokens[j] == "password" && tokens[j + 1].Length > 0)
                    {
                        return tokens[j + 1];
                    }
                }
            }
            return null;
        }

        // A macdef body runs to the next blank line and is not made of netrc tokens.
        private static string RemoveMacros(string text)
        {
            StringBuilder kept = new StringBuilder();
            bool inMacro = false;
            foreach (string line in text.Split('\n'))
            {
                string trimmed = line.Trim();
                if (inMacro)
                {
                    inMacro = trimmed.Length > 0;
                    continue;
                }
                if (trimmed.StartsWith("macdef", StringComparison.Ordinal) &&
                    (trimmed.Length == 6 || char.IsWhiteSpace(trimmed[6])))
                {
                    inMacro = true;
                    continue;
                }
                kept.Append(line).Append('\n');
            }
            return kept.ToString();
        }
    }
}
