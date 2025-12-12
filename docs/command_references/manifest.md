# edkrepo manifest

## Summary

Lists the available projects.

## Usage

```
edkrepo manifest [-h] [-a] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### -a, --archived

Include a listing of archived projects.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### List all available projects

```
edkrepo manifest
```

### List projects including archived projects

```
edkrepo manifest --archived
```

### List projects with verbose output

```
edkrepo manifest --verbose
```

## Notes

- This command displays all projects available in the configured manifest repositories.
- Each project entry shows the project name that can be used with commands like `edkrepo clone`.
- Archived projects are typically older or deprecated projects that are no longer actively maintained but are preserved for reference.
- The project list is retrieved from the global manifest repositories configured for EdkRepo.

