#! /usr/bin/env sh

cd "$(dirname $(dirname $0))"

TARGET_DIR=$PWD/backups
FILENAME="$(date +%s).bak"
TARGET_PATH=$TARGET_DIR/$FILENAME

mkdir -p $TARGET_DIR
trap "rm -f $TARGET_PATH" EXIT



docker compose exec db pg_dump --username postgres postgres > $TARGET_PATH

docker compose -f compose.yml -f compose.prod.yml run --rm \
    aws-cli s3 cp postgres/$FILENAME s3://backups/db/$FILENAME
