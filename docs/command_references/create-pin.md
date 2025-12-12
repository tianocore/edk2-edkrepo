# edkrepo create-pin

## Summary

Creates a PIN file based on the current workspace state.

## Usage

```
edkrepo create-pin [-h] [--source-manifest-repo SOURCE_MANIFEST_REPO]
                   [--performance] [-v] [-c]
                   PinFileName Description
```

## Positional Arguments

### PinFileName

**Type:** Required

The name of the PIN file. Extension must be `.xml`. File paths are supported only if the `--push` option is not used.

### Description

**Type:** Required

A short summary of the PIN file contents. Must be contained in quotes (`""`).

## Options

### -h, --help

Show help message and exit.

### --source-manifest-repo SOURCE_MANIFEST_REPO

The name of the workspace's source global manifest repository.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Create a PIN file with a description

```
edkrepo create-pin Release_v1.0.0.xml "Release 1.0.0 - Production Ready"
```

### Create a PIN file in a specific directory

```
edkrepo create-pin C:\Pins\MyProject_v2.1.xml "Version 2.1 development snapshot"
```

### Create a PIN file with verbose output

```
edkrepo create-pin --verbose Milestone_Q4.xml "Q4 milestone build"
```

### Create a PIN file from a specific manifest repository

```
edkrepo create-pin --source-manifest-repo my-manifest-repo Snapshot.xml "Current development state"
```

## Notes

- PIN files capture the exact commit SHAs for all repositories in the workspace at the time of creation.
- The PIN file extension must be `.xml`.
- The description must be enclosed in quotes and should provide meaningful context about the state being captured.
- Use `edkrepo checkout-pin` to restore a workspace to the state captured in a PIN file.
- PIN files are particularly useful for:
  - Creating release snapshots
  - Capturing known-good configurations
  - Enabling reproducible builds
  - Documenting specific development milestones
