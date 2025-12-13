# EdkRepo User's Guide

## Introduction

EdkRepo is a multi-repository tool designed to streamline EDK II firmware development. Built on top of Git, EdkRepo automates common workflows for projects that span multiple Git repositories, making it easier to clone, manage, and contribute to complex firmware projects. EdkRepo uses manifest XML files to describe the git repositories and packages that a project uses, providing a centralized way to define project structure and dependencies. EdkRepo is written in Python and is compatible with Python 3.10 or later.

### Key Features

- **Multi-Repository Management** - Clone and manage projects composed of multiple Git repositories as a single workspace
- **Branch Combinations** - Switch between predefined sets of branches across all repositories simultaneously
- **PIN Files** - Capture and restore exact repository states for reproducible builds
- **Sparse Checkout** - Work with only the files you need in large repositories
- **Code Review Integration** - Streamline the process of submitting changes for review
- **Workspace Maintenance** - Keep your development environment healthy with built-in maintenance operations

### Getting Started

To begin using EdkRepo, you'll typically:

1. Use `edkrepo manifest` to view available projects
2. Use `edkrepo clone` to create a new workspace for your project
3. Use `edkrepo status` to check the current state of your workspace
4. Use `edkrepo sync` to pull the latest changes from remote repositories
5. Make your changes and use `edkrepo send-review` to submit them for review

For detailed information about each command, see the Command References section below.

<details>
<summary>

## Command References

</summary>

The commands provided by EdkRepo are documented below. These commands provide functionality for downloading and setting up local workspaces, syncing workspaces, and moving between predefined groups of branches. Additional commands and command line arguments may be added over time to enhance functionality and improve user experience. EdkRepo is designed to work in conjunction with Git—tasks not automated by EdkRepo are meant to be performed using standard Git commands.

- [cache](command_references/cache.md) - Manages local caching support for project repos
- [checkout](command_references/checkout.md) - Enables checking out a specific branch combination
- [checkout-pin](command_references/checkout-pin.md) - Checks out the revisions described in a PIN file
- [clean](command_references/clean.md) - Deletes untracked files from all repositories in the workspace
- [clone](command_references/clone.md) - Downloads a project and creates a new workspace
- [combo](command_references/combo.md) - Displays the currently checked out combination and lists all available combinations
- [create-pin](command_references/create-pin.md) - Creates a PIN file based on the current workspace state
- [f2f-cherry-pick](command_references/f2f-cherry-pick.md) - Cherry pick changes between different folders
- [list-pins](command_references/list-pins.md) - List pin files available for the current project
- [list-repos](command_references/list-repos.md) - Lists the git repos used by available projects
- [log](command_references/log.md) - Combined log output for all repos across the workspace
- [maintenance](command_references/maintenance.md) - Performs workspace wide maintenance operations
- [manifest](command_references/manifest.md) - Lists the available projects
- [manifest-repos](command_references/manifest-repos.md) - Lists, adds or removes a manifest repository
- [reset](command_references/reset.md) - Unstages all staged files in the workspace
- [send-review](command_references/send-review.md) - Sends a local change for code review
- [sparse](command_references/sparse.md) - Displays the current sparse checkout status
- [squash](command_references/squash.md) - Convert multiple commits into a single commit
- [status](command_references/status.md) - Displays the current combo and the status of each repository
- [sync](command_references/sync.md) - Updates the local copy of the current combination's target branches
- [update-manifest-repo](command_references/update-manifest-repo.md) - Updates the global manifest repository

</details>
