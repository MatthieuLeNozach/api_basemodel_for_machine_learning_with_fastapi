import logging
from fastapi import FastAPI, Depends
from sqladmin import Admin
from project.config import settings
from project.database import engine
from project.fu_core import api_router
from project.database import engine, get_async_session
from project.inference.seeders import seed_inference_data

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    from project.logging import configure_logging
    configure_logging()
    

    
    app = FastAPI()

    from project.celery_utils import create_celery
    app.celery_app = create_celery()

    @app.on_event("startup")
    async def on_startup():
        async for session in get_async_session():
            logger.info("Seeding the database with initial data...")
            await seed_inference_data(session)

    @app.get("/")
    async def root():
        return {"message": "hello world"}

    app.include_router(api_router, prefix=settings.API_V1_STR)

    logger.info("Application created with routes: %s", app.routes)
    return app

