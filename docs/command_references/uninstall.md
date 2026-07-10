# edkrepo uninstall

## Summary

Uninstalls EdkRepo.

The `~/.edkrepo` directory is intentionally preserved in case it contains modified configuration files. It can be safely deleted if no longer needed.

## Usage

```
edkrepo uninstall [-h] [--yes] [--system] [-v]
```

## Options

### -h, --help

Show help message and exit.

### -y, --yes

Do not prompt for confirmation before uninstalling. Has no effect on Windows.

### -s, --system

Linux only. Uninstall a system-level EdkRepo install instead of a user-level install (requires root).

### -v, --verbose

Increases command verbosity.

## Examples

### Uninstall EdkRepo for the current user, with a confirmation prompt

```
edkrepo uninstall
```

### Uninstall EdkRepo for the current user without prompting

```
edkrepo uninstall --yes
```

### Uninstall a system-level EdkRepo install (requires root)

```
sudo edkrepo uninstall --system --yes
```
