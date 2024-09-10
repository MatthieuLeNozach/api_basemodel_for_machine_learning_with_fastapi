# Api base model for machine learning with FastAPI

A template app for async machine learning inference, with built-in user management, service access policies, monitoring and enriched with various dev tools.



## Table of Contents

- [Api base model for machine learning with FastAPI](#api-base-model-for-machine-learning-with-fastapi)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [1. Install python dependencies](#1-install-python-dependencies)
    - [2. Generate a `.env` file](#2-generate-a-env-file)
    - [3. Build images](#3-build-images)
    - [4. Build a docker compose from template and make a first run](#4-build-a-docker-compose-from-template-and-make-a-first-run)
    - [5. Stop and restart the services](#5-stop-and-restart-the-services)
    - [Optional](#optional)
      - [Launch Prometheus / Grafana monitoring services](#launch-prometheus--grafana-monitoring-services)
  - [Development](#development)
    - [1. Setting up the database](#1-setting-up-the-database)
      - [Initialize async alembic migrations](#initialize-async-alembic-migrations)
      - [Generate the PGAdmin config file to register the DB](#generate-the-pgadmin-config-file-to-register-the-db)
    - [2. Populate the database](#2-populate-the-database)
      - [Add a first user in the DB and make it superuser](#add-a-first-user-in-the-db-and-make-it-superuser)
      - [Grant service access to a model](#grant-service-access-to-a-model)
    - [3. Test the inference service](#3-test-the-inference-service)
      - [Send a request](#send-a-request)
      - [Use the `task_id` to get your response](#use-the-task_id-to-get-your-response)
    - [4. Add new ML models](#4-add-new-ml-models)
      - [Adding the model class](#adding-the-model-class)
      - [Registering the model](#registering-the-model)
      - [Adding a model input schema](#adding-a-model-input-schema)
      - [Creating a request endpoint](#creating-a-request-endpoint)
  - [Dev Tools](#dev-tools)
    - [Tests](#tests)
    - [Linting and pre-commit](#linting-and-pre-commit)
  - [Monitoring](#monitoring)
  - [What next?](#what-next)
    - [Create a simple HTMX Frontend](#create-a-simple-htmx-frontend)


## Features

- FastAPI async web application (separated request and response endpoints)
- User authentication and management using FastAPI-Users
- Async task processing with Celery
- PostgreSQL DB with async SQLAlchemy ORM
- Redis for response caching and as Celery message broker
- Prometheus and Grafana for monitoring (WIP)
- Nginx as a reverse proxy (WIP)


## Project Structure

This project aims to follow a **feature driven architecture**:
- Under `project/`, folders refer to separate routers and features
- Each of the subfolders has it's own set of **models**, **tasks**, **views** (API endpoints), ...
- `fu-core/` contains the set of routers specific to **fastapi-users** (User DB, security)
- `inference/` contains the router with the machine learning endpoints and service access management
- New features can be added quickly this way, like a `dashboard/` router for example

```text
.
├── run.sh                        # The app's starting point: ./run.sh help
├── compose/                      # Docker and build related content
├── project/                 
│   ├── fu_core/                  # FastAPI-Users functions (users, security)
│   ├── inference/                # Machine learning inference code
│   ├── __init__.py               # FastAPI app generator
│   ├── celery_utils.py      
│   ├── config.py                 # Application config
│   ├── database.py          
│   ├── logging.py           
│   └── redis_utils.py      
├── prometheus-grafana/           # Separate docker compose and config files
├── tests/                   
├── .env.example                  # CHANGE ME TO .env
├── docker-compose.template.yml   # Docker Compose generated in the build
├── requirements-worker.txt # Put libs for the workhorse container (ex. Pytorch)
└── requirements.txt          # Put every other required python lib here 
```


[Insert database schema placeholder image here]



## Installation

### Prerequisites

- Docker and Docker Compose
- Poetry for Python package management

### 1. Install python dependencies
- Not essential, as this project is fully containerized, but strongly advised  for code completions and database migrations with `alembic`

```sh
poetry install
poetry shell
```

### 2. Generate a `.env` file

```sh
cp .env.example .env
```
Modify this config file if needed

### 3. Build images

*See [here](run.sh#l21) what happens under the hood*

```sh
chmod +x ./run.sh

./run.sh build-all
```

### 4. Build a docker compose from template and make a first run
*See [here](run.sh#l86) what happens under the hood*


```sh
./run.sh up-dev
```

### 5. Stop and restart the services

```sh
# Stop
./run.sh down
# or
docker compose down

# Start
./run.sh up
# or 
docker compose up
```

### Optional 

#### Launch Prometheus / Grafana monitoring services

```sh
./run.sh monitoring-up

# Stop the service with:
./run.sh monitoring-down

```


## Development

### 1. Setting up the database

#### Initialize async alembic migrations
*See [here](run.sh#l130) what happens under the hood*

```sh
./run.sh init-alembic

./run.sh get-revision-postgres
```


#### Generate the PGAdmin config file to register the DB

```sh
./run.sh generate-servers-json
```
**Caution** Use this only in development, this file will contain sensitive DB credentials, it must not be shared public

### 2. Populate the database

#### Add a first user in the DB and make it superuser 

1. Go to `localhost/docs` if Nginx is enabled, else `localhost:28010/docs`
2. Click on the `auth/register` route and follow instructions to add a new user
3. Go to **PGAdmin** service at `localhost:5052`, enter credentials (see `/compose/pgadmin/servers.json`)
4. In the left pane, navigate through `.../Databases/Schemas/Tables/user` and `edit/view data`
5. Change the field `is_superuser` to `true` for the new user
6. Commit your changes!


#### Grant service access to a model

1. Login the superuser: click on any lock button on `localhost/docs` and type in your credentials
2. use the route `/inference/pair_user_model`
  - Your user id is an **UUID** like `"c5aec529-57cf-4494-82e9-57c5ab02b265"`.
    - As a superuser, you can pair any model with any user
  - Default `access_policy` is `1`
  - Default `inference_model` is `2`: a dummy temperature predictor using geo coordinates and time

### 3. Test the inference service

#### Send a request
1. Go to `inference/predict-temp/{model_id}` route
2. Enter `model`: `2` and any date / coordinates
3. Your ticket is ready! Copy `task_id` from the response 

#### Use the `task_id` to get your response
1. Go to `inference/task-status/{task_id}` route
2. Paste the `task-id` from above
3. Voilà, the results are in the response json! 
  - Notice: **each distinct input schema must have it's own custom request endpoint** 
  - However, to keep Celery task management modular, no response schema is enforced on the Celery side. The route `task_status` just passes indiscriminately whatever output was retrieved from the worker.


### 4. Add new ML models

#### Adding the model class

1. Each model file should contain a **class with a `predict` method**
2. Imports necessary should be **placed INSIDE the `__init__` method**, not outside the class! This way, heavy library imports only happen in the `celery worker`, won't have to be installed in any other container!
3. Move the file containing the model in `project/inference/ml_models`


#### Registering the model
This part allows to register a model in the database, map it with users and access policies, etc.
1. In `inference/model_registry`, copy-paste a new `@register_model` function 
2. Fill some info about the model in the decorator  (classification / regression, version, service access policy etc)
3. Return an instance of your model in the function
- Note: Packaged models (ex `VaderSentimentAnalyzer`) dont require a separate file, instantiate them directly in a @register_model function

#### Adding a model input schema

#### Creating a request endpoint


## Dev Tools

### Tests

### Linting and pre-commit


## Monitoring


## What next?

### Create a simple HTMX Frontend
- How to handle login data storage when logging in via web page?
  - Cookies
- How handle security issues with communication backend / frontend?
  - CORS Middleware against CSRF attacks
- How to handle async request / response end points when rendering a web page? 



```sh

```