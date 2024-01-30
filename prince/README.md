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


Trigger a job
```bash
docker compose exec python -m prince
```


# Local development

Get rabbitmq and flower running

```bash
docker compose up rabbitmq flower
```


In a seperate terminal, run the worker:

```bash
poetry run celery -A prince.celery_app worker -l INFO
```


In another terminal, trigger some jobs:
```bash
poetry run python -m prince
```