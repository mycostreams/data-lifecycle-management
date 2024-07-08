
set -e

docker compose -f compose.test.yml build --quiet
docker compose -f compose.test.yml run -ti pytest tests
