# edkrepo list-repos

## Summary

Lists the git repos used by available projects and the branches that are used.

## Usage

```
edkrepo list-repos [-h] [--repos REPOS [REPOS ...]] [-a]
                   [--format FORMAT] [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --repos REPOS [REPOS ...]

Only show the given subset of repos instead of all repos. The name of a repo is determined by the name given by the most manifest files.

### -a, --archived

Include a listing of archived projects.

### --format FORMAT

Choose between text or json output format. Default is text.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### List all repositories

```
edkrepo list-repos
```

### List specific repositories

```
edkrepo list-repos --repos edk2 edk2-platforms
```

### List repositories including archived projects

```
edkrepo list-repos --archived
```

### List repositories in JSON format

```
edkrepo list-repos --format json
```

### List specific repositories in JSON format

```
edkrepo list-repos --repos edk2 --format json
```

### List repositories with verbose output

```
edkrepo list-repos --verbose
```

## Notes

- The output includes the branches used by each repository in different project combinations.
- Use `--repos` to filter the output to specific repositories of interest.
- The `--archived` option includes projects that are no longer actively maintained but are still available for reference.
- Repository names are determined by the most common name used across manifest files.
