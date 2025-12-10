@echo off
REM @file
REM build_windows_installer.bat
REM
REM Copyright (c) 2017 - 2025, Intel Corporation. All rights reserved.<BR>
REM SPDX-License-Identifier: BSD-2-Clause-Patent
REM

REM
REM Step 1 - Setup Visual Studio Build Environment
REM
setlocal ENABLEDELAYEDEXPANSION
set SCRIPT_ERROR=0

set FIND_VS_WHERE=0
if not defined TOOL_CHAIN_TAG (
  set FIND_VS_WHERE=1
) else (
  if /I "%TOOL_CHAIN_TAG%"=="VS2022" (
    set FIND_VS_WHERE=1
  )
  if /I "%TOOL_CHAIN_TAG%"=="VS2019" (
    set FIND_VS_WHERE=1
  )
  if /I "%TOOL_CHAIN_TAG%"=="VS2017" (
    set FIND_VS_WHERE=1
  )
)
if %FIND_VS_WHERE% NEQ 0 (
  if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
    set "VS_WHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
    goto VS2017PlusCheck
  ) else if exist "%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe" (
    set "VS_WHERE=%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe"
    goto VS2017PlusCheck
  ) else (
    goto VS2017PlusCheckDone
  )
) else (
  goto VS2017PlusCheckDone
)

:VS2017PlusCheck

if defined VS170COMNTOOLS (
  set TOOL_CHAIN_TAG=VS2022
)
if defined VS160COMNTOOLS (
  set TOOL_CHAIN_TAG=VS2019
)
if defined VS150COMNTOOLS (
  set TOOL_CHAIN_TAG=VS2017
)

set CHECK_VS2022=0
if not defined TOOL_CHAIN_TAG (
  set CHECK_VS2022=1
) else (
  if /I "%TOOL_CHAIN_TAG%"=="VS2022" (
    set CHECK_VS2022=1
  )
)
if %CHECK_VS2022% NEQ 0 (
  for /f "usebackq tokens=1* delims=: " %%i in (`"%VS_WHERE%" -version [17.0^,18.0^)`) do (
    if /i "%%i"=="installationPath" set INSTALL_PATH=%%j
  )
)
if %CHECK_VS2022% NEQ 0 (
  if defined INSTALL_PATH (
    echo.
    echo Prebuild:  Set the VS2022 environment.
    echo.
    if not defined VS170COMNTOOLS (
      call "%INSTALL_PATH%\VC\Auxiliary\Build\vcvars32.bat"
    )
    set TOOL_CHAIN_TAG=VS2022
  )
)

set CHECK_VS2019=0
if not defined TOOL_CHAIN_TAG (
  set CHECK_VS2019=1
) else (
  if /I "%TOOL_CHAIN_TAG%"=="VS2019" (
    set CHECK_VS2019=1
  )
)
if %CHECK_VS2019% NEQ 0 (
  for /f "usebackq tokens=1* delims=: " %%i in (`"%VS_WHERE%" -version [16.0^,17.0^)`) do (
    if /i "%%i"=="installationPath" set INSTALL_PATH=%%j
  )
)
if %CHECK_VS2019% NEQ 0 (
  if defined INSTALL_PATH (
    echo.
    echo Prebuild:  Set the VS2019 environment.
    echo.
    if not defined VS160COMNTOOLS (
      call "%INSTALL_PATH%\VC\Auxiliary\Build\vcvars32.bat"
    )
    set TOOL_CHAIN_TAG=VS2019
  )
)

set CHECK_VS2017=0
if not defined TOOL_CHAIN_TAG (
  set CHECK_VS2017=1
) else (
  if /I "%TOOL_CHAIN_TAG%"=="VS2017" (
    set CHECK_VS2017=1
  )
)
if %CHECK_VS2017% NEQ 0 (
  for /f "usebackq tokens=1* delims=: " %%i in (`"%VS_WHERE%" -version [15.0^,16.0^)`) do (
    if /i "%%i"=="installationPath" set INSTALL_PATH=%%j
  )
)
if %CHECK_VS2017% NEQ 0 (
  if defined INSTALL_PATH (
    echo.
    echo Prebuild:  Set the VS2017 environment.
    echo.
    if not defined VS150COMNTOOLS (
      call "%INSTALL_PATH%\VC\Auxiliary\Build\vcvars32.bat"
    )
    set TOOL_CHAIN_TAG=VS2017
  )
)

:VS2017PlusCheckDone

if not defined TOOL_CHAIN_TAG (
  if defined VS140COMNTOOLS (
    set TOOL_CHAIN_TAG=VS2015
  )
)
if /I "%TOOL_CHAIN_TAG%"=="VS2015" (
  echo.
  echo Prebuild:  Set the VS2015 environment.
  echo.
  if not defined VSINSTALLDIR call "%VS140COMNTOOLS%\vsvars32.bat"
)
if not defined TOOL_CHAIN_TAG (
  echo Unable to locate a Visual Studio installation.
  set SCRIPT_ERROR=1
  goto End
)

REM
REM Step 2 - Make sure existing dist folder is clean
REM
if exist ..\dist (
  pushd ..\dist
  del /F EdkRepoSetup*.exe
  del /F *.whl
  rmdir /S /Q self_extract
  popd
)

REM
REM Step 3 - Set Version Numbers and build wheels
REM
py -3 set_version_and_build_wheels.py
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)

REM
REM Step 4 - Build C++/C# installer code
REM
pushd ..\edkrepo_installer
MSBuild edkrepo-installer.sln /m /t:Rebuild /p:Configuration=Release /p:Platform="Mixed Platforms"
if errorlevel 1 (
  popd
  set SCRIPT_ERROR=1
  goto End
)
popd

REM
REM Step 5 - All other needed files
REM
xcopy /S /Y ..\edkrepo_installer\Vendor ..\dist\self_extract
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)

copy /B /Y ..\edkrepo_installer\EdkRepoInstaller\bin\Release\EdkRepoInstaller.exe ..\dist\self_extract
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)
copy /B /Y ..\edkrepo_installer\EdkRepoInstallerConfig.xml ..\dist\self_extract
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)
copy /B /Y ..\edkrepo_installer\sha_data.cfg ..\dist\self_extract
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)

REM
REM Step 6 - Create 7-Zip archive
REM
del /F ..\edkrepo_installer\SelfExtract\setup-package.7z
..\edkrepo_installer\SelfExtract\7za a -mx9 -ms=on -m0=LZMA2 -mmt=off ..\edkrepo_installer\SelfExtract\setup-package.7z ..\dist\self_extract\*
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)
rmdir /S /Q ..\dist\self_extract

REM
REM Step 7 - Generate packed .exe
REM
cd ..\edkrepo_installer\SelfExtract
call build_selfextract.bat
cd ..\..\build-scripts
if errorlevel 1 (
  set SCRIPT_ERROR=1
  goto End
)

REM
REM Step 8 - Rename setup.exe to EdkRepoInstaller-x.x.x.exe
REM
if exist final_copy.bat (
  call final_copy.bat
  del final_copy.bat
)

:End
@If %SCRIPT_ERROR% EQU 1 goto Fail
goto Done
:Fail
exit /b 1
:Done
