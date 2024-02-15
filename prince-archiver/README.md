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
```å


# Local development

Get rabbitmq and flower running

```bash
docker compose up rabbitmq flower
```


In a seperate terminal, run the worker:

```bash
poetry run celery -A prince.celery_app worker -l INFO
```

In a seperate terminal, run the beat:
```bash
poetry run celery -A prince.celery_app beat -l INFO
```
