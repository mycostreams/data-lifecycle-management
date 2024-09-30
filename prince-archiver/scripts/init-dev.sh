#!/bin/bash

set -e
set -x

cd "$(dirname $(dirname $0))"

docker compose -f compose.yml -f compose.dev.yml run --rm prince \
    prince-cli populate-data-dir
