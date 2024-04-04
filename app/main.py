# file: app/main.py
"""
Module: main.py

This module serves as the entry point for the FastAPI application. It sets up the
API routes, database connection, and handles the application's lifespan events.

The module includes the following main components:

- ML Models:
  - `placeholder_ml_model_v1`: An instance of the PlaceholderMLModelV1 class.
  - `placeholder_ml_model_v2`: An instance of the PlaceholderMLModelV2 class.

- API:
  - The FastAPI application instance is created.
  - API routes are included using the `include_router` method for different modules:
    - `auth`: Authentication-related routes.
    - `admin`: Admin-related routes.
    - `users`: User-related routes.
    - `ml_service_v1`: Machine learning service version 1 routes.
    - `ml_service_v2`: ____________
- Database:
  - The database tables are created based on the defined models using `Base.metadata.create_all`.

- Lifespan Events:
  - `startup_event`: Called when the application starts up. It creates a superuser if the
    environment variable "CREATE_SUPERUSER" is set to a truthy value. It also loads the
    machine learning models.
  - `shutdown_event`: Called when the application shuts down. It removes the superuser if
    the environment variable "CREATE_SUPERUSER" is set to a truthy value.

- Routes:
  - `/healthcheck`: A simple healthcheck endpoint to check the status of the application.

The module loads environment variables from the `.environment` folder using the `load_dotenv`
function from the `python-dotenv` library.

Note: Make sure to have the necessary environment variables set up in the `.environment`
folder for the application to function properly.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI

from .ml_models.v1 import PlaceholderMLModelV1
from .ml_models.v2 import PlaceholderMLModelV2
from .models import Base
from .database import engine, SessionLocal
from .routers import auth, admin, users, ml_service_v1, ml_service_v2 
from .devtools import create_superuser, remove_superuser
load_dotenv(override=True)  # loads environment variables from the .environment folder

############## ML MODELS ###############
placeholder_ml_model_v1 = PlaceholderMLModelV1()
placeholder_ml_model_v2 = PlaceholderMLModelV2()

############### API ###############
app = FastAPI()
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(ml_service_v1.router)
app.include_router(ml_service_v2.router)


############### DATABASE ###############
Base.metadata.create_all(bind=engine)


############### LIFESPAN ###############
@app.on_event("startup")
async def startup_event() -> None:
    """
    Startup event handler for the FastAPI application.

    This function is called when the application starts up. It performs the following tasks:
    1. If the environment variable "CREATE_SUPERUSER" is set to a truthy value, it creates a superuser
       in the database using the `create_superuser` function.
    2. Loads the machine learning models for version 1 and version 2 using the `load_model` method
       of the respective model instances.

    Returns:
        None

    Raises:
        None
    """
    if os.getenv("CREATE_SUPERUSER", "False").lower() in ["true", "1", "yes"]:
        db = SessionLocal()
        create_superuser(db)
        db.close()

    await ml_service_v1.placeholder_ml_model_v1.load_model()
    await ml_service_v2.placeholder_ml_model_v2.load_model()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Shutdown event handler for the FastAPI application.

    This function is called when the application shuts down. It performs the following task:
    1. If the environment variable "CREATE_SUPERUSER" is set to a truthy value, it removes the superuser
       from the database using the `remove_superuser` function.

    Returns:
        None

    Raises:
        None
    """
    if os.getenv("CREATE_SUPERUSER", "False").lower() in ["true", "1", "yes"]:
        db = SessionLocal()
        remove_superuser(db)
        db.close()


############### ROUTES ###############
@app.get("/healthcheck")
def get_healthcheck() -> None:
    """
    Healthcheck endpoint to check the status of the application.

    This function is used to check the health status of the FastAPI application. It returns a JSON
    response indicating that the application is healthy.

    Returns:
        dict: A dictionary containing the health status of the application.
            - "status" (str): The status of the application, which is always "healthy".

    Raises:
        None
    """
    return {"status": "healthy"}
