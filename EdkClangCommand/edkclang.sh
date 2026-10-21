#!/usr/bin/env bash
## @file
# edkclang.sh
#
# Git Bash version of edkclang. Lists the installed edk2-clang versions and switches the current shell
# between them. Depends on edkclang-core.exe, which must be on the PATH.
#
# This file must be sourced, since a program cannot change the environment of the shell that started it.
# It is sourced by /etc/profile.d, so the 'edkclang' function exists in every login shell.
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

# Replaces FROM with TO if ENTRY is FROM or is inside FROM. The comparison ignores case, as Windows paths do.
_edkclang_swap_entry() {
  local entry=$1 from=$2 to=$3
  if [[ ${entry,,} == "${from,,}" || ${entry,,} == "${from,,}"[/\\]* ]]; then
    entry=$to${entry:${#from}}
  fi
  printf '%s' "$entry"
}

# Applies _edkclang_swap_entry to every entry of the colon separated list PATH_LIST.
_edkclang_swap_path() {
  local list=$1 from=$2 to=$3 entry result= separator=
  local -a entries
  IFS=: read -ra entries <<< "$list"
  for entry in "${entries[@]}"; do
    result+=$separator$(_edkclang_swap_entry "$entry" "$from" "$to")
    separator=:
  done
  printf '%s' "$result"
}

edkclang() {
  local core line tag payload mode
  local rc=1 from= to=
  core=$(command -v edkclang-core.exe) || {
    echo "edkclang: edkclang-core.exe was not found on the PATH. Open a new shell, or reinstall edk2-clang." >&2
    return 1
  }

  # Every line edkclang-core.exe prints is in "TAG:payload" format. See edkclang.cmd for the meaning of the tags.
  while IFS= read -r line; do
    line=${line%$'\r'}
    tag=${line%%:*}
    payload=${line#*:}
    case $tag in
      '#OUT') printf '%s\n' "$payload" ;;
      '#OUTNL') echo ;;
      '#ERR') printf '%s\n' "$payload" >&2 ;;
      '#ERRNL') echo >&2 ;;
      '#ENV') export "$payload" ;;
      '#SUBST') from=${payload%%|*}; to=${payload#*|} ;;
      '#EXIT') rc=$payload ;;
    esac
  done < <("$core" --emit-cmd "$@")

  # Swap the previous version for the new one in PATH (POSIX paths) and CLANG_BIN (any path style)
  if [[ -n $from && -n $to ]]; then
    PATH=$(_edkclang_swap_path "$PATH" "$(cygpath -u "$from")" "$(cygpath -u "$to")")
    if [[ -n ${CLANG_BIN-} ]]; then
      for mode in -u -m -w; do
        CLANG_BIN=$(_edkclang_swap_entry "$CLANG_BIN" "$(cygpath $mode "$from")" "$(cygpath $mode "$to")")
      done
    fi
  fi
  return "$rc"
}
