# edkrepo status

## Summary

Displays the current combo and the status of each repository in the combination.

## Usage

```
edkrepo status [-h] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Display workspace status

```
edkrepo status
```

### Display status with verbose output

```
edkrepo status --verbose
```

### Display status with performance timing

```
edkrepo status --performance
```

## Notes

- This command shows the currently checked out combination and provides a status summary for each repository in the workspace.
- The output includes information such as:
  - The current combination name
  - Branch information for each repository
  - Working directory status (modified files, staged changes, etc.)
- Use this command to get a quick overview of the workspace state before performing operations like sync or checkout.
- The status information helps identify which repositories have uncommitted changes or are out of sync with remote branches.
- This is similar to running `git status` on each repository individually, but provides a consolidated workspace-wide view.
