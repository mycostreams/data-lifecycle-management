# Data lifecycle management

Code relating to the lifecycle management of *raw* image data — moving imaging output from
the microscope, into object storage, and on to long-term archival.

This is a monorepo of independent Dockerized services; each has its own README with setup and
usage. In the pipeline it comes first: nothing downstream runs until data has landed in S3, and
`export-ingester` is what starts orchestrator's daily jobs on Snellius. See
[docs/data-flow.md](docs/data-flow.md) for the path from microscope to Dropbox, and
[rhizosphere/repos/data-lifecycle-management.md](https://github.com/Staalduine/rhizosphere/blob/main/repos/data-lifecycle-management.md).

## Services

| Service | Role |
|---|---|
| [`prince-archiver`](prince-archiver/README.md) | Moves local image data to S3-compatible object storage as soon as an imaging event is available (services: `mock-prince`, `exporter`, `purger`, `state-manager`). |
| [`surf-archiver`](surf-archiver/README.md) | CLI + remote client that copies daily data from S3, bundling it into per-experiment, per-day tar archives on the SURF Data Archive and emitting a RabbitMQ message when done. |
| [`export-ingester`](export-ingester/README.md) | Fetches export payloads from the state-manager API, SFTPs them to Snellius and submits orchestrator's daily jobs (`daily.sh`, `daily_videos.sh`, `daily_overview.sh`) over SSH. The schedules are arq crons in `export_ingester/worker.py`. |

## Infrastructure

[`infrastructure/`](infrastructure/) holds the shared supporting stack the services run
against: `alloy`, `object-store`, `redis`, and `traefik`.

## DevOps & contributing

See [DEVOPS.md](DEVOPS.md) for the contributing workflow (branch → PR → green CI → merge) and
operational runbook.
