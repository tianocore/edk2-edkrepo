# edkrepo sparse

## Summary

Displays the current sparse checkout status and enables changing the sparse checkout state.

## Usage

```
edkrepo sparse [-h] [--enable] [--disable] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --enable

Enables sparse checkout if supported in the project manifest file.

### --disable

Disables sparse checkout if it is currently enabled.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Display current sparse checkout status

```
edkrepo sparse
```

### Enable sparse checkout

```
edkrepo sparse --enable
```

### Disable sparse checkout

```
edkrepo sparse --disable
```

### Check status with verbose output

```
edkrepo sparse --verbose
```

## Notes

- When run without options, the command displays whether sparse checkout is currently enabled or disabled.
- Sparse checkout allows you to work with only a subset of files in a repository, reducing disk space usage and improving performance.
- The sparse checkout configuration must be defined in the project manifest file for `--enable` to work.
- Enabling sparse checkout will update your working directory to include only the files specified in the sparse configuration.
- Disabling sparse checkout will restore all files in the repository to your working directory.
- Sparse checkout is particularly useful for large projects where you only need to work with specific components or directories.
