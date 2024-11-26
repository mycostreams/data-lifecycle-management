#! /usr/bin/env sh

cd "$(dirname $(dirname $0))"

FILENAME="$(date +%s).bak"

docker compose run --rm \
    aws-cli s3 cp dump.rdb s3://mycostreams-raw-data/backups/redis/$FILENAME
