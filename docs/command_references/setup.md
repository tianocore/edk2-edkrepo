# edkrepo setup

## Summary

Configures EdkRepo for your user account after a system-level install.

A system-level EdkRepo install makes EdkRepo available for all users on the machine, but does not modify any user's home directory. Each user who wants to use EdkRepo, should run `edkrepo setup` once to add edkrepo configuration files to their home directory. This process creates `~/.edkrepo`, sets up shell command completion, and optionally adds the current combo and git branch to the shell prompt. See the [Installation](../edkrepo_users_guide.md#installation) section of the User's Guide for more details on this two-phase install process.

`edkrepo setup` is not needed after a `--local` install, since a local install configures the user's home directory as part of installation process. Because of this, the `edkrepo setup` command will not exist unless a system-level EdkRepo install is present.

If EdkRepo is run by a user for whom `edkrepo setup` has not yet been run, and a system-level install is present, EdkRepo automatically runs `edkrepo setup` on the user's behalf and then asks the user to re-run their command.

## Usage

```
edkrepo setup [-h] [--prompt] [--no-prompt] [-v]
```

Either `--prompt` or `--no-prompt` must be specified.

## Options

### -h, --help

Show help message and exit.

### --prompt

Add EdkRepo combo and git branch to the shell prompt.

### --no-prompt

Do NOT add EdkRepo combo and git branch to the shell prompt.

### -v, --verbose

Increases command verbosity.

## Examples

### Configure EdkRepo for the current user, and add the combo/branch to the shell prompt

```
edkrepo setup --prompt
```

### Configure EdkRepo for the current user, without shell prompt changes

```
edkrepo setup --no-prompt
```
