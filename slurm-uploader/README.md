# Overview

Submit a job from a local to machine to Snellius, to archive a day of images.

## Installation on Snellius

SSH into snellius then:

```bash
git clone git@github.com:iw108/amolf.git

./mycostreams/slurm-uploader/scripts/install-environment

```

## Running locally

In in order to test the publisher/subscriber locally, start RabbitMQ:

```bash
docker compose up
```

Then in one terminal run the subscriber
```bash
poetry run cli subscribe
```

And in another run the publisher
```bash
poetry run cli publish "job_id"
```

To submit a job
```bash
poetry run cli submit $(date -I)
```
