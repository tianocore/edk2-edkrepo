#!/usr/bin/env python3
#
## @file
# commit_msg.py
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os

def main():
    if 'COMMIT_MESSAGE_NO_EDIT' in os.environ:
        return
    with open(sys.argv[1], 'w', encoding="utf-8", errors="backslashreplace") as f:
        if 'COMMIT_MESSAGE' in os.environ:
            f.write(os.environ['COMMIT_MESSAGE'])
        else:
            f.write("Cherry Pick\n")
if __name__ == "__main__":
    main()
