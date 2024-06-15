from fastapi import APIRouter

inference_router = APIRouter(
    prefix="/inference"
)
from project.inference import tasks, views
from project.inference.views import *