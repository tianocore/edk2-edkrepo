# edkrepo log

## Summary

Combined log output for all repos across the workspace.

## Usage

```
edkrepo log [-h] [-n NUMBER] [-o] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### -n, --number NUMBER

Only show NUMBER most recent commits.

### -o, --oneline

Show a single-line summary for each commit.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Display full log for all repositories

```
edkrepo log
```

### Display the 10 most recent commits

```
edkrepo log --number 10
```

### Display log in single-line format

```
edkrepo log --oneline
```

### Display the 20 most recent commits in single-line format

```
edkrepo log --number 20 --oneline
```

### Display log with verbose output

```
edkrepo log --verbose
```

## Notes

- This command provides a unified view of commit history across all repositories in the workspace.
- The log output is combined and sorted chronologically, making it easy to see the progression of changes across multiple repositories.
- For detailed log information about a specific repository, navigate to that repository directory and use `git log` directly.
