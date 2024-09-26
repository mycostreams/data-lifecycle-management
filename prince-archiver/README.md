# Introduction

This project provides a mechanism for moving local image data to an s3 supported
object storage backend as soon as a timestep is available. 

It consists of the following entrypoints:
- `event-ingester`
- `state-manager`
- `upload-worker`
- `api`

The `event-ingester` ingests imaging events produced by various imaging systems (e.g. 
Prince), copying them to a staging area if necessary. It then appends this information 
to a redis stream which can be read by other (sub)systems. It is also responsible for 
deleting source and staging files after a predefined amount of elapsed time.

The `state-manaher` is responsible for persisting state relating to imaging events, 
storing it in a local database. It pulls messages from the `event-ingester` stream and 
also recieves notifications from the `upload-worker` and external `surf-archiver` systems.
The former notifies the worker that image data has been uploaded to object storage. The 
latter informs the system when uploads have been moved into the tape archive.

The `upload-worker` pulls messages from the `data-ingester` stream. It bundles the 
corresponding image data into a tar file, and uploads it to an S3 supported object
storage. It notifies the `state-manager` when this upload process is complete.

The `api` acts as a gateway to access information related to the latest state of the 
imaging events.


# Input directory structure 

In order to successfully ingest imaging events, the file system of the external systems 
(e.g. Prince, Aretha) need to be mounted into the `event-ingester` container. 
It is assumed that the directory structure of the source systems has the following 
stucture. The data ingestion 

```
|-- <system>
|   |-- events:
|   |   |-- *.json
|   |-- <img-dir>
|   |   |-- Img
|   |   |   |-- *.tif
```

The `*.json` files contain metadata relating to an imaging event and has the form:

```
{
    timestep_id: UUID
    plate: int
    cross_date: date
    position: int
    timestamp: datetime
    img_count: int
    img_dir: str
}

```
Where `img_dir` is the relative path to directory containing the images.


# Running via docker compose

As a preliminary step, we must ensure that the database migrations are run, the redis
groups are created and data directories are created. To do this run:

```bash
./scripts/init-dev.sh
```

Now you can get all services started with:

```bash
docker compose -f compose.yml -f compose.dev.yml up -d
```

Follow the logs of the relevant containers with:

```bash
docker compose -f compose.yml -f compose.dev.yml logs -f event-ingester state-manager upload-worker
```

To view data via the api navigate to `http://fastapi.localhost/docs`. Alternatively 
to access programmitically run:

```bash
curl --headers Host:fastapi.localhost localhost:80/api/1/exports
```
