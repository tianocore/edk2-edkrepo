#!/usr/bin/env python3
#
## @file
# set_version_and_build_wheels.py
#
# Copyright (c) 2017 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import configparser
import fnmatch
import io
import shutil
import time
import re
from subprocess import call, check_call
from xml.etree import ElementTree

PYTHON_VERSION="3"

#
# Environment detection
#
WIN = "win"
MAC = "mac"
LINUX = "linux"
if sys.platform == "win32":
    ostype = WIN
elif sys.platform == "darwin":
    ostype = MAC
elif sys.platform.startswith("linux"):
    ostype = LINUX
elif os.name == "posix":
    print("Warning: Unrecognized UNIX OS... treating as Linux")
    ostype = LINUX
else:
    raise EnvironmentError("Unsupported OS")

setup_py_version_data = re.compile(r"\s*version='([\d.]+)',")
assembly_file_version_data = re.compile(r"\s*\[\s*assembly:\s*AssemblyFileVersion\s*\(\"([\d.]+)\"\)\s*\]")
version_number_data = re.compile(r"(\d+)\.(\d+)\.(\d+)\.(\d+)")
file_version_data = re.compile(r"FILEVERSION\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
product_version_data = re.compile(r"PRODUCTVERSION\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
file_version_string_data = re.compile(r"\s*VALUE\s*\"FileVersion\"\s*,\s*\"([\d.]+)\"")
product_version_string_data = re.compile(r"\s*VALUE\s*\"ProductVersion\"\s*,\s*\"([\d.]+)\"")
wheel_package = re.compile("^([^-]+)-")

def get_current_version_number():
    cfg_path = os.path.join(os.path.dirname(__file__), "version_numbers.ini")
    config = configparser.ConfigParser()
    config.read(cfg_path)
    initial_version = config['edkrepo']['version']
    if "BUILD_NUMBER" in os.environ:
        version = "{}.{}".format(initial_version, os.environ["BUILD_NUMBER"])
        package_version = initial_version
    else:
        version = "{}.0".format(initial_version)
        package_version = initial_version
    return (version, package_version)

def set_version_number_setup_py(package_version):
    file_path = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "setup.py")
    if os.path.isfile(file_path):
        newFile = []
        with open(file_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            data = setup_py_version_data.match(line.rstrip())
            if data:
                newFile.append("      version='{}',\n".format(package_version))
            else:
                newFile.append("{}\n".format(line.rstrip()))
        with open(file_path, "w") as f:
            f.writelines(newFile)

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

def _set_version_number_and_wheels_cr_tools_installer_config(package_version, wheels):
    file_path = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "edkrepo_installer")
    file_path = os.path.join(file_path, "EdkRepoInstallerConfig.xml")
    tree = ElementTree.parse(file_path)
    root = tree.getroot()
    for root_element in root:
        if root_element.tag == "SubstitutablePythons":
            for py_version in root_element:
                if py_version.tag == "Python":
                    present_wheels = []
                    for wheel in py_version:
                        if wheel.tag == "Wheel":
                            for found_wheel in wheels:
                                if wheel.attrib["Name"] == found_wheel[0]:
                                    wheel.attrib["Version"] = package_version
                                    wheel.attrib["Path"] = found_wheel[1]
                                    present_wheels.append(found_wheel[0])
                    for found_wheel in wheels:
                        if found_wheel[0] not in present_wheels:
                            ElementTree.SubElement(py_version, "Wheel",
                                                   {"Name": found_wheel[0],
                                                    "Path": found_wheel[1],
                                                    "Version": package_version,
                                                    "UninstallAllOtherCopies": "false"})
        elif root_element.tag == "Python":
            py_version = root_element
            present_wheels = []
            for wheel in py_version:
                if wheel.tag == "Wheel":
                    for found_wheel in wheels:
                        if wheel.attrib["Name"] == found_wheel[0]:
                            wheel.attrib["Version"] = package_version
                            wheel.attrib["Path"] = found_wheel[1]
                            present_wheels.append(found_wheel[0])
            for found_wheel in wheels:
                if found_wheel[0] not in present_wheels:
                    ElementTree.SubElement(py_version, "Wheel",
                                           {"Name": found_wheel[0],
                                            "Path": found_wheel[1],
                                            "Version": package_version,
                                            "UninstallAllOtherCopies": "false"})
    tree.write(file_path)
    print("Installer config regenerated successfully")

def set_version_number_setup_launcher_rc(version):
    data = version_number_data.match(version)
    if data:
        major = data.group(1)
        minor = data.group(2)
        bugfix = data.group(3)
        build = data.group(4)
    file_path = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "edkrepo_installer")
    file_path = os.path.join(file_path, "SetupLauncher")
    file_path = os.path.join(file_path, "SetupLauncher.rc")
    if os.path.isfile(file_path):
        newFile = []
        with open(file_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            line = line.rstrip()
            data = file_version_data.match(line)
            if data:
                newFile.append("FILEVERSION {}, {}, {}, {}\n".format(major, minor, bugfix, build))
            else:
                data = product_version_data.match(line)
                if data:
                    newFile.append("PRODUCTVERSION {}, {}, {}, {}\n".format(major, minor, bugfix, build))
                else:
                    data = file_version_string_data.match(line)
                    if data:
                        newFile.append("			VALUE \"FileVersion\", \"{}.{}.{}.{}\"\n".format(major, minor, bugfix, build))
                    else:
                        data = product_version_string_data.match(line)
                        if data:
                            newFile.append("			VALUE \"ProductVersion\", \"{}.{}.{}.{}\"\n".format(major, minor, bugfix, build))
                        else:
                            newFile.append("{}\n".format(line))
        with open(file_path, "w") as f:
            f.writelines(newFile)

def make_selfextract_version_script(version):
    file_path = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "edkrepo_installer")
    file_path = os.path.join(file_path, "SelfExtract")
    file_path = os.path.join(file_path, "set_version.bat")
    this_year = time.localtime(time.time())[0]
    with io.open(file_path, 'w', encoding='utf-8') as ver:
        ver.write('@echo off\n')
        ver.write('chcp 65001\n')
        ver.write('rcedit.exe 7zS.sfx --set-file-version "{}"\n'.format(version))
        ver.write('rcedit.exe 7zS.sfx --set-product-version "{}"\n'.format(version))
        ver.write('rcedit.exe 7zS.sfx --set-version-string CompanyName "TianoCore"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string FileDescription "EdkRepo Installer"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string FileVersion "{}"\n'.format(version))
        ver.write('rcedit.exe 7zS.sfx --set-version-string InternalName "This package created with 7-Zip, Copyright © 1999-2010 Igor Pavlov"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string LegalCopyright "Copyright © {} TianoCore Contributors"\n'.format(this_year))
        ver.write('rcedit.exe 7zS.sfx --set-version-string OriginalFilename "7zS.sfx.exe"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string ProductName "EdkRepo"\n')
        ver.write('rcedit.exe 7zS.sfx --set-version-string ProductVersion "{}"\n'.format(version))
        ver.write('chcp 437\n')
    print("VersionInfo script written to set_version.bat\n")

