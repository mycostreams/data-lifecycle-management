#! /usr/bin/env sh
set -e

COMPOSE_FILE=tests/compose.integration.yml

function compose-down {
    docker compose -f ${COMPOSE_FILE} down --volumes --remove-orphans
}
trap compose-down EXIT


export POSTGRES_DSN="postgresql+asyncpg://postgres:postgres@localhost:5431/postgres"

compose-down
docker compose -f ${COMPOSE_FILE} up --detach --wait

poetry run alembic upgrade head
poetry run pytest tests ${@} -m integration
