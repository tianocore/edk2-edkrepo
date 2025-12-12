# edkrepo cache

## Summary

Manages local caching support for project repos. The goal of this feature is to improve clone performance.

## Usage

```
edkrepo cache [-h] [--enable] [--disable] [--update] [--info]
              [--format FORMAT] [--path PATH] [--selective]
              [--source-manifest-repo SOURCE_MANIFEST_REPO]
              [--performance] [-v] [-c]
              [project]
```

## Positional Arguments

### project

**Type:** Optional

Project or manifest/pin file to add to the cache.

## Options

### -h, --help

Show help message and exit.

### --enable

Enables caching support on the system.

### --disable

Disables caching support on the system.

### --update

Update the repo cache for all cached projects. Will enable cache if currently disabled.

### --info

Display the current cache information.

### --format FORMAT

Change the format that the cache information is displayed in.

### --path PATH

Path where cache will be created or "`default`" to restore the default path.

### --selective

Only update the cache with the objects referenced by Project or the current workspace manifest.

### --source-manifest-repo SOURCE_MANIFEST_REPO

The name of the workspace's source global manifest repository.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Enable caching support

```
edkrepo cache --enable
```

### Disable caching support

```
edkrepo cache --disable
```

### Add a project to the cache

```
edkrepo cache MyProjectName
```

### Update all cached projects

```
edkrepo cache --update
```

### Selectively update cache for a specific project

```
edkrepo cache --selective MyProjectName
```

### Display cache information

```
edkrepo cache --info
```

### Display cache information in a specific format

```
edkrepo cache --info --format json
```

### Set a custom cache path

```
edkrepo cache --path C:\EdkRepoCache
```

### Restore the default cache path

```
edkrepo cache --path default
```

## Notes

- The cache feature improves clone performance by storing repository objects locally that can be reused across multiple clones.
- Enabling the cache for the first time will create the cache directory structure.
- Using `--update` will automatically enable the cache if it is currently disabled.
- The `--selective` option is useful when you only want to cache specific projects rather than all objects from all cached projects.
- Cache information can be displayed in different formats using the `--format` option (availability depends on implementation).
