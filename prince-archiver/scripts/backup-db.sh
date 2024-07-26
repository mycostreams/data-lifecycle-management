#! /usr/bin/env sh

cd "$(dirname $(dirname $0))"


TEMP_DIR="$(mktemp -d)"
FILENAME="$(date +%s).bak"

trap "rm -rf $TEMP_DIR" EXIT

TARGET_PATH=$TEMP_DIR/$FILENAME

docker compose exec db pg_dump --username postgres postgres > $TARGET_PATH

rclone copy $TARGET_PATH ceph-s3:backups/db
