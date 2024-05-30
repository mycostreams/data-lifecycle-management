#! /usr/bin/env sh
set -e

docker compose -f tests/compose.integration.yml up --detach --wait

poetry run alembic upgrade head
poetry run pytest tests ${@} -m integration

docker compose -f tests/compose.integration.yml down --volumes --remove-orphans
