# EdkRepo - The Multi-Repository Tool for EDK II

## Introduction

EdkRepo is the multi-repository tool for EDK II firmware development. EdkRepo is built on top of git. It is intended to automate common developer workflows for projects that use more than one git repository. For example many of the new projects in the edk2-platforms repository require the user to clone several git repositories. EdkRepo makes it easier to set up and upstream changes for these projects. EdkRepo does not replace git, rather it provides higher level extensions that make it easier to work with git. EdkRepo is written in Python and is compatible with Python 3.7 or later.

## Documentation

- [Users Guide](docs/edkrepo_users_guide.md)
- [Developer Documentation](docs/doc_index.md)

## Linux Build and Installation

### Install Pre-Requisites

- Git 2.24.x or later
- Python 3.7 or later
- Python SetupTools
- Python Pip

### Ubuntu/Debian Specific Instructions

Tested versions:

- Ubuntu 24.04 LTS, 22.04 LTS, 20.04 LTS
- Debian 13, 12

`sudo apt-get install git git-lfs python3 python3-setuptools python3-pip`

### OpenSUSE Specific Instructions

`sudo zipper install git python3 python3-setuptools python3-pip`

### Red Hat/Fedora/Rocky Specific Instructions

`sudo dnf install git python3-pip`

### Install EdkRepo on Linux

Installing EdkRepo on Linux requires one to extract the tarball and run the included installer script.

1. Extract the archive using the following command
  `tar -xzvf edkrepo-<version>.tar.gz`
2. Run the installer script `./install.py` and follow the on-screen prompts.

The -v flag can be added for more verbose output if desired.

### Automated Linux Installation

For an automated non-interactive install, one must provide at least 2 arguments: `--local` or `--system` and `--prompt` or `--no-prompt`.

`--local` requests installation to the current user's home directory. Root access is not required and no system wide changes are made. This is the **recommended** installation method.

`--system` request a system-wide installation. Root access is required. This method is useful for systems where multiple users will be running EdkRepo as it saves disk space in that scenario.

For system level installations, one must provide the `--user` parameter and run the installation script as root. The `--user` parameter can sometimes be needed when running in a container environment.

### Linux and macOS Build Process

To build a EdkRepo distribution tarball, the Python wheel package is required in addition to the above dependencies. On Ubuntu, one can install it using:

`sudo apt-get install python3-wheel`

Build the distribution tarball by running the following:

1. `cd build-scripts`
2. `./build_linux_installer.py`

### Install From Source on Linux or macOS

To install from source, one must have installed using the tarball method at least once in order to setup the EdkRepo configuration files. One this is done, one may use the standard distutils method to install EdkRepo from source:

`./setup.py install`

## macOS Build and Installation

### macOS Install Pre-Requisites

#### 1. Install the Xcode Command Line Tools

a) Open a Terminal and type the following command:

`xcode-select --install`

b) A new window will appear, click Install.
c) Accept the license agreement.
d) Wait for the installation to complete.

#### 2. Install Homebrew

Install [Homebrew](https://brew.sh/) if it has not been installed already. Homebrew is a package manager for macOS that has become the most common method of installing command line software on macOS that was not originally provided by Apple. EdkRepo has several dependencies that are distributed via Homebrew.

Type the following command to install Homebrew:

`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"`

Follow the on-screen prompts.

#### 3. Install Dependencies

Run the following commands to install EdkRepo's dependencies:

`brew install bash-completion git git-gui xz pyenv`

`pyenv install 3.13.11`

`pyenv global 3.13.11`

During installation, you may be prompted to enter your password.

#### 3 (a). Upgrading from an Older Version

If you have previously installed EdkRepo and currently have an older version of the above dependencies installed, you can upgrade using the following commands:

```bash
brew update
brew upgrade pyenv
pyenv install 3.13.11
pyenv uninstall 3.8.16 # Replace this with the version number you currently have installed, you can see which version is currently active with "pyenv version".
pyenv global 3.13.11
pyenv rehash
```

#### 4. Configure Shell for Pyenv and Git

To enable usage of Pyenv installed Python interpreters and Git command completions, run the following command:

`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/tianocore/edk2-edkrepo/main/edkrepo_installer/mac-scripts/setup_git_pyenv_mac.sh)"`

Restart your shell so the Pyenv changes can take effect:

`exec $SHELL`

If you are upgrading from an older version and have already run this script once you do not need to run it again.

### Install EdkRepo on macOS

Extract the archive:

`tar -xzvf edkrepo-<version>.tar.gz`

If you are installing from source, you will need to build the distribution tarball using the following commands first:

1. `pip install wheel` (If not done already)
2. `cd build-scripts`
3. `./build_linux_installer.py`

Install EdkRepo:

`./install.py`

Restart your shell so the new Pyenv shim for EdkRepo can take effect:

`exec $SHELL`

## Windows Build and Installation

### Pre-Requisites

- Git 2.24.x or later
- Python 3.10.16 or later (Python 3.13 is recommended)

Git 2.51.2 is the version that has received the most validation, though any version of Git 2.24.0 or later works fine. For security reasons, it is generally advisable to run the newest release of Git for Windows that works for you. If you want to install 2.51.2, here are some links:

- [Direct Link - Git for Windows 2.52.2 - X64](https://github.com/git-for-windows/git/releases/download/v2.51.2.windows.1/Git-2.51.2-64-bit.exe)
- [Direct Link - Git for Windows 2.52.2 - ARM64](https://github.com/git-for-windows/git/releases/download/v2.51.2.windows.1/Git-2.51.2-arm64.exe)

Python 3.10.16 or later is required, with Python 3.13.11 or later recommended due to performance improvements and security fixes. You can get Python from here: [https://www.python.org/]([https://www.python.org/). The Windows installer .exe will fail if Python 3.10.16 or later is not detected.

### Install EdkRepo on Windows

1. Run the installer .exe
2. Click Install

### Install From Source on Windows

To install from source, one must build and run the installer .exe using the instructions below at least once in order to setup the EdkRepo configuration files. One this is done, one may use the standard distutils method to install EdkRepo from source:

`py -3 setup.py install`

### Windows Build Process

#### Build Pre-Requisites

- Visual Studio 2015 or later with the C# language installed
- Python Wheel

Install Python wheel using the following:

`py -3 -m pip install wheel`

#### Build

Open a command prompt and type the following:

1. `cd build-scripts`
2. `build_windows_installer.bat`

## Timeline

| Time | Event |
|:----:|:-----:|
| WW 10 2021 | Moved from edk2-staging to a dedicated repository |
| WW 26 2019 | Initial commit of EdkRepo |
|...|...|

## Maintainers

- Ashley DeSimone <ashley.e.desimone@intel.com>
- Nate DeSimone <nathaniel.l.desimone@intel.com>
- Kevin Sun <kevin.sun@intel.com>

## Known Issues

Please see [https://github.com/tianocore/edk2-edkrepo/issues](https://github.com/tianocore/edk2-edkrepo/issues)

## Related Links

- [https://github.com/tianocore/edk2-edkrepo-manifest](https://github.com/tianocore/edk2-edkrepo-manifest)
- [https://github.com/tianocore/edk2-platforms](https://github.com/tianocore/edk2-platforms)
