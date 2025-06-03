@echo off
REM @file
REM cln.bat
REM
REM Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
REM SPDX-License-Identifier: BSD-2-Clause-Patent
REM

set SCRIPT_ERROR=0

where git.exe > NUL
if %ERRORLEVEL% EQU 0 (
    set GIT_FOUND=1
) else (
    set GIT_FOUND=0
)
if exist ..\.git (
  if %GIT_FOUND% NEQ 0 (
    set IS_GIT_REPO=1
  ) else (
    set IS_GIT_REPO=0
  )
) else (
  set IS_GIT_REPO=0
)

pushd ..\EdkMingwInstaller
rmdir /S /Q bin
rmdir /S /Q obj
if %IS_GIT_REPO% NEQ 0 (
  git checkout Properties/AssemblyInfo.cs
)
popd

if exist ..\dist (
  pushd ..\dist
  del /F EdkClangSetup*.exe
  rmdir /S /Q self_extract
  popd
)

:End
@If %SCRIPT_ERROR% EQU 1 goto Fail
goto Done
:Fail
exit /b 1
:Done
