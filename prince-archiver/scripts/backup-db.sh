#! /usr/bin/env sh

set -e

cd "$(dirname $(dirname $0))"

BASE_PATH=${1:-"/data/prince"}
FILENAME="$(date +%s).bak"

TARGET_PATH=$BASE_PATH/$FILENAME

docker compose exec -ti db pg_dump --username postgres postgres > $TARGET_PATH
