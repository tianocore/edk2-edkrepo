# edkrepo clean

## Summary

Deletes untracked files from all repositories in the workspace.

## Usage

```
edkrepo clean [-h] [-f] [-q] [-d] [-x] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### -f, --force

Without this flag, untracked files are listed but not deleted.

### -q, --quiet

Don't list files as they are deleted.

### -d, --dirs

Remove directories in addition to files.

### -x, --include-ignored

Removes all untracked files.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Preview what would be deleted (dry run)

```
edkrepo clean
```

### Delete untracked files

```
edkrepo clean --force
```

### Delete untracked files and directories

```
edkrepo clean --force --dirs
```

### Delete all untracked files including ignored files

```
edkrepo clean --force --include-ignored
```

### Delete files quietly without listing them

```
edkrepo clean --force --quiet
```

### Preview with verbose output

```
edkrepo clean --verbose
```

## Notes

- The `--dirs` option is necessary to remove untracked directories; without it, only files are affected.
- The `--include-ignored` option will remove files that match `.gitignore` patterns, which may include build outputs and other generated files.
- This command operates on all repositories in the workspace.
