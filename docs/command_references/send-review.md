# edkrepo send-review

## Summary

Sends a local change for code review, required to make any official code change.

## Usage

```
edkrepo send-review [-h] [-n] [--reviewers REVIEWERS [REVIEWERS ...]]
                    [--dry-run] [--draft] [--title TITLE [TITLE ...]]
                    [-o] [--performance] [-v] [-c]
                    [repository]
```

## Positional Arguments

### repository

**Type:** Optional

The repository containing the code to be reviewed.

## Options

### -h, --help

Show help message and exit.

### -n, --noweb

Suppresses the default behavior of opening the review in a web browser.

### --reviewers REVIEWERS [REVIEWERS ...]

Adds one or more reviewers via the command line.

### --dry-run

Lists the reviewers, target branch, and affected files but does not send a review.

### --draft

Creates a draft review.

### --title TITLE [TITLE ...]

The title of the PR. Also used to generate the name of the PR branch.

### -o, --override

Ignore warnings.

### --performance

Displays performance timing data for successful commands.

### -v, --verbose

Increases command verbosity.

### -c, --color

Force color output (useful with '`less -r`').

## Examples

### Send a review for the current repository

```
edkrepo send-review
```

### Send a review for a specific repository

```
edkrepo send-review edk2
```

### Send a review with a custom title

```
edkrepo send-review --title Fix memory leak in PCI driver
```

### Add specific reviewers

```
edkrepo send-review --reviewers user1@example.com user2@example.com
```

### Create a draft review

```
edkrepo send-review --draft --title Work in progress feature
```

### Dry run to preview the review

```
edkrepo send-review --dry-run
```

### Send a review without opening a web browser

```
edkrepo send-review --noweb --title Bug fix for USB controller
```

### Send a review with override to ignore warnings

```
edkrepo send-review --override --title Critical security patch
```

## Notes

- By default, the command opens the review in your web browser.
- Use `--dry-run` to preview what will be sent before actually creating the review.
- The title specified with `--title` is used both for the pull request title and to generate the PR branch name.
- If no repository is specified, the command operates on the current repository based on your working directory.
- Multiple reviewers can be specified by listing them after the `--reviewers` option.
- The `--override` option allows you to proceed past warnings that would otherwise prevent sending the review.
