@echo off
REM @file
REM build_selfextract.bat
REM
REM Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
REM SPDX-License-Identifier: BSD-2-Clause-Patent
REM

rem This script will modify the version information
rem on the self extracting exe, build the 7-zip
rem archive, and pack it into the exe.  It will
rem also delete all intermediate files when finished

copy 7zS-original.sfx 7zS.sfx
call set_version.bat
del set_version.bat

rem Compress the EXE using UPX, this will reduce the self
rem extractor's overhead on the archive by about 50%
upx -9 7zS.sfx

rem Third Step - compact the executable, the config file
rem and the archive together to make the final executable
copy /b 7zS.sfx + config.txt + setup-package.7z ..\dist\setup.exe
del 7zS.sfx
del setup-package.7z
