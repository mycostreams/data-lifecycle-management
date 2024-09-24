# Surf archiver: CLI tool 

Surf-Archiver copies daily data from S3, bundling it into a per experiment per day
tar archive.


# Installation

Surf archiver can be installed using [pipx](https://github.com/pypa/pipx). This allows
the cli to be executing the command `surf-archiver`.

In order for it run, ensure that the appropriate AWS environment variables are set. 
These include (but are not limited to):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`


# Example usage

To view available commands run:
```
surf-archive --help
```


To archive for a specific date run:
```
surf-archive archive "2000-01-01" --target-dir .
```
