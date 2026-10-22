/** @file
  ShieldIcon.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;

namespace TianoCore.EdkClangSettings
{
    internal static class ShieldIcon
    {
        private const uint SIID_SHIELD = 77;
        private const uint SHGSI_ICON = 0x100;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct SHSTOCKICONINFO
        {
            public uint cbSize;
            public IntPtr hIcon;
            public int iSysImageIndex;
            public int iIcon;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
            public string szPath;
        }

        [DllImport("shell32.dll")]
        private static extern int SHGetStockIconInfo(uint siid, uint flags, ref SHSTOCKICONINFO info);

        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr icon);

        // The shield Windows puts on buttons and links that need administrator approval, or null if it is unavailable.
        public static ImageSource Load()
        {
            SHSTOCKICONINFO info = new SHSTOCKICONINFO { cbSize = (uint)Marshal.SizeOf(typeof(SHSTOCKICONINFO)) };
            if (SHGetStockIconInfo(SIID_SHIELD, SHGSI_ICON, ref info) != 0 || info.hIcon == IntPtr.Zero)
            {
                return null;
            }
            try
            {
                ImageSource source = Imaging.CreateBitmapSourceFromHIcon(info.hIcon, Int32Rect.Empty, System.Windows.Media.Imaging.BitmapSizeOptions.FromEmptyOptions());
                source.Freeze();
                return source;
            }
            finally
            {
                DestroyIcon(info.hIcon);
            }
        }
    }
}
