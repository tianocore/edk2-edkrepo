# edkrepo manifest-repos

## Summary

Lists, adds or removes a manifest repository.

## Usage

```
edkrepo manifest-repos [-h] [--performance] [-v] [-c]
                       {list,add,remove} [name] [url] [branch] [path]
```

## Positional Arguments

### {list,add,remove}

**Type:** Required

Which action to take:
- **list** - List all available manifest repositories
- **add** - Add a manifest repository
- **remove** - Remove a manifest repository

### name

**Type:** Conditional (Required with add or remove)

The name of a manifest repository to add/remove. Required with Add or Remove flags.

### url

**Type:** Conditional (Required with add)

The URL of a manifest repository to add. Required with Add flag.

### branch

**Type:** Conditional (Required with add)

The branch of a manifest repository to use. Required with Add flag.

### path

**Type:** Conditional (Required with add)

The local path that a manifest is stored at in the edkrepo global data directory. Required with Add flag.

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

### List all manifest repositories

```
edkrepo manifest-repos list
```

### Add a new manifest repository

```
edkrepo manifest-repos add my-manifests https://github.com/myorg/manifests.git main manifests
```

### Remove a manifest repository

```
edkrepo manifest-repos remove my-manifests
```

### List manifest repositories with verbose output

```
edkrepo manifest-repos list --verbose
```

## Notes

- The path parameter specifies where the manifest repository will be cloned within EdkRepo's global data directory.
- Removing a manifest repository does not delete the local clone; it only removes it from EdkRepo's configuration.
- Multiple manifest repositories can be configured, allowing you to work with projects from different organizations or sources.
- After adding a new manifest repository, use `edkrepo manifest` to see the projects available from all configured repositories.
