# edkrepo update-manifest-repo

## Summary

Updates the global manifest repository (advanced users only).

## Usage

```
edkrepo update-manifest-repo [-h] [--hard] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --hard

Without this flag, the sync operations on the global manifest repository will not be completed if there are unstaged changes present.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Update the global manifest repository

```
edkrepo update-manifest-repo
```

### Force update even with unstaged changes

```
edkrepo update-manifest-repo --hard
```

### Update with verbose output

```
edkrepo update-manifest-repo --verbose
```

## Notes

- This command is intended for advanced users who need to manually update the global manifest repository.
- By default, the command will not proceed if there are unstaged changes in the global manifest repository.
- **Warning:** Using `--hard` will discard any local changes in the global manifest repository.
- Use `edkrepo sync --update-local-manifest` to update project-specific manifest files in a workspace.
- After updating the global manifest repository, new projects or updated project configurations will become available.
- This command updates all configured manifest repositories, not just a single one.
