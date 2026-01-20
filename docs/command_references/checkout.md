# edkrepo checkout

## Summary

Enables checking out a specific branch combination defined in the project manifest file.

## Usage

```
edkrepo checkout [-h] [-o] [--performance] [-v] [-c] Combination
```

## Positional Arguments

### Combination

**Type:** Optional

The name of the branch combination to checkout as defined in the project manifest file.

## Options

### -h, --help

Show help message and exit.

### -o, --override

Ignore warnings.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Checkout a specific combination

```
edkrepo checkout ReleaseBranch
```

### Checkout with override to ignore warnings

```
edkrepo checkout --override DevelopmentBranch
```

### Checkout with verbose output

```
edkrepo checkout --verbose MainlineBranch
```

### Checkout the default combination

```
edkrepo checkout default
```

## Notes

- The combination name must be defined in the project manifest file for the current workspace.
- Use `edkrepo combo` to list available combinations for the current project.
- The `--override` option allows you to proceed past warnings that would otherwise prevent the checkout.
- All repositories in the workspace will be updated to match the branches specified in the selected combination.
