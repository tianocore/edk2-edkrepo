#!/bin/sh
#
## @file
# self_extract_header.sh
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# This is a self-extracting installer stub. A gzip-compressed tar archive
# containing the EdkRepo installer payload is appended immediately after the
# __EDKREPO_ARCHIVE__ marker line below. This script extracts that archive
# to a temporary directory, locates install.py inside it, and runs it,
# passing through any command line arguments given to this script.
#

set -u

cleanup() {
    if [ -n "${tmp_dir:-}" ] && [ -d "$tmp_dir" ]; then
        rm -rf "$tmp_dir"
    fi
}
trap cleanup EXIT INT TERM

self="$0"

archive_line=$(awk '/^__EDKREPO_ARCHIVE__$/ { print NR + 1; exit }' "$self")
if [ -z "$archive_line" ]; then
    echo "Error: unable to locate embedded archive" >&2
    exit 1
fi

tmp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t edkrepo)
if [ -z "$tmp_dir" ] || [ ! -d "$tmp_dir" ]; then
    echo "Error: unable to create temporary directory" >&2
    exit 1
fi

tail -n "+${archive_line}" "$self" | tar xzf - -C "$tmp_dir"
if [ $? -ne 0 ]; then
    echo "Error: failed to extract embedded archive" >&2
    exit 1
fi

install_py=$(find "$tmp_dir" -maxdepth 2 -name install.py | head -n 1)
if [ -z "$install_py" ]; then
    echo "Error: unable to locate install.py in extracted archive" >&2
    exit 1
fi

install_dir=$(dirname "$install_py")
cd "$install_dir" || exit 1
chmod +x ./install.py 2>/dev/null

./install.py "$@"
status=$?

exit "$status"

__EDKREPO_ARCHIVE__
