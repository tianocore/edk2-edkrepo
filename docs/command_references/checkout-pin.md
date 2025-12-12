# edkrepo checkout-pin

## Summary

Checks out the revisions described in a PIN file in an existing workspace of the same project.

## Usage

```
edkrepo checkout-pin [-h] [-o]
                     [--source-manifest-repo SOURCE_MANIFEST_REPO]
                     [--performance] [-v] [-c]
                     pinfile
```

## Positional Arguments

### pinfile

**Type:** Required

The name of the pin file to checkout.

## Options

### -h, --help

Show help message and exit.

### -o, --override

Ignore warnings.

### --source-manifest-repo SOURCE_MANIFEST_REPO

The name of the workspace's source global manifest repository.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Checkout a pin file by name

```
edkrepo checkout-pin Release_v1.0.0
```

### Checkout a pin file with full path

```
edkrepo checkout-pin C:\Pins\my-project-pin.xml
```

### Checkout with override to ignore warnings

```
edkrepo checkout-pin --override Release_v1.0.0
```

### Checkout with verbose output

```
edkrepo checkout-pin --verbose Release_v1.0.0
```

### Checkout a pin file from a specific manifest repository

```
edkrepo checkout-pin --source-manifest-repo my-manifest-repo Release_v1.0.0
```

## Notes

- PIN files capture the exact commit SHAs for all repositories in a project at a specific point in time.
- The workspace must be for the same project as the PIN file being checked out.
- Use `edkrepo list-pins` to see available PIN files for the current project.
- The `--override` option allows you to proceed past warnings that would otherwise prevent the checkout.