def build_wheels(extension_pkgs):
    dir_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    file_path = os.path.join(dir_path, "setup.py")
    if ostype == WIN:
        check_call('py -{} "{}" bdist_wheel'.format(PYTHON_VERSION, file_path), shell=True, cwd=dir_path)
    else:
        check_call('python{} "{}" bdist_wheel'.format(PYTHON_VERSION, file_path), shell=True, cwd=dir_path)
    for pkg in extension_pkgs:
        ext_dir_path = os.path.abspath(pkg)
        ext_file_path = os.path.join(ext_dir_path, 'setup.py')
        if ostype == WIN:
            check_call('py -{} "{}" bdist_wheel'.format(PYTHON_VERSION, ext_file_path), shell=True, cwd=ext_dir_path)
        else:
            check_call('python{} "{}" bdist_wheel'.format(PYTHON_VERSION, ext_file_path), shell=True, cwd=ext_dir_path)
    print("Wheels built successfully")

def copy_wheels_and_set_xml(package_version, extension_pkgs):
    dir_path = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "dist")
    dest_path = os.path.join(dir_path, "self_extract")
    if ostype == LINUX:
        dest_path = os.path.join(dest_path, 'wheels')
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path)
    wheels = []
    for file_name in os.listdir(dir_path):
        if fnmatch.fnmatch(file_name, "*.whl"):
            data = wheel_package.match(file_name)
            if data:
                wheels.append((data.group(1), file_name))
                _copy_file(os.path.join(dir_path, file_name), os.path.join(dest_path, file_name))
    for pkg in extension_pkgs:
        ext_dir_path = os.path.join(os.path.abspath(pkg), 'dist')
        for file_name in os.listdir(ext_dir_path):
            if fnmatch.fnmatch(file_name, "*.whl"):
                data = wheel_package.match(file_name)
                if data:
                    wheels.append((data.group(1), file_name))
                    _copy_file(os.path.join(ext_dir_path, file_name), os.path.join(dest_path, file_name))
    _set_version_number_and_wheels_cr_tools_installer_config(package_version, wheels)

def create_final_copy_script(version):
    if ostype == WIN:
        with open("final_copy.bat", "w") as f:
            f.write("pushd ..\\dist\n")
            f.write("ren \"setup.exe\" \"EdkRepoSetup-{}.exe\"\n".format(version))
            f.write("popd\n")
    elif ostype == LINUX:
        with open('final_copy.py', 'w') as f:
            f.write('#!/usr/bin/python3\n')
            f.write('import os, shutil, sys\n')
            f.write('dist_name = "edkrepo-{{}}".format("{}")\n'.format(version))
            f.write('installer_dir = "../dist/self_extract"\n')
            f.write('shutil.make_archive(os.path.join("..", "dist", dist_name), "gztar", installer_dir)\n')
        os.chmod('final_copy.py', 0o755)

def _copy_file(source, destination):
    if ostype == WIN:
        check_call("copy /B /Y \"{}\" \"{}\"".format(source, destination), shell=True)
    else:
        check_call("cp -f {} {}".format(source, destination), shell=True)

def make_version_cfg_file(version):
    if ostype == LINUX:
        cfg_src = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'edkrepo_installer', 'linux-scripts')
        install_cfg = configparser.ConfigParser(allow_no_value=True)
        install_cfg.read(os.path.join(cfg_src, 'install.cfg'))
        install_cfg['version']['installer_version'] = version
        with open(os.path.join(cfg_src, 'install.cfg'), 'w') as f:
            install_cfg.write(f)

def main():
    extension_pkgs = []
    print("Building Python packages and generating new version number...")
    (version, package_version) = get_current_version_number()
    set_version_number_setup_py(package_version)
    if ostype == WIN:
        set_version_number_assembly_info(version)
        set_version_number_setup_launcher_rc(version)
        make_selfextract_version_script(version)
    print("Version number generated and set successfully")
    build_wheels(extension_pkgs)
    copy_wheels_and_set_xml(package_version, extension_pkgs)
    make_version_cfg_file(version)
    create_final_copy_script(version)

if __name__ == "__main__":
    main()
