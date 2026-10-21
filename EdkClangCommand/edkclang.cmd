@echo off
REM @file
REM edkclang.cmd
REM
REM Lists the installed edk2-clang versions and switches the current session between them.
REM Depends on edkclang-core.exe.
REM
REM Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
REM SPDX-License-Identifier: BSD-2-Clause-Patent
REM

set "EDKCLANG_FROM="
set "EDKCLANG_TO="
set "EDKCLANG_RC=1"

REM Every line edkclang-core.exe prints is in "TAG:payload" format. The TAG value determines which action to take:
REM   #OUT / #ERR       text for stdout / stderr (#OUTNL / #ERRNL is an empty line, which for /f would skip)
REM   #ENV:NAME=VALUE   environment variable to set in this session
REM   #SUBST:OLD|NEW    replace OLD with NEW in PATH and CLANG_BIN
REM   #EXIT:CODE        the exit code
for /f "usebackq tokens=1* delims=:" %%A in (`""%~dp0edkclang-core.exe" --emit-cmd %*"`) do (
  if "%%A"=="#OUT" echo(%%B
  if "%%A"=="#OUTNL" echo(
  if "%%A"=="#ERR" >&2 echo(%%B
  if "%%A"=="#ERRNL" >&2 echo(
  if "%%A"=="#ENV" for /f "tokens=1* delims==" %%X in ("%%B") do set "%%X=%%Y"
  if "%%A"=="#SUBST" for /f "tokens=1,2 delims=|" %%X in ("%%B") do (set "EDKCLANG_FROM=%%X" & set "EDKCLANG_TO=%%Y")
  if "%%A"=="#EXIT" set "EDKCLANG_RC=%%B"
)


REM Swap the previous version for the new one in PATH and CLANG_BIN (set by edksetup.bat)
if defined EDKCLANG_FROM (
  call set "PATH=%%PATH:%EDKCLANG_FROM%=%EDKCLANG_TO%%%"
  if defined CLANG_BIN call set "CLANG_BIN=%%CLANG_BIN:%EDKCLANG_FROM%=%EDKCLANG_TO%%%"
)
set "EDKCLANG_FROM="
set "EDKCLANG_TO="

REM Ensure the exit code is retained when run through cmd /c
call :edkclang_exit %EDKCLANG_RC%
exit /b %errorlevel%

:edkclang_exit
set "EDKCLANG_RC="
exit /b %1
