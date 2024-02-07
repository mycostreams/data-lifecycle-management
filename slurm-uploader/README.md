# Overview

Module for generating slurm scripts and transferring them to snellius.


To run locally create a `.env` file. This can be the same as the `.env.example`. Then run:

```
docker compose up sftp

poetry run python -m slurm_uploader

```

You should see that that a slurm script has been uploaded to the sftp server within the mounted directory.
