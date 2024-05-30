# docker compose build


docker compose up -d --wait 
docker compose run db-migrations --quiet

poetry run behave ./tests/e2e/features

docker compose down -v
