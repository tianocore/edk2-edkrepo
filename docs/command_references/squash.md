# edkrepo squash

## Summary

Convert multiple commits into a single commit.

## Usage

```
edkrepo squash [-h] [--oneline] [--performance] [-v] [-c]
               commit-ish new-branch
```

## Positional Arguments

### commit-ish

**Type:** Required

The range of commits to be squashed, specified using the same syntax as git rev-list.

### new-branch

**Type:** Required

The single commit that is the result of the squash operation will be placed into a new branch with this name.

## Options

### -h, --help

Show help message and exit.

### --oneline

Compact the commit messages of the squashed commits down to one line.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Squash the last 3 commits into a new branch

```
edkrepo squash HEAD~3..HEAD my-squashed-branch
```

### Squash commits with compact one-line messages

```
edkrepo squash --oneline HEAD~5..HEAD feature-complete
```

### Squash a specific range of commits

```
edkrepo squash abc1234..def5678 refactored-feature
```

### Squash with verbose output

```
edkrepo squash --verbose HEAD~4..HEAD consolidated-changes
```

## Notes

- The commit range uses the same syntax as `git rev-list`, such as `HEAD~3..HEAD` or `commit1..commit2`.
- The resulting squashed commit will be placed on a new branch, leaving the original commits unchanged.
- Use `--oneline` to condense commit messages into a more compact format.
- This command is useful for cleaning up development history before sending changes for review.
- The new branch can be used for code review or merging while preserving the detailed history in the original branch.
- Common use cases include:
  - Consolidating multiple work-in-progress commits into a single logical change
  - Preparing a clean commit history for upstream submission
  - Simplifying complex development iterations into reviewable units
