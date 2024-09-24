#! /usr/bin/env sh

cd "$(dirname $(dirname $0))"

FILENAME="$(date +%s).bak"

docker compose run -f compose.yml -f compose.prod --rm \
    aws-cli s3 cp redis/dump.rds s3://backups/redis/$FILENAME
