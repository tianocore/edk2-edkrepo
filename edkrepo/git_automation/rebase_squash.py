#!/usr/bin/env python3
#
## @file
# rebase_squash.py
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import re

def main():
    with open(sys.argv[1], 'r', errors="surrogateescape") as f:
        lines = f.readlines()
    r = re.compile("^pick(.*)$")
    with open(sys.argv[1], 'w', encoding="utf-8", errors="backslashreplace") as f:
        f.write(lines[0])
        for i in range(1,len(lines)):
            m = r.match(lines[i])
            if m: f.write("s {}\n".format(m.group(1)))
            else: f.write(lines[i])
if __name__ == "__main__":
    main()
