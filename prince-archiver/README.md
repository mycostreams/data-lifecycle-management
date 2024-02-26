# Introduction

Demo code for getting 


# Input directory structure

The input directory structure is assumed to have the form:

```
|-- <timestamp>-<Prince position>
|   |-- Img
|   |   |-- **/*.tif
|   |-- param.json
```


# Running via docker compose

Get all containers running:

```bash
docker compose up
```


# Local development

Get rabbitmq and postgres running

```bash
docker compose up postgres rabbitmq s3mock
```


In a seperate terminal, run the worker:

```bash
poetry run celery -A prince_archiver.celery worker -l INFO
```

Start the file watcher:

```bash
poetry run watch
```

