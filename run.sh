#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#================================================================#
#####################    ENV VARIABLES    ########################

function try-load-dotenv {
    # Function to load environment variables from [.env/.dev-sample]
    if [ ! -f "$THIS_DIR/.env/.dev-sample" ]; then
        echo "no .env/.dev-sample file found"
        return 1
    fi
    while read -r line; do
        export "$line"
    done < <(grep -v '^#' "$THIS_DIR/.env/.dev-sample" | grep -v '^$')
}

#================================================================#
########################    DOCKER    ############################

function build-image() {
    # Function to build a single Docker image
    local target_dir="$1"
    # Get the name of the containing folder
    folder_name=$(basename "$target_dir")
    # Construct the Dockerfile path
    dockerfile_path="${target_dir}/Dockerfile.${folder_name}"
    # Build the Docker image
    if [ "$folder_name" = "base" ]; then
        docker build -t "${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}" -f "$dockerfile_path" .
    else
        docker build --build-arg BASE_IMAGE="${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:base" -t "${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}" -f "$dockerfile_path" .
    fi
}

function build-all() {
    # Function to build all Docker images
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }

    # Define the target directories and whether they should be built from the base image
    declare -A target_dirs=(
        ["compose/fastapi-celery/base"]=false
        ["compose/fastapi-celery/web"]=true
        ["compose/fastapi-celery/celery/worker"]=true
        ["compose/fastapi-celery/celery/beat"]=true
        ["compose/fastapi-celery/celery/flower"]=true
    )

    # Build the base image first
    build-image "$THIS_DIR/compose/fastapi-celery/base" false

    # Loop through the target directories and build the images, skipping the base image
    for target_dir in "${!target_dirs[@]}"; do
        if [ "$target_dir" != "compose/fastapi-celery/base" ]; then
            from_base="${target_dirs[$target_dir]}"
            build-image "$THIS_DIR/$target_dir" "$from_base"
        fi
    done
}

function push-image() {
    # Function to push a single Docker image
    local service_dir="$1"
    # Load environment variables
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    # Get the name of the containing folder
    folder_name=$(basename "$service_dir")
    # Push the Docker image
    docker push "${DOCKERHUB_ACCOUNT}/${DOCKERHUB_REPO}:${folder_name}"
}


function push-all-images() {
    # Function to push all Docker images
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    # Define the services and their corresponding Dockerfiles
    declare -A services
    services=(
        ["compose/fastapi-celery/web"]="Dockerfile"
        ["compose/fastapi-celery/celery/worker"]="Dockerfile.worker"
        ["compose/fastapi-celery/celery/beat"]="Dockerfile.beat"
        ["compose/fastapi-celery/celery/flower"]="Dockerfile.flower"
    )
    # Loop through the services and push the images
    for service_dir in "${!services[@]}"; do
        push-image "$THIS_DIR/$service_dir"
    done
}

#================================================================#
#####################    DOCKER COMPOSE   ########################

function generate-docker-compose() {
    # Function to generate docker-compose.yml from template
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    # Path to the template file
    local template_file="$THIS_DIR/docker-compose.template.yml"
    # Path to the output file
    local output_file="$THIS_DIR/docker-compose.yml"
    # Replace placeholders in the template file with environment variables
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
    # Function to bring up services using the template
    create-network shared_network
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    generate-docker-compose
    docker compose -f "$THIS_DIR/docker-compose.yml" up
}

function down() {
    docker compose -f "$THIS_DIR/docker-compose.yml" down --remove-orphans
}

function monitoring-up() {
    docker compose -f "prometheus-grafana/docker-compose.yml" up
}
function monitoring-down() {
    docker compose -f "prometheus-grafana/docker-compose.yml" down --remove-orphans
}

#================================================================#
#######################    DATABASE    ###########################


function init-alembic() {
    # Init asyncchronous alembic
    alembic init -t async alembic
    # Add essential fastapi-users imports to the script.py.mako template
    echo 'import fastapi_users_db_sqlalchemy' >> alembic/templates/script.py.mako
}

function get-revision-postgres() {
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    # Ensure that docker compose down is called on script exit
    trap 'docker compose down' EXIT
    # Start PostgreSQL service
    docker compose up -d postgres
    # Wait for PostgreSQL to be ready
    until docker compose exec postgres pg_isready -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT"; do
        >&2 echo "Waiting for PostgreSQL to become available..."
        sleep 1
    done
    # Ensure permissions are set correctly
    docker compose run --user root web chown -R fastapi:fastapi /app/alembic/versions
    # Apply existing migrations
    docker compose run web alembic upgrade head
    # Run Alembic revision in the web container
    docker compose run web alembic revision --autogenerate 
}

function generate-servers-json() {
    # Function to generate servers.json from template
    try-load-dotenv || { echo "Failed to load environment variables"; return 1; }
    # Path to the template file
    local template_file="$THIS_DIR/compose/pgadmin/servers.template.json"
    # Path to the output file
    local output_file="$THIS_DIR/compose/pgadmin/servers.json"
    # Replace placeholders in the template file with environment variables
    envsubst < "$template_file" > "$output_file"
}

#================================================================#
########################    LINTING    ###########################


# run linting, formatting, and other static code quality tools
function lint {
    pre-commit run --all-files
}



#================================================================#
########################    TESTS    #############################

function run-tests {
    pytest -vv -s -x -rs --cov --cov-report=html
}


#================================================================#
########################    UTILS    #############################

function purge-pycache() {
    find . -type d -name "__pycache__" -exec sudo rm -r {} +
    find . -type f -name "*.pyc" -exec sudo rm -f {} +
}


# print all functions in this file
function help {
    echo "$0 <task> <args>"
    echo "Tasks:"
    compgen -A function | cat -n
}



TIMEFORMAT="Task completed in %3lR"
time ${@:-help}