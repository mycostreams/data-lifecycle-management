#!/bin/sh
set -e

service ssh start

exec "$@"
