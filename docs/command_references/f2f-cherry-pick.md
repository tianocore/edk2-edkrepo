# edkrepo f2f-cherry-pick

## Summary

Cherry pick changes between different folders.

## Usage

```
edkrepo f2f-cherry-pick [-h] [--template TEMPLATE]
                        [--folders FOLDERS [FOLDERS ...]] [--continue]
                        [--abort] [--list-templates] [-x] [--squash]
                        [--performance] [-v] [-c]
                        [commit-ish]
```

## Positional Arguments

### commit-ish

**Type:** Optional

The commit or range of commits to be cherry picked, specified using the same syntax as git rev-parse/rev-list.

## Options

### -h, --help

Show help message and exit.

### --template TEMPLATE

The source and destination name separated by a colon (`:`). Names are taken from templates pre-defined in the manifest file.

Example: `CNL:ICL` might merge `CannonLakeSiliconPkg`→`IceLakeSiliconPkg` + `CannonLakePlatSamplePkg`→`IceLakePlatSamplePkg`. This can also be done in reverse (`ICL:CNL`).

### --folders FOLDERS [FOLDERS ...]

A list of source and destination folders separated by a colon (`:`). Only needed if a pre-defined template is not in the manifest file.

Example: `CannonLakeSiliconPkg:IceLakeSiliconPkg`

### --continue

Continue processing a cherry pick after resolving a merge conflict.

### --abort

Abort processing a cherry pick after encountering a merge conflict.

### --list-templates

Print a list of templates defined in the manifest file, and the mappings they define.

### -x, --append-sha

Append a line that says "`(cherry picked from commit ...)`" to the original commit message in order to indicate which commit this change was cherry-picked from.

### --squash

If given a range of commits, automatically squash them during the cherry pick.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### List available templates

```
edkrepo f2f-cherry-pick --list-templates
```

### Cherry pick a single commit using a template

```
edkrepo f2f-cherry-pick --template CNL:ICL abc1234
```

### Cherry pick a range of commits

```
edkrepo f2f-cherry-pick --template CNL:ICL main~5..main~2
```

### Cherry pick with custom folder mapping

```
edkrepo f2f-cherry-pick --folders CannonLakeSiliconPkg:IceLakeSiliconPkg abc1234
```

### Cherry pick multiple folder mappings

```
edkrepo f2f-cherry-pick --folders CannonLakeSiliconPkg:IceLakeSiliconPkg CannonLakePlatSamplePkg:IceLakePlatSamplePkg abc1234
```

### Cherry pick with SHA appended to commit message

```
edkrepo f2f-cherry-pick --template CNL:ICL --append-sha abc1234
```

### Cherry pick and squash a range of commits

```
edkrepo f2f-cherry-pick --template CNL:ICL --squash main~5..main~2
```

### Continue after resolving conflicts

```
edkrepo f2f-cherry-pick --continue
```

### Abort a cherry pick in progress

```
edkrepo f2f-cherry-pick --abort
```

## Notes

- "f2f" stands for "folder-to-folder", indicating this command cherry picks changes from one folder structure to another.
- Templates defined in the manifest file simplify cherry picking between commonly mapped folder pairs.
- The `--folders` option allows custom mappings without requiring template definitions in the manifest.
- Multiple folder mappings can be specified with `--folders` to cherry pick changes across several directories simultaneously.
- If conflicts occur during cherry picking, resolve them manually, then use `--continue` to proceed or `--abort` to cancel.
- The `--append-sha` option is useful for maintaining traceability of cherry-picked commits.
- Use `--squash` when cherry picking multiple related commits that should be combined into a single commit in the destination.
- This command is particularly useful for porting changes between platform variants or silicon generations.
