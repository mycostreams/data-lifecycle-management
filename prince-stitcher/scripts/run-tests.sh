
set -e

docker compose -f compose.test.yml build --quiet
docker compose -f compose.test.yml run  --rm image-stitcher pytest tests
