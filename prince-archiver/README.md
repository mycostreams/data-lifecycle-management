# Overview

This project provides a mechanism for moving local image data to an s3 supported
object storage backend as soon as an imaging event is available. 

It consists of the following services:
- `mock-prince` (for dev purposes)
- `exporter`
- `purger`
- `state-manager`

`mock-prince` simulates the  `prince` experiment setup. It produces new image data at configurable
intervals, after which it publishes messages to the `dlm:new-imaging-event`
Redis stream to notify other systems/ services that the raw image data is ready for processing. The raw data is 
shared between (interested) services by a via volumes. 

The `exporter` service is responsible for uploading raw image data to s3 supported
storage. It consumes messages from the `dlm:new-imaging-event` stream. When a message is 
received it bundles the corresponding raw image data into a tar file, and uploads it to an 
S3 supported object storage. Once completed it publishes a message to the `dlm:new-export` stream.

The `purger` service is responsible for deleting *stale* raw data. It periodically reads 
the `dlm:new-imaging-event` stream between predfined time ranges and deletes the corresponding 
raw image data.

The `state-manager` service is responsible for persisting information relating to 
state of the raw image data. To this end, it consumes the `dlm:new-imaging-event` and 
`dlm:new-imaging-event` streams, updating the local state when messages are received. 
It also subscribes to messages published by the `surf-archvier` services via RabbitMQ, which 
informs the service of the location of the raw data within the data archive.  The `state-manager` service 
also provides a RestAPI. This allows users get presigned URLs to retrieve raw image data from object storage
and to find out where the image exist within the data archive. 


# Development

## Docker compose
The easiest way to get up and running is via Docker Compose. To get the development system up
and running run the following:

```bash
docker compose build state-manager
docker compose up -d
```

This will launch the services in detatched mode. Note that this combines the configurations
defined in `compose.yml` and `compose.override.yml`. 

Follow the logs of the relevant containers with:

```bash
docker compose logs -f state-manager exporter ...
```

To view the data via the api navigate to `http://localhost:8000/docs`. Alternatively 
to access it programmitically run e.g.:

```bash
curl localhost:8000/api/1/exports
```

## Local installation

The project uses Poetry as the package management tool. To install the project locally run:

```bash
poetry install
```

A local installation is rerequired to run the static analysis and tests. 


# Static Anaylsis

Code formatting and linting is handled with Ruff:

```bash
poetry run ruff format
poetry run ruff check --fix
```

mypy is used static type checking:

```bash
poetry run mypy . 
```

# Testing

There are three types of tests:
- unit 
- integration
- end to end

The integration tests use `testcontainers` to launch docker containers and faciliate
testing the interation with external services. This is all handled internally by
`testcontainers` but will require Docker to be running. The end to end tests simulate 
interactions across services and use `Docker Compose` to orchestrate things. 

To run the tests:
```bash
poetry run pytest tests/unit  # unit
poetry run pytest tests/integration # integration

./scripts/run-e2e.sh  # end to end
```
