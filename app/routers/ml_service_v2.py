# file: app/routers/ml_service_v2.py
"""
Module: ml_service_v2.py

This module provides API endpoints for version 2 of the ML service. It uses the FastAPI framework
to define routes and handle HTTP requests. The module includes the following main components:

- Dependencies:
  - `get_db`: Dependency function to get a database session.
  - `get_current_user`: Dependency function to authenticate and retrieve the current user.
  - `get_ml_model_v2`: Dependency function to lazy-load the ML model.

- Routes:
  - `/healthcheck`: Endpoint to check the health status of the ML service.
  - `/predict`: Endpoint to make predictions using the loaded ML model.

The module also integrates with the `PlaceholderMLModelV2` class from the `ml_models.v2` module to
load and use the ML model for making predictions. It uses the `ServiceCall` and `PredictionInput`
models and schemas for data validation and storage.

Authentication and authorization are handled using the `get_current_user` dependency, which verifies
the user's access rights to the ML service endpoints.

The module follows a modular structure and uses dependency injection to promote code reusability and
maintainability.
"""

from datetime import datetime
from typing import Annotated
from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, ServiceCall
from ..schemas import PredictionInput, PredictionOutput, ServiceCallCreate
from ..ml_models.v2 import PlaceholderMLModelV2
from .auth import get_current_user

router = APIRouter(prefix="/mlservice/v2", tags=["mlservice/v2"])

placeholder_ml_model_v2 = PlaceholderMLModelV2()


############### DEPENDENCIES ###############
async def get_ml_model_v2(
    model: PlaceholderMLModelV2 = Depends(),
) -> PlaceholderMLModelV2:
    """
    Dependency function to lazy-load the ML model.

    Args:
        model: The PlaceholderMLModelV2 instance to be loaded.

    Returns:
        The loaded PlaceholderMLModelV2 instance.
    """
    if not model.loaded:
        await model.load_model()
    return model


db_dependency = Annotated[Session, Depends(get_db)]  # pylint: disable=invalid-name
user_dependency = Annotated[
    dict, Depends(get_current_user)
]  # pylint: disable=invalid-name
ml_model_v2_dependency = Annotated[
    PlaceholderMLModelV2, Depends(get_ml_model_v2)
]  # pylint: disable=invalid-name


############### ROUTES ###############
@router.get("/healthcheck", status_code=status.HTTP_200_OK)
async def check_service_v2(user: user_dependency, db: db_dependency) -> dict:
    """
    Endpoint to check the health status of the ML service.

    Args:
        user: The authenticated user dependency.
        db: The database session dependency.

    Returns:
        A dictionary containing the health status of the service.

    Raises:
        HTTPException: If the user is not authenticated or lacks access rights.
    """
    if user is None or not user.get("has_access_v2"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"status": "healthy"}


# Define your routes here
@router.post("/predict", status_code=status.HTTP_200_OK)
async def make_prediction_v2(
    prediction_input: PredictionInput,
    user: user_dependency,
    db: db_dependency,
    model: ml_model_v2_dependency,
) -> dict:
    """
    Endpoint to make predictions using the loaded ML model and log the service call.

    Args:
        prediction_input: The input data for the prediction.
        user: The authenticated user dependency.
        db: The database session dependency.
        model: The loaded ML model dependency.

    Returns:
        The prediction output from the ML model.

    Raises:
        HTTPException: If the user is not authenticated or lacks access rights.
    """
    if user is None or not user.get("has_access_v2"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    request_time = datetime.now()
    prediction_output = await model.predict(prediction_input)
    completion_time = datetime.now()
    duration = (completion_time - request_time).total_seconds()

    service_call_data = ServiceCallCreate(
        service_version="v2",
        success=True,
        owner_id=user["id"],
        request_time=request_time,
        completion_time=completion_time,
        duration=duration,
    )
    service_call = ServiceCall(**service_call_data.dict())
    db.add(service_call)
    db.commit()
    db.refresh(service_call)

    return prediction_output
