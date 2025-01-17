

Ingest an API payload and pipe it to SFTP server (e.g. Snellius)


To trigger the ingestion via cron jobs run:

```bash
docker compose --profile dev up
```

The resulting json file can be found in the mounted volume (`./sftp-data/`)



To manually trigger the ingestion run:
```bash
docker compose up sftp mock-api
docker compose run --rm --no-deps export-ingester python -m export_ingester.main
docker compose --profile dev down
```

