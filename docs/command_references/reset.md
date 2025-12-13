# edkrepo reset

## Summary

Unstages all staged files in the workspace.

## Usage

```
edkrepo reset [-h] [--hard] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --hard

Deletes files after unstaging.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Unstage all staged files (soft reset)

```
edkrepo reset
```

### Unstage and delete all changes (hard reset)

```
edkrepo reset --hard
```

### Reset with verbose output

```
edkrepo reset --verbose
```

## Notes

- By default, this command performs a soft reset, which unstages files but preserves your working directory changes.
- The `--hard` option will discard all changes in the working directory after unstaging, effectively reverting all repositories to their last committed state.
- This command operates on all repositories in the workspace.
- Use `edkrepo status` before and after running reset to see which files are affected.
