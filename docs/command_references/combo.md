# edkrepo combo

## Summary

Displays the currently checked out combination and lists all available combinations.

## Usage

```
edkrepo combo [-h] [-a] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### -a, --archived

Include a listing of archived combinations.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Display current combination and list available combinations

```
edkrepo combo
```

### Include archived combinations in the listing

```
edkrepo combo --archived
```

### Display with verbose output

```
edkrepo combo --verbose
```

## Notes

- The currently checked out combination is highlighted in the output.
- Combinations define sets of branches across multiple repositories in the workspace.
- Use `edkrepo checkout` to switch to a different combination.
- Archived combinations are typically older or deprecated combinations that are no longer actively maintained but are preserved for reference.
