#! /usr/bin/env bash

set -e
set -x


python prince_archiver/prestart_db.py

# Run migrations
alembic upgrade head

# Create redis groups
python /app/prince_archiver/prestart_redis.py

