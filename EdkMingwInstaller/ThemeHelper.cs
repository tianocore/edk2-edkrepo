/** @file
  ThemeHelper.cs

@copyright
  Copyright 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/
using System.Windows;
using System.Windows.Media;
using Wpf.Ui.Appearance;

namespace TianoCore.EdkMingwInstaller
{
    internal static class ThemeHelper
    {
        public static bool IsDarkTheme()
        {
            ApplicationTheme theme = ApplicationThemeManager.GetAppTheme();
            if (theme == ApplicationTheme.Dark)
            {
                return true;
            }
            if (theme == ApplicationTheme.HighContrast)
            {
                Color windowColor = SystemColors.WindowColor;
                double luminance = ((0.299 * windowColor.R) + (0.587 * windowColor.G) + (0.114 * windowColor.B)) / 255.0;
                return luminance < 0.5;
            }
            return false;
        }
    }
}
