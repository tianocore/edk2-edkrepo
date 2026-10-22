/** @file
  ReleaseFeed.cs

  Finds the EDK II Clang releases that are published on GitHub, and downloads one of them.

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Reflection;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace TianoCore.EdkClangSettings
{
    internal sealed class AvailableVersion
    {
        // The LLVM version, which is also the name of the folder it installs to.
        public string Version { get; set; }
        public Version Parsed { get; set; }
        public int Build { get; set; }
        public string AssetName { get; set; }
        public string DownloadUrl { get; set; }

        // Null if GitHub did not publish a digest for the asset.
        public string Sha256 { get; set; }
        public long Size { get; set; }
    }

    internal sealed class FeedException : Exception
    {
        public FeedException(string message) : base(message)
        {
        }

        public FeedException(string message, Exception inner) : base(message, inner)
        {
        }
    }

    [DataContract]
    internal sealed class GitHubAsset
    {
        [DataMember(Name = "name")]
        public string Name { get; set; }

        [DataMember(Name = "browser_download_url")]
        public string DownloadUrl { get; set; }

        [DataMember(Name = "digest")]
        public string Digest { get; set; }

        [DataMember(Name = "size")]
        public long Size { get; set; }
    }

    [DataContract]
    internal sealed class GitHubRelease
    {
        [DataMember(Name = "tag_name")]
        public string TagName { get; set; }

        [DataMember(Name = "draft")]
        public bool Draft { get; set; }

        [DataMember(Name = "prerelease")]
        public bool Prerelease { get; set; }

        [DataMember(Name = "assets")]
        public List<GitHubAsset> Assets { get; set; }
    }

    internal static class ReleaseFeed
    {
        private const string FirstPageUrl = "https://api.github.com/repos/tianocore/edk2-edkrepo/releases?per_page=100";
        private const string ApiUrlPrefix = "https://api.github.com/";
        private const string DownloadUrlPrefix = "https://github.com/tianocore/edk2-edkrepo/releases/download/";
        private const string TagPrefix = "edkclang-v";
        private const int MaxPages = 10;

        // The same repository also publishes EdkRepo releases, which do not match this name.
        private static readonly Regex AssetPattern =
            new Regex(@"^EdkClangSetup-(\d+\.\d+\.\d+)\.(\d+)\.exe$", RegexOptions.CultureInvariant);
        private static readonly Regex DigestPattern =
            new Regex(@"^sha256:([0-9a-fA-F]{64})$", RegexOptions.CultureInvariant);
        private static readonly Regex NextLinkPattern =
            new Regex(@"<([^>]+)>\s*;\s*rel=""next""", RegexOptions.CultureInvariant);

        private static readonly HttpClient Client = CreateClient();

        private static HttpClient CreateClient()
        {
            // .NET Framework 4.6.2 applications default to TLS 1.0, which GitHub does not accept.
            ServicePointManager.SecurityProtocol &= ~(SecurityProtocolType.Ssl3 | SecurityProtocolType.Tls | SecurityProtocolType.Tls11);
            ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;

            IWebProxy proxy = WebRequest.GetSystemWebProxy();
            proxy.Credentials = CredentialCache.DefaultCredentials;
            HttpClient client = new HttpClient(new HttpClientHandler { Proxy = proxy, UseProxy = true });
            client.Timeout = TimeSpan.FromMinutes(30);
            return client;
        }

        private static HttpRequestMessage CreateRequest(string url, bool api, string token = null)
        {
            HttpRequestMessage request = new HttpRequestMessage(HttpMethod.Get, url);
            // GitHub rejects requests without a User-Agent.
            request.Headers.UserAgent.ParseAdd("EdkClangSettings/" + Assembly.GetExecutingAssembly().GetName().Version);
            if (api)
            {
                request.Headers.Accept.ParseAdd("application/vnd.github+json");
                request.Headers.Add("X-GitHub-Api-Version", "2022-11-28");
                if (token != null)
                {
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                }
            }
            return request;
        }

        public static async Task<List<AvailableVersion>> FetchAsync(CancellationToken cancellation)
        {
            List<GitHubRelease> releases = new List<GitHubRelease>();
            string url = FirstPageUrl;
            // Authenticated requests have a much higher rate limit.
            string token = NetrcCredentials.FindGitHubToken();
            for (int page = 0; page < MaxPages && url != null; page++)
            {
                try
                {
                    using (HttpRequestMessage request = CreateRequest(url, true, token))
                    using (HttpResponseMessage response = await Client.SendAsync(request, cancellation).ConfigureAwait(false))
                    {
                        if (response.StatusCode == HttpStatusCode.Unauthorized && token != null)
                        {
                            // The token in the netrc file is invalid or expired, so ask again without it.
                            token = null;
                            page--;
                            continue;
                        }
                        if (response.StatusCode == HttpStatusCode.Forbidden || (int)response.StatusCode == 429)
                        {
                            IEnumerable<string> remaining;
                            bool limited = response.Headers.TryGetValues("X-RateLimit-Remaining", out remaining) &&
                                remaining.FirstOrDefault() == "0";
                            throw new FeedException(limited
                                ? "GitHub is limiting requests from this network. Try again later, or put a GitHub personal access token for api.github.com in your .netrc file."
                                : string.Format("GitHub returned HTTP {0} ({1}).", (int)response.StatusCode, response.ReasonPhrase));
                        }
                        response.EnsureSuccessStatusCode();
                        using (Stream stream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false))
                        {
                            DataContractJsonSerializer serializer = new DataContractJsonSerializer(typeof(List<GitHubRelease>));
                            releases.AddRange((List<GitHubRelease>)serializer.ReadObject(stream));
                        }
                        url = GetNextPageUrl(response);
                    }
                }
                catch (HttpRequestException e)
                {
                    throw new FeedException(e.Message, e);
                }
                catch (SerializationException e)
                {
                    throw new FeedException("GitHub returned data that could not be read.", e);
                }
            }
            return Parse(releases);
        }

        private static string GetNextPageUrl(HttpResponseMessage response)
        {
            IEnumerable<string> values;
            if (!response.Headers.TryGetValues("Link", out values))
            {
                return null;
            }
            Match match = NextLinkPattern.Match(string.Join(",", values));
            return match.Success && match.Groups[1].Value.StartsWith(ApiUrlPrefix, StringComparison.Ordinal)
                ? match.Groups[1].Value
                : null;
        }

        // Keeps the newest build of each EDK II Clang version that is a published (not draft, not preview) release.
        public static List<AvailableVersion> Parse(IEnumerable<GitHubRelease> releases)
        {
            Dictionary<string, AvailableVersion> newest = new Dictionary<string, AvailableVersion>(StringComparer.Ordinal);
            foreach (GitHubRelease release in releases)
            {
                if (release == null || release.Draft || release.Prerelease || release.Assets == null ||
                    release.TagName == null || !release.TagName.StartsWith(TagPrefix, StringComparison.Ordinal))
                {
                    continue;
                }
                foreach (GitHubAsset asset in release.Assets)
                {
                    if (asset == null || asset.Name == null || asset.DownloadUrl == null)
                    {
                        continue;
                    }
                    Match name = AssetPattern.Match(asset.Name);
                    Version parsed;
                    if (!name.Success ||
                        !asset.DownloadUrl.StartsWith(DownloadUrlPrefix, StringComparison.Ordinal) ||
                        !TianoCore.EdkClang.EdkClangLayout.TryParseVersion(name.Groups[1].Value, out parsed))
                    {
                        continue;
                    }
                    int build = int.Parse(name.Groups[2].Value);
                    AvailableVersion existing;
                    if (newest.TryGetValue(name.Groups[1].Value, out existing) && existing.Build >= build)
                    {
                        continue;
                    }
                    Match digest = DigestPattern.Match(asset.Digest ?? string.Empty);
                    newest[name.Groups[1].Value] = new AvailableVersion
                    {
                        Version = name.Groups[1].Value,
                        Parsed = parsed,
                        Build = build,
                        AssetName = asset.Name,
                        DownloadUrl = asset.DownloadUrl,
                        Sha256 = digest.Success ? digest.Groups[1].Value.ToLowerInvariant() : null,
                        Size = asset.Size
                    };
                }
            }
            return newest.Values.OrderByDescending(v => v.Parsed).ToList();
        }

        //
        // Downloads the installer to destination. The file is deleted unless it matches the SHA-256 digest that GitHub
        // published for it.
        //
        public static async Task DownloadAsync(
            AvailableVersion version, string destination, IProgress<Tuple<long, long>> progress, CancellationToken cancellation)
        {
            if (version.Sha256 == null)
            {
                throw new FeedException("GitHub did not publish a SHA-256 digest for this release, so it cannot be verified.");
            }
            if (!version.DownloadUrl.StartsWith(DownloadUrlPrefix, StringComparison.Ordinal))
            {
                throw new FeedException("The download address is not on github.com.");
            }

            string actual;
            try
            {
                using (HttpRequestMessage request = CreateRequest(version.DownloadUrl, false))
                using (HttpResponseMessage response = await Client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellation).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();
                    long total = response.Content.Headers.ContentLength ?? version.Size;
                    using (Stream source = await response.Content.ReadAsStreamAsync().ConfigureAwait(false))
                    using (FileStream target = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None))
                    using (SHA256 hash = new SHA256CryptoServiceProvider())
                    {
                        byte[] buffer = new byte[81920];
                        long received = 0;
                        int read;
                        while ((read = await source.ReadAsync(buffer, 0, buffer.Length, cancellation).ConfigureAwait(false)) > 0)
                        {
                            received += read;
                            if (version.Size > 0 && received > version.Size)
                            {
                                throw new FeedException("The download is larger than GitHub reported.");
                            }
                            hash.TransformBlock(buffer, 0, read, null, 0);
                            await target.WriteAsync(buffer, 0, read, cancellation).ConfigureAwait(false);
                            progress.Report(Tuple.Create(received, total));
                        }
                        hash.TransformFinalBlock(buffer, 0, 0);
                        actual = BitConverter.ToString(hash.Hash).Replace("-", string.Empty).ToLowerInvariant();
                    }
                }
            }
            catch (HttpRequestException e)
            {
                TryDelete(destination);
                throw new FeedException(e.Message, e);
            }
            catch
            {
                TryDelete(destination);
                throw;
            }

            if (!string.Equals(actual, version.Sha256, StringComparison.Ordinal))
            {
                TryDelete(destination);
                throw new InvalidDataException("The downloaded file does not match the SHA-256 digest that GitHub published for it.");
            }
        }

        private static void TryDelete(string path)
        {
            try
            {
                File.Delete(path);
            }
            catch (IOException)
            {
            }
            catch (UnauthorizedAccessException)
            {
            }
        }
    }
}
