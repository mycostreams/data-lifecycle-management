#! /usr/bin/env sh

set -e

docker compose build

docker compose -f tests/compose.integration.yml down --volumes --remove-orphans
docker compose -f tests/compose.e2e.yml up --detach --wait

docker compose -f tests/compose.e2e.yml run -ti db-migrations

poetry run behave ${@}

docker compose -f tests/compose.integration.yml down --volumes --remove-orphans
