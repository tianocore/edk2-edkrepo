# edkrepo sync

## Summary

Updates the local copy of the current combination's target branches by pulling the latest changes from the remote. Does not update local branches.

## Usage

```
edkrepo sync [-h] [--fetch] [-u] [-o] [-s]
             [--source-manifest-repo SOURCE_MANIFEST_REPO]
             [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --fetch

Performs a fetch only sync, no changes will be made to the local workspace.

### -u, --update-local-manifest

Updates the local copy of the project manifest file prior to performing sync operations.

### -o, --override

Ignore warnings and proceed with sync operations.

### -s, --skip-submodule

Skip the pull or sync of any submodules.

### --source-manifest-repo SOURCE_MANIFEST_REPO

The name of the workspace's source global manifest repository.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Sync all repositories in the workspace

```
edkrepo sync
```

### Fetch updates without modifying the workspace

```
edkrepo sync --fetch
```

### Sync and update the project manifest

```
edkrepo sync --update-local-manifest
```

### Sync without updating submodules

```
edkrepo sync --skip-submodule
```

### Sync with override to ignore warnings

```
edkrepo sync --override
```

### Sync with verbose output

```
edkrepo sync --verbose
```

## Notes

- This command pulls the latest changes from the remote repositories for all repos in the current combination.
- The sync operation updates the target branches defined in the combination but does not affect your local working branches.
- Use `--fetch` to download updates without modifying your workspace, allowing you to review changes before applying them.
- The `--update-local-manifest` option ensures you're working with the latest project configuration by updating the manifest file first.
- If you have uncommitted changes, the sync operation may fail or require you to use `--override`.
- Submodules are synced by default; use `--skip-submodule` if you want to skip submodule updates.
- Run `edkrepo status` before syncing to check for uncommitted changes that might conflict with updates.
