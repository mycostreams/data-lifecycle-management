#! /usr/bin/env sh
set -e

COMPOSE_FILE=tests/compose.e2e.yml

compose_down(){
    docker compose -f ${COMPOSE_FILE} down --volumes --remove-orphans
}
trap compose-down EXIT


compose_down

docker compose build
docker compose -f ${COMPOSE_FILE} up --detach --wait
docker compose -f ${COMPOSE_FILE} run -ti db-migrations

poetry run behave ${@}

