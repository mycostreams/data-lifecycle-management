# Surf archiver: CLI tool 

Surf-Archiver copies daily data from S3, bundling it into a per experiment per day
tar archive. 

It consists of two components: 
1) a CLI tool
2) a remote client which can execute CLI installed on a remote machine

The CLI tool can be installed via [pipx](https://github.com/pypa/pipx).


# Development

The easiest way to develop the tool is via docker. This ensures that you can connect
to the dependent services (e.g. s3, rabbitmq). The `prestart` container ensures that 
some test data is populated on s3.

The `surf-archiver-cli` container allows for the invocation of the cli tool. For example:

```bash
docker compose run --rm surf-archiver-cli
surf-archiver --help # See the available commands

surf-archiver archive 2000-01-01  # archive a specific day
cat /data/app.log  # check the logs
ls /data/  # See what data has been archived

```
