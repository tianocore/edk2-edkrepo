This branch is for integrating the EdkRepo tool in to EDK2

# Introduction

EdkRepo is the multi-repository tool for EDK II firmware development. EdkRepo is built on top of git. It is intended to automate common developer workflows for projects that use more than one git repository. For example many of the new projects in the edk2-platforms repository require the user to clone several git repositories. EdkRepo makes it easier to set up and upstream changes for these projects. EdkRepo does not replace git, rather it provides higher level extensions that make it easier to work with git. EdkRepo is written in Python and is compatible with Python 3.5 or later.

# Build and Installation
## Linux Instructions
### Pre-Requisites
- Git 2.13.x or later
- Python 3.5 or later
- Python SetupTools
- Python Pip
### Ubuntu Specific Instructions
Tested versions: 18.04 LTS, 16.04 LTS
#### Install Dependencies (Ubuntu 16.04 & 18.04)
`sudo apt-get install git python3 python3-setuptools python3-pip`
#### Upgrade git (Ubuntu 16.04 LTS Only)
The version of git that is installed by default in Ubuntu 16.04 is too old for EdkRepo (16.04 includes git 2.7.4, the minimum is 2.13+). To upgrade git, run the following commands:

`sudo apt-add-repository ppa:git-core/ppa`

Press [ENTER] to confirm that you want to add the new repository.

`sudo apt-get update`

`sudo apt-get install git`

### OpenSUSE
`sudo zipper install git python3 python3-setuptools python3-pip`

### Install Process
Installing EdkRepo on Linux requires one to extract the tarball and run the included installer script.
1. Extract the archive using the following command
  `tar -xzvf edkrepo-<version>.tar.gz`
2. Run the installer script with elevated privileges
  `sudo ./install.py --user <username>`

The -v flag can be added for more verbose output if desired.

### Build Process
To build a EdkRepo distribution tarball, the Python wheel package is required in addition to the above dependencies. On Ubuntu, one can install it using:

`sudo apt-get install python3-wheel`

1. `cd build-scripts`
2. `./build_linux_installer.py`

### Install From Source
To install from source, one must have installedd using the tarball method above at least once in order to setup the EdkRepo configuration files. One this is done, one may use the standard distutils method to install EdkRepo from source:

`./setup.py install`

## Windows Instructions
### Pre-Requisites
- Git 2.13.x or later
- Python 3.5 or later

Git 2.16.2 is the version that has recieved the most validation, though any version of Git 2.13 or later works fine. If you want to install 2.16.2, here are some links:
- [Direct Link - Git for Windows 2.16.2 - 64 Bit](https://github.com/git-for-windows/git/releases/download/v2.16.2.windows.1/Git-2.16.2-64-bit.exe)
- [Direct Link - Git for Windows 2.16.2 - 32 Bit](https://github.com/git-for-windows/git/releases/download/v2.16.2.windows.1/Git-2.16.2-64-bit.exe)

Python 3.7 or later is recommended due to performance improvements. You can get Python from here: https://www.python.org/

### Install Process
1. Run the installer .exe
2. Click Install

### Build Process
#### Build Pre-Requisites
- Visual Studio 2015 or later with the C# language installed
- Python Wheel

Install Python wheel using the following:

`py -3 -m pip install wheel`

Open a command prompt and type the following:
1. `cd build-scripts`
2. `build_windows_installer.bat`

# Timeline
| Time | Event |
|:----:|:-----:|
| WW 26 2019 | Initial commit of EdkRepo |
|...|...|

# Branch Owners
- Ashley DeSimone <ashley.e.desimone@intel.com>
- Nate DeSimone <nathaniel.l.desimone@intel.com>

# Integration
EdkRepo could live in several places:
1. edk2-platforms
2. edk2-pytool-library
3. The edk2-toolenv repository proposed by Sean (assuming approval of Sean’s RFC)
4. A new, separate repository created for EdkRepo

This is a topic that requires community discussion to decide what the final location should be.

# Known Issues
| Issue | Status |
|:-----:|:------:|
|...|...|

# Related Links
- https://github.com/tianocore/edk2-platforms
