from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


########## SERVICE ACCESS SCHEMAS ##########

class UserAccessCreate(BaseModel):
    user_id: UUID
    model_id: int
    access_policy_id: int

class UserAccessResponse(BaseModel):
    user_id: UUID
    model_id: int
    access_policy_id: int
    api_calls: int
    access_granted: bool
    last_accessed: datetime

    class Config:
        from_attributes = True
        
        
        
########## ML SCHEMAS ##########


class TemperatureModelInput(BaseModel):
    latitude: int
    longitude: int
    month: int
    hour: int

class TemperatureModelOutput(BaseModel):
    temperature: float