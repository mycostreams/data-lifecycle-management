#! /usr/bin/env sh
set -e

COMPOSE_FILE=tests/compose.e2e.yml

compose_down(){
    docker compose -f ${COMPOSE_FILE} down --volumes --remove-orphans
}
trap compose_down EXIT


compose_down

docker compose build --quiet

docker compose -f ${COMPOSE_FILE} run --rm db-migrations
docker compose -f ${COMPOSE_FILE} run --rm timestep-generator test_tools init

docker compose -f ${COMPOSE_FILE} up --detach --wait

poetry run behave ${@}
