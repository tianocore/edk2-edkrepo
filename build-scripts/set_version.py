#!/usr/bin/env python3
#
## @file
# set_version.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import configparser
import fnmatch
import io
#import shutil
import time
import re
from subprocess import call, check_call


assembly_file_version_data = re.compile(r"\s*\[\s*assembly:\s*AssemblyFileVersion\s*\(\"([\d.]+)\"\)\s*\]")

def get_current_version_number():
    cfg_path = os.path.join(os.path.dirname(__file__), "version_numbers.ini")
    config = configparser.ConfigParser()
    config.read(cfg_path)
    initial_version = config['edkclang']['version']
    if "BUILD_NUMBER" in os.environ:
        version = "{}.{}".format(initial_version, os.environ["BUILD_NUMBER"])
        package_version = initial_version
    else:
        version = "{}.0".format(initial_version)
        package_version = initial_version
    return (version, package_version)

def set_version_number_assembly_info(version):
    assembly_info_files = []
    for root, _, filenames in os.walk(".."):
        for filename in filenames:
            if fnmatch.fnmatch(filename, "AssemblyInfo.cs"):
                assembly_info_files.append(os.path.join(root, filename))
    for file_path in assembly_info_files:
        newFile = []
        with open(file_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            data = assembly_file_version_data.match(line.rstrip())
            if data:
                newFile.append("[assembly: AssemblyFileVersion(\"{}\")]\n".format(version))
            else:
                newFile.append("{}\n".format(line.rstrip()))
        with open(file_path, "w") as f:
            f.writelines(newFile)

def make_selfextract_version_script(version):
    file_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    file_path = os.path.join(file_path, "SelfExtract")
    file_path = os.path.join(file_path, "set_version.bat")
    this_year = time.localtime(time.time())[0]
    with io.open(file_path, 'w', encoding='utf-8') as ver:
        ver.write('@echo off\n')
        ver.write('chcp 65001\n')
        ver.write('rcedit.exe 7zS.sfx --set-file-version "{}"\n'.format(version))
        ver.write('rcedit.exe 7zS.sfx --set-product-version "{}"\n'.format(version))
        ver.write('rcedit.exe 7zS.sfx --set-version-string CompanyName "TianoCore"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string FileDescription "EDK II Clang Mingw-w64 for Windows Installer"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string FileVersion "{}"\n'.format(version))
        ver.write('rcedit.exe 7zS.sfx --set-version-string InternalName "This package created with 7-Zip, Copyright © 1999-2024 Igor Pavlov"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string LegalCopyright "Copyright © {} TianoCore Contributors"\n'.format(this_year))
        ver.write('rcedit.exe 7zS.sfx --set-version-string OriginalFilename "7zS.sfx.exe"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string ProductName "EDK II Clang Mingw-w64"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string ProductVersion "{}"\n'.format(version))
        ver.write('chcp 437\n')
    print("VersionInfo script written to set_version.bat\n")

def create_final_copy_script(version):
    with open("final_copy.bat", "w") as f:
        f.write("pushd ..\\dist\n")
        f.write("ren \"setup.exe\" \"EdkClangSetup-{}.exe\"\n".format(version))
        f.write("popd\n")

def _copy_file(source, destination):
    check_call("copy /B /Y \"{}\" \"{}\"".format(source, destination), shell=True)

def main():
    print("Building Python packages and generating new version number...")
    (version, package_version) = get_current_version_number()
    set_version_number_assembly_info(version)
    make_selfextract_version_script(version)
    print("Version number generated and set successfully")
    create_final_copy_script(version)

if __name__ == "__main__":
    main()
