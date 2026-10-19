/** @file
  TianoCoreBranding.xaml.cs

@copyright
  Copyright 2019 - 2026 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace TianoCore.EdkMingwInstaller
{
    /// <summary>
    /// Interaction logic for TianoCoreBranding.xaml
    /// </summary>
    public partial class TianoCoreBranding : Grid
    {
        public TianoCoreBranding()
        {
            InitializeComponent();
        }

        public static Viewbox GetDefaultWelcomeSplash(bool dark)
        {
            TianoCoreBranding branding = new TianoCoreBranding();
            branding.Children.Remove(branding.WelcomeSplash);
            return dark ? RecolorForDarkTheme(branding.WelcomeSplash) : branding.WelcomeSplash;
        }

        public static Viewbox GetDefaultLogo(bool dark)
        {
            TianoCoreBranding branding = new TianoCoreBranding();
            branding.Children.Remove(branding.TianoCoreLogo);
            return dark ? RecolorForDarkTheme(branding.TianoCoreLogo) : branding.TianoCoreLogo;
        }

        //
        // Re-color the logo art for dark mode
        //
        private static Viewbox RecolorForDarkTheme(Viewbox source)
        {
            string xaml = XamlWriter.Save(source);
            xaml = xaml.Replace("#FF000000", "#FFFFFFFF");
            xaml = xaml.Replace("#FFBDE7FF", "#FF42484B");
            xaml = xaml.Replace("#FF9FD7F8", "#FF373D40");
            xaml = xaml.Replace("#FFFFD3B5", "#FF423C37");
            return (Viewbox)XamlReader.Parse(xaml);
        }
    }
}
