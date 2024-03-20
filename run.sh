#!/bin/sh

# No argument passed with the script -> default to dev
MODE=${1:-dev}
SUPERUSER=${2:-no}

if ["$MODE" = "prod"]; then
    ENV_FILE=.env.prod
else
    ENV_FILE=.env.dev
fi

export $(grep -v '^#' .environment/.env.shared | xargs)
export $(grep -v '^#' .environment/$ENV_FILE | xargs)

if [ "$SUPERUSER" = "superuser" ]; then
    export CREATE_SUPERUSER=True
fi

exec uvicorn --reload --host $HOST --port $PORT "$APP_MODULE"