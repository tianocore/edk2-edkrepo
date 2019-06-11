This branch is for integrating the EdkRepo tool in to EDK2

# Introduction

EdkRepo is the multi-repository tool for EDK II firmware development. EdkRepo is built on top of git. It is intended to automate common developer workflows for projects that use more than one git repository. For example many of the new projects in the edk2-platforms repository require the user to clone several git repositories. EdkRepo makes it easier to set up and upstream changes for these projects. EdkRepo does not replace git, rather it provides higher level extensions that make it easier to work with git. EdkRepo is written in Python and is compatible with Python 3.5 or later.

# Timeline
| Time | Event |
|:----:|:-----:|
| WW 24 2019 | Initial commit of EdkRepo |
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
