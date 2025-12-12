# edkrepo list-pins

## Summary

List pin files available for the current project.

## Usage

```
edkrepo list-pins [-h] [--description] [--project PROJECT]
                  [--source-manifest-repo SOURCE_MANIFEST_REPO]
                  [--performance] [-v] [-c]
```

## Options

### -h, --help

Show help message and exit.

### --description

Prints the description field of the pin file in addition to the pin file name.

### --project PROJECT

The project to display pin files for.

### --source-manifest-repo SOURCE_MANIFEST_REPO

The name of the workspace's source global manifest repository.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### List pin files for the current workspace project

```
edkrepo list-pins
```

### List pin files with descriptions

```
edkrepo list-pins --description
```

### List pin files for a specific project

```
edkrepo list-pins --project MyProjectName
```

### List pin files from a specific manifest repository

```
edkrepo list-pins --source-manifest-repo my-manifest-repo
```

### List pin files with descriptions and verbose output

```
edkrepo list-pins --description --verbose
```

## Notes

- When run from within a workspace, the command lists pin files for the current project by default.
- Use the `--project` option to list pin files for a different project without being in a workspace.
- The `--description` option provides context about what each pin file represents, making it easier to identify the appropriate pin to use.
- Pin files represent specific snapshots of repository states and can be checked out using `edkrepo checkout-pin`.
- Use `edkrepo create-pin` to create new pin files based on the current workspace state.
