# file: app/routers/ml_service_v2.py

from datetime import datetime
from typing import Annotated
from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, ServiceCall
from ..schemas import PredictionInput, PredictionOutput, ServiceCallCreate
from ..ml_models.v2 import PlaceholderMLModelV2
from .auth import get_current_user

router = APIRouter(prefix='/mlservice/v2', tags=['mlservice/v2'])

placeholder_ml_model_v2 = PlaceholderMLModelV2()

# Dependency function to get the ML model instance
async def get_ml_model_v2(model: PlaceholderMLModelV2 = Depends()) -> PlaceholderMLModelV2:
    if not model.loaded:
        await model.load_model()
    return model

############### DEPENDENCIES ###############
async def get_ml_model_v2(model: PlaceholderMLModelV2 = Depends()) -> PlaceholderMLModelV2:
    """Dependency to lazy-load a ML model"""
    if not model.loaded:
        await model.load_model()
    return model




db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
ml_model_v2_dependency = Annotated[PlaceholderMLModelV2, Depends(get_ml_model_v2)]




############### ROUTES ###############
@router.get('/healthcheck', status_code=status.HTTP_200_OK)
async def check_service_v2(user: user_dependency, db: db_dependency) -> dict:
    if user is None or not user.get('has_access_v2'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {'status': 'healthy'}

# Define your routes here
@router.post('/predict', status_code=status.HTTP_200_OK)
async def make_prediction_v2(prediction_input: PredictionInput, user: user_dependency, db: db_dependency, model: ml_model_v2_dependency):
    if user is None or not user.get('has_access_v2'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    request_time = datetime.now()
    prediction_output = await model.predict(prediction_input)
    completion_time = datetime.now()
    duration = (completion_time - request_time).total_seconds()
    
    service_call_data = ServiceCallCreate(
        service_version='v2',
        success=True,
        owner_id=user['id'],
        request_time=request_time,
        completion_time=completion_time,
        duration=duration
    )
    service_call = ServiceCall(**service_call_data.dict())
    db.add(service_call)
    db.commit()
    db.refresh(service_call)
    
    return prediction_output