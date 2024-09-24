#! /usr/bin/env sh
set -e

COMPOSE_FILE=tests/compose.yml

compose_down(){
    docker compose -f ${COMPOSE_FILE} down --volumes --remove-orphans
}
trap compose_down EXIT

compose_down

docker compose -f ${COMPOSE_FILE} up --quiet-pull --detach --wait

poetry run pytest tests ${@}
