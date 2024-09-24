#! /usr/bin/env sh

cd "$(dirname $(dirname $0))"

FILENAME="$(date +%s).bak"

docker compose -f compose.yml -f compose.prod run --rm \
    aws-cli s3 cp redis/dump.rds s3://backups/redis/$FILENAME
