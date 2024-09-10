#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#================================================================#
#####################    ENV VARIABLES    ########################

function try-load-dotenv {
    echo "Loading environment variables from .env/.dev-sample"
    if [ ! -f "$THIS_DIR/.env/.dev-sample" ]; then
        echo "No .env/.dev-sample file found"
        return 1
    fi
    while read -r line; do
        export "$line"
    done < <(grep -v '^#' "$THIS_DIR/.env/.dev-sample" | grep -v '^$')
}

#================================================================#
########################    DOCKER    ############################

function build-image() {
    echo "Building Docker image for target directory $1"
    local target_dir="$1"
    folder_name=$(basename "$target_dir")
    dockerfile_path="${target_dir}/Dockerfile.${folder_name}"
    
    if [ "$folder_name" = "base" ]; then
        echo "Building base image: ${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}"
        docker build -t "${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}" -f "$dockerfile_path" .
    else
        echo "Building image with base: ${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:base"
        docker build --build-arg BASE_IMAGE="${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:base" -t "${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}" -f "$dockerfile_path" .
    fi
}

function build-all() {
    echo "Building all Docker images"
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }

    declare -A target_dirs=(
        ["compose/fastapi-celery/base"]=false
        ["compose/fastapi-celery/web"]=true
        ["compose/fastapi-celery/celery/worker"]=true
        ["compose/fastapi-celery/celery/beat"]=true
        ["compose/fastapi-celery/celery/flower"]=true
    )

    build-image "$THIS_DIR/compose/fastapi-celery/base" false

    for target_dir in "${!target_dirs[@]}"; do
        if [ "$target_dir" != "compose/fastapi-celery/base" ]; then
            echo "Building Docker image for $target_dir"
            build-image "$THIS_DIR/$target_dir" "${target_dirs[$target_dir]}"
        fi
    done
}

function push-image() {
    echo "Pushing Docker image for $1"
    local service_dir="$1"
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    folder_name=$(basename "$service_dir")
    docker push "${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}"
}

function push-all-images() {
    echo "Pushing all Docker images"
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    declare -A services
    services=(
        ["compose/fastapi-celery/web"]="Dockerfile"
        ["compose/fastapi-celery/celery/worker"]="Dockerfile.worker"
        ["compose/fastapi-celery/celery/beat"]="Dockerfile.beat"
        ["compose/fastapi-celery/celery/flower"]="Dockerfile.flower"
    )

    for service_dir in "${!services[@]}"; do
        echo "Pushing service $service_dir"
        push-image "$THIS_DIR/$service_dir"
    done
}

#================================================================#
#####################    DOCKER COMPOSE   ########################

function generate-docker-compose() {
    echo "Generating docker-compose.yml from template"
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    local template_file="$THIS_DIR/docker-compose.template.yml"
    local output_file="$THIS_DIR/docker-compose.yml"
    envsubst < "$template_file" > "$output_file"
}

function create-network() {
    local network_name="$1"
    if [ -z "$(docker network ls --filter name=^${network_name}$ --format='{{ .Name }}')" ]; then
        echo "Creating network ${network_name}"
        docker network create "${network_name}"
    else
        echo "Network ${network_name} already exists"
    fi
}

function up-dev() {
    echo "Starting development services"
    create-network shared_network
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    generate-docker-compose
    docker compose -f "$THIS_DIR/docker-compose.yml" up
}

function down() {
    echo "Bringing down services"
    docker compose -f "$THIS_DIR/docker-compose.yml" down --remove-orphans
}

function monitoring-up() {
    echo "Starting monitoring services"
    docker compose -f "prometheus-grafana/docker-compose.yml" up
}

function monitoring-down() {
    echo "Stopping monitoring services"
    docker compose -f "prometheus-grafana/docker-compose.yml" down --remove-orphans
}

#================================================================#
#######################    DATABASE    ###########################

function init-alembic() {
    echo "Initializing asynchronous Alembic"
    alembic init -t async alembic

    echo "Adding essential fastapi-users imports to script.py.mako"
    echo 'import fastapi_users_db_sqlalchemy' >> alembic/script.py.mako

    new_imports="import os
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine
from alembic import context
from main import create_app
from project.config import settings
from project.database import Base
from project.fu_core.users.models import User
from project.inference.models import *

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
database_url = str(settings.DATABASE_URL)
config.set_main_option('sqlalchemy.url', database_url)
fastapi_app = create_app()
target_metadata = Base.metadata"

    echo "Updating imports in env.py"
    sed -i '1,30d' alembic/env.py
    echo "$new_imports" | cat - alembic/env.py > tempfile && mv tempfile alembic/env.py
}

function get-revision-postgres() {
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    echo "Ensuring docker compose down on script exit"
    trap 'docker compose down' EXIT
    echo "Starting PostgreSQL service"
    docker compose up -d postgres
    echo "Waiting for PostgreSQL to become available..."
    until docker compose exec postgres pg_isready -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT"; do
        sleep 1
    done
    echo "Setting permissions correctly"
    docker compose run --user root web chown -R fastapi:fastapi /app/alembic/versions
    echo "Applying migrations"
    docker compose run web alembic upgrade head
    echo "Creating Alembic revision"
    docker compose run web alembic revision --autogenerate 
}

function generate-servers-json() {
    echo "Generating servers.json from template"
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    local template_file="$THIS_DIR/compose/pgadmin/servers.template.json"
    local output_file="$THIS_DIR/compose/pgadmin/servers.json"
    envsubst < "$template_file" > "$output_file"
}

#================================================================#
########################    LINTING    ###########################

function lint {
    echo "Running linting and formatting"
    pre-commit run --all-files
}

#================================================================#
########################    TESTS    #############################

function run-tests {
    echo "Running tests"
    pytest -vv -s -x -rs --cov --cov-report=html
}

#================================================================#
########################    UTILS    #############################

function purge-pycache() {
    echo "Purging Python cache files"
    find . -type d -name "__pycache__" -exec sudo rm -r {} +
    find . -type f -name "*.pyc" -exec sudo rm -f {} +
}

function help {
    echo "$0 <task> <args>"
    echo "Tasks:"
    compgen -A function | cat -n
}

TIMEFORMAT="Task completed in %3lR"
time ${@:-help}
