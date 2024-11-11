#! /usr/bin/env sh
set -e

COMPOSE_FILE=tests/compose.e2e.yml

compose_down(){
    docker compose -f ${COMPOSE_FILE} down --volumes --remove-orphans
}
trap compose_down EXIT

compose_down

docker compose -f ${COMPOSE_FILE} build event-generator --quiet

docker compose -f ${COMPOSE_FILE} up --detach --wait

poetry run behave ${@}
