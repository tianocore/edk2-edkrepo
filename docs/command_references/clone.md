# edkrepo clone

## Summary

Downloads a project and creates a new workspace.

## Usage

```
edkrepo clone [-h] [--sparse] [--nosparse] [--treeless] [--blobless]
              [--full] [--single-branch] [--no-tags] [-s]
              [--source-manifest-repo SOURCE_MANIFEST_REPO]
              [--performance] [-v] [-c]
              Workspace ProjectNameOrManifestFile [Combination]
```

## Positional Arguments

### Workspace

**Type:** Required

The destination for the newly created workspace. This must be an empty directory. A value of "`.`" indicates the current working directory.

### ProjectNameOrManifestFile

**Type:** Required

Either a project name as listed by "`edkrepo manifest`" or the path to a project manifest file.

If a relative path is provided, clone will first search relative to the current working directory and then search relative to the global manifest repository.

### Combination

**Type:** Optional

The name of the combination to checkout. If not specified, the project's default combination is used.

## Options

### -h, --help

Show help message and exit.

### --sparse

Enables sparse checkout if supported by the project manifest file.

### --nosparse

Disables sparse checkout if the project manifest file enables it by default.

### --treeless

Creates a partial "treeless" clone; all reachable commits will be downloaded with additional blobs and trees being downloaded on demand by future Git operations as needed.

Treeless clones result in significantly faster initial clone times and minimize the amount of content downloaded.

Workspaces created with this option are best used for one-time workspaces that will be discarded.

Any project manifest partial clone settings are ignored.

### --blobless

Creates a partial "blobless" clone; all reachable commits and trees will be downloaded with additional blobs being downloaded on demand by future Git operations as needed.

Blobless clones result in significantly faster initial clone times and minimize the amount of content downloaded.

Workspaces created with this option are best used for persistent development environments.

Any project manifest partial clone settings are ignored.

### --full

Creates a "full" clone; all reachable commits, trees, and blobs will be downloaded.

Full clones have the greatest initial clone times and amount of content downloaded.

Any project manifest partial clone settings are ignored.

### --single-branch

Clone only the history leading to the tip of a single branch for each repository in the workspace.

The branch is determined by the default combination or by the Combination parameter.

### --no-tags

Skips download of tags and updates config settings to ensure that future pull and fetch operations do not follow tags.

Future explicit tag fetches will continue to work as expected.

### -s, --skip-submodule

Skip the pull or sync of any submodules.

### --source-manifest-repo SOURCE_MANIFEST_REPO

The name of the workspace's source global manifest repository.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Clone a project using the default combination

```
edkrepo clone C:\Workspace\MyProject MyProjectName
```

### Clone a project with a specific combination

```
edkrepo clone C:\Workspace\MyProject MyProjectName ReleaseBranch
```

### Clone to the current directory

```
edkrepo clone . MyProjectName
```

### Clone with sparse checkout enabled

```
edkrepo clone --sparse C:\Workspace\MyProject MyProjectName
```

### Clone using a blobless partial clone for persistent development

```
edkrepo clone --blobless C:\Workspace\MyProject MyProjectName
```

### Clone using a treeless partial clone for one-time use

```
edkrepo clone --treeless C:\Workspace\MyProject MyProjectName
```

### Clone with single-branch optimization

```
edkrepo clone --single-branch C:\Workspace\MyProject MyProjectName
```

### Clone from a manifest file

```
edkrepo clone C:\Workspace\MyProject C:\Manifests\my-project.xml
```

## Notes

- The workspace directory must be empty or not exist. EdkRepo will create the directory if needed.
- Partial clone options (`--treeless`, `--blobless`, `--full`) override any partial clone settings in the project manifest.
- The `--single-branch` option can significantly reduce clone time and disk space for projects with extensive history.
- Use `--blobless` for persistent development workspaces where you want faster clone times but will be working with the code long-term.
- Use `--treeless` for temporary or one-time workspaces where minimizing initial download is most important.
