#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <migration_name>"
    exit 1
fi

migration=$1

docker-compose run --rm web sh -c "alembic revision -m \"$migration\" --autogenerate && alembic upgrade head"

echo "Migration '$migration' has been created."
