#!/usr/bin/env python3
#
## @file
# set_version.py
#
# Copyright (c) 2025 - 2026, Intel Corporation. All rights reserved.<BR>
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
import subprocess
from subprocess import call, check_call


assembly_file_version_data = re.compile(r"\s*\[\s*assembly:\s*AssemblyFileVersion\s*\(\"([\d.]+)\"\)\s*\]")
assembly_informational_version_data = re.compile(r"\s*\[\s*assembly:\s*AssemblyInformationalVersion\s*\(\"([\d.]+)\"\)\s*\]")
clang_version_data = re.compile(r"clang version (\d+\.\d+\.\d+)")

def get_clang_version(clang_path):
    """Returns the version that the packaged clang.exe reports, such as 22.1.8."""
    output = subprocess.run([clang_path, "--version"], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True, check=True).stdout
    match = clang_version_data.search(output)
    if not match:
        raise ValueError("could not parse the output of '{} --version'".format(clang_path))
    return match.group(1)

def get_current_version_number(clang_path):
    """Returns (version, engine_version, llvm_version).

    version         - LLVM version + build number; names the setup .exe and the SFX stub.
    engine_version  - installer engine version + build number; stamped as AssemblyFileVersion so the
                      installer can tell whether the uninstaller already on disk is newer.
    llvm_version    - the toolchain version reported by clang_path; stamped as
                      AssemblyInformationalVersion and used as the install folder name.
    """
    cfg_path = os.path.join(os.path.dirname(__file__), "version_numbers.ini")
    config = configparser.ConfigParser()
    config.read(cfg_path)
    llvm_version = get_clang_version(clang_path)
    engine_version = config['installer']['version']
    build_number = os.environ.get("BUILD_NUMBER", "0")
    return ("{}.{}".format(llvm_version, build_number),
            "{}.{}".format(engine_version, build_number),
            llvm_version)

def set_version_number_assembly_info(engine_version, llvm_version):
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
            if assembly_file_version_data.match(line.rstrip()):
                newFile.append("[assembly: AssemblyFileVersion(\"{}\")]\n".format(engine_version))
            elif assembly_informational_version_data.match(line.rstrip()):
                newFile.append("[assembly: AssemblyInformationalVersion(\"{}\")]\n".format(llvm_version))
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
    if len(sys.argv) != 2:
        print("Usage: set_version.py <path to the packaged clang.exe>")
        return 1
    print("Building Python packages and generating new version number...")
    try:
        (version, engine_version, llvm_version) = get_current_version_number(sys.argv[1])
    except (OSError, subprocess.CalledProcessError, ValueError) as e:
        print("ERROR: could not get the clang version: {}".format(e))
        return 1
    print("Packaged clang is version {}".format(llvm_version))
    set_version_number_assembly_info(engine_version, llvm_version)
    make_selfextract_version_script(version)
    print("Version number generated and set successfully")
    create_final_copy_script(version)
    return 0

if __name__ == "__main__":
    sys.exit(main())
