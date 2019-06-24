/** @file
  CpuArchitecture.cs

@copyright
  Copyright 2016 - 2019 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TianoCore.EdkRepoInstaller
{
    public enum CpuArchitecture
    {
        IA32,
        X64,
        Unknown
    }
}
