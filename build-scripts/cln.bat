@echo off
REM @file
REM cln.bat
REM
REM Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
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

if exist .\__pycache__ (
  rmdir /S /Q __pycache__
)

pushd ..\edkrepo_installer
rmdir /S /Q EdkRepoInstaller\bin
rmdir /S /Q EdkRepoInstaller\obj
if %IS_GIT_REPO% NEQ 0 (
  git checkout EdkRepoInstaller/Properties/AssemblyInfo.cs
  git checkout EdkRepoInstallerConfig.xml
)
popd

if exist ..\dist (
  pushd ..\dist
  del /F EdkRepoSetup*.exe
  del /F *.whl
  del /F edkrepo*.tar.gz
  rmdir /S /Q self_extract
  popd
)

pushd ..
rmdir /S /Q build
rmdir /S /Q edkrepo.egg-info
popd

:End
@If %SCRIPT_ERROR% EQU 1 goto Fail
goto Done
:Fail
exit /b 1
:Done
