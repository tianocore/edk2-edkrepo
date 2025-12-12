# edkrepo maintenance

## Summary

Performs workspace wide maintenance operations.

## Usage

```
edkrepo maintenance [-h] [--no-gc] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --no-gc

Skips garbage collection operations. Performs all other workspace maintenance operations.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Perform full maintenance including garbage collection

```
edkrepo maintenance
```

### Perform maintenance without garbage collection

```
edkrepo maintenance --no-gc
```

### Perform maintenance with verbose output

```
edkrepo maintenance --verbose
```

### Perform maintenance with performance timing

```
edkrepo maintenance --performance
```

## Notes

- This command performs various maintenance operations across all repositories in the workspace.
- Maintenance operations typically include garbage collection, which can help reduce disk space usage and improve performance.
- Use `--no-gc` to skip garbage collection if you need faster execution or want to preserve all unreferenced objects.
- Garbage collection may take some time on large repositories, especially if it hasn't been run recently.
- Regular maintenance helps keep the workspace healthy and can prevent performance degradation over time.
- It's recommended to run maintenance periodically, especially after extensive development activity or before creating backups.
