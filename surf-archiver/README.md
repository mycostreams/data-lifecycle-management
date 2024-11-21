# surf-archiver

The `surf-archiver` tool consists of two components: 
1) a CLI tool
2) a remote client which can execute CLI installed on a remote machine

The CLI tool copies daily data from S3 supported storage, bundling it into a per 
experiment per day tar archives. Once completed it emits a message via RabbitMQ. The 
intended use case is for the CLI tool to installed on the Surf Data Archive and remotely 
triggered daily.


The tool copies data based on the S3 key. It is assumed that the keys have the following
structure:
```
<SRC BUCKET>/<images|videos>/<EXPERIMENT-ID>/YYYYMMDD/*.tar
```

The resulting archive will be created at:
```
<DATA DIR>/<images|videos>/<EXPERIMENT-ID>/YYYY-MM-DD.tar
```

# Installation of the CLI tool

The CLI tool can be installed via [pipx](https://github.com/pypa/pipx).


In order to run the tool needs some configuration. It can be configured by via a yaml 
file:

```yaml
bucket:             # S3 bucket data is pulled from
target_dir:         # Target directory data is stored in       
connction_url:      # RabbitMQ connection url
exchange_name:      # RabbitMQ Exchange name
log_file:           # log file path
```

By default the tool will look for this configuration in the `${HOME}/.surf-archiver`.
The tool will additionally look for these parameters in the shell environment. If they
are defined here, they need to be prefixed by `surf_archiver_`. 


In addition to the above, the following environment variables need to be set in order to
connect to S3.
```bash
AWS_SECRET_KEY_ID=
AWS_ACCESS_KEY_ID=
AWS_ENDPOINT_URL=
```
