# file: app/routers/ml_service_v1.py

"""
Module: ml_service_v1.py

This module provides API endpoints for version 2 of the ML service. It uses the FastAPI framework
to define routes and handle HTTP requests. The module includes the following main components:

- Dependencies:
  - `get_db`: Dependency function to get a database session.
  - `get_current_user`: Dependency function to authenticate and retrieve the current user.
  - `get_ml_model_v1`: Dependency function to lazy-load the ML model.

- Routes:
  - `/healthcheck`: Endpoint to check the health status of the ML service.
  - `/predict`: Endpoint to make predictions using the loaded ML model.

The module also integrates with the `PlaceholderMLModelV1` class from the `ml_models.v1` module to
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
from ..ml_models.v1 import PlaceholderMLModelV1
from .auth import get_current_user

router = APIRouter(prefix="/mlservice/v1", tags=["mlservice/v1"])

placeholder_ml_model_v1 = PlaceholderMLModelV1()


############### DEPENDENCIES ###############
async def get_ml_model_v1(
    model: PlaceholderMLModelV1 = Depends(),
) -> PlaceholderMLModelV1:
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
ml_model_v1_dependency = Annotated[
    PlaceholderMLModelV1, Depends(get_ml_model_v1)
]  # pylint: disable=invalid-name


############### ROUTES ###############
@router.get("/healthcheck", status_code=status.HTTP_200_OK)
async def check_service_v1(
    user: user_dependency, db: db_dependency
) -> dict:  # pylint: disable=unused-argument
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
    if user is None or not user.get("has_access_v1"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"status": "healthy"}


@router.post("/predict", status_code=status.HTTP_200_OK)
async def make_prediction_v1(
    prediction_input: PredictionInput,
    user: user_dependency,
    db: db_dependency,
    model: ml_model_v1_dependency,
) -> PredictionOutput:
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
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is None"
        )

    if not user.get("has_access_v1"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not have access to the service",
        )

    request_time = datetime.now()
    prediction_output = await model.predict(prediction_input)
    completion_time = datetime.now()
    duration = (completion_time - request_time).total_seconds()

    service_call_data = ServiceCallCreate(
        service_version="v1",
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
