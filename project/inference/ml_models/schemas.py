from pydantic import BaseModel

class TemperatureModelInput(BaseModel):
    latitude: int
    longitude: int
    month: int
    hour: int

class TemperatureModelOutput(BaseModel):
    temperature: float